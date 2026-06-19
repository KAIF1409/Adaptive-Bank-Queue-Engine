# Adaptive Bank Queue Engine (ABQE)

A FastAPI backend that replaces simple FIFO token queues at a bank counter with a priority-aware scheduler — one that can interrupt for emergencies, age out long-waiting customers, run shortest-job-first when things get backed up, and balance load across multiple counters.

---

## Why I built this

I was at a Canara Bank branch waiting to make a ₹3,000 cash deposit — a two-minute job — and ended up sitting there for over an hour. While I waited, I watched the token system completely fail at handling anything outside the happy path:

- An elderly customer ahead of me had a ₹4 lakh transaction that needed manual counting and verification. It tied up the counter for a long time, and everyone behind him — including my quick deposit — just sat there waiting, even though our transactions would've taken a fraction of the time.
- Someone walked in needing an urgent medical-related withdrawal and got handed a regular token, stacked behind 40 people on the same priority level as a routine deposit.

Sitting there, it was hard not to notice that this is basically the same problem operating systems deal with when scheduling processes on a CPU — head-of-line blocking, convoy effects, starvation, the works. So I went home and built a scheduler for it, using the same ideas (priority scheduling, aging, preemption) that OS schedulers use, just applied to a bank queue instead of a process queue.

## What it actually does

The core of the project is one endpoint: `GET /api/queue/dynamic-schedule`. Given the current set of tokens in the database, it recomputes a priority rank for every token and returns the queue in the order people should actually be served, instead of strict arrival order. It also assigns tokens across however many counters are marked available.

Three scheduling modes, depending on what's happening in the queue:

1. **Strict FIFO** — the default. No emergencies, no timeouts. Tokens are ranked by arrival timestamp, same as a normal token system.
2. **Emergency interrupt mode** — triggers the moment a token is flagged `is_medical_emergency` or `is_financial_emergency`. These get pulled to the front, ranked further by an urgency score, and (with multiple counters active) routed to whichever counter is free fastest.
3. **Adaptive/timeout mode** — triggers when at least one token is `PAUSED` (a counter got stuck or stalled). Once this kicks in, the engine starts behaving differently: shorter transactions get pushed ahead of longer ones (a rough shortest-job-first pass, since transaction amount roughly predicts how long it'll take), and tokens that have been waiting 35+ minutes — or belong to a senior citizen / pregnant customer — get their priority boosted so they don't get starved out indefinitely.

When more than one counter is available, the engine round-robins normal tokens across them and tries to keep emergency tokens off counters that are already handling another emergency.

## Tech stack

- **FastAPI** — the API layer
- **PyMySQL** — talks to a MySQL database (`bank_tokens` table tracks token state: `WAITING`, `PROCESSING`, `PAUSED`, `COMPLETED`)
- **Vercel** — deployment (single `api/index.py` entrypoint, see `vercel.json`)

It's a single-file backend right now — no frontend, no auth layer, just the scheduling API and the database. That's intentional for this stage; the point was to get the scheduling logic right first.

## How I built it

This was a solo project, and I used AI (Gemini) as a coding assistant rather than a co-architect. To be specific about the split:

- **Mine:** the actual problem framing — mapping bank-floor chaos to OS scheduling concepts — the priority formulas, deciding when the engine should switch between FIFO / emergency / aging modes, the amount-based time brackets, and the test scenarios used to verify it actually behaves correctly.
- **AI-assisted:** turning those rules into FastAPI route code, writing the SQL schema/queries, and drafting documentation.

I think it's worth being upfront about that rather than pretending every line was typed from scratch — the scheduling logic and the reasoning behind it are mine; the boilerplate around it had help.

## The priority math

For each token, depending on which mode is active:

**Emergency mode:**
```
priority_score = 0 - (medical_urgency_score × 10) + effective_time_remaining
```

**Timeout / aging mode:**
```
priority_score = 100 - demographic_boost + (effective_time_remaining × 0.5)
```
(tokens waiting 35+ minutes get an extra boost pushing them toward the front)

**Standard mode:**
```
priority_score = token_creation_timestamp
```

Lower score = served sooner. The queue is just sorted by this value before counters are assigned.

## API endpoints

| Endpoint | Method | What it does |
|---|---|---|
| `/` | GET | Health check |
| `/api/tokens/create` | POST | Issues a new token — takes customer info, transaction type/amount, emergency flags, special category, and auto-assigns a time estimate based on transaction size |
| `/api/queue/dynamic-schedule?available_counters=N` | GET | Recomputes and returns the live prioritized queue across N counters |

## Test scenarios I ran

I tested this against five scenarios to make sure each mode actually triggers and behaves the way it's supposed to — standard FIFO, emergency preemption, counter-timeout triggering the aging/SJF fallback, vulnerable-demographic routing, and multi-counter load balancing. Each one was run against a fresh database state with specific inserted tokens and verified against the actual API output.

<details>
<summary><b>Test 1 — Standard FIFO</b></summary>

Three normal tokens inserted in order, one counter available. Expected: served strictly in arrival order.

<img width="737" height="522" alt="Test Case 1" src="https://github.com/user-attachments/assets/4fd8a644-3ade-429e-9662-6bfb8670b6b6" />
</details>

<details>
<summary><b>Test 2 — Emergency preemption</b></summary>

Two medical-emergency tokens with different urgency scores. Expected: higher urgency served first, both ranked ahead of any normal token.

<img width="1037" height="421" alt="Test Case 2a" src="https://github.com/user-attachments/assets/dc51a243-c65b-4eab-83d8-f8bfab14b4ce" />
<img width="1037" height="421" alt="Test Case 2b" src="https://github.com/user-attachments/assets/837ee1b7-34d8-4475-8a4e-b769873be03a" />
</details>

<details>
<summary><b>Test 3 — Counter timeout triggers aging/SJF</b></summary>

A large transaction is marked `PAUSED` mid-processing. Expected: the engine switches out of FIFO mode and starts favoring shorter jobs.

<img width="1092" height="282" alt="Test Case 3a" src="https://github.com/user-attachments/assets/3c2a70be-b77e-4947-9672-8d170aa00ea1" />
<img width="1092" height="282" alt="Test Case 3b" src="https://github.com/user-attachments/assets/643b4e09-4d6f-429d-8daa-bb5d7ebeec4b" />
</details>

<details>
<summary><b>Test 4 — Vulnerable demographic routing</b></summary>

A senior citizen and a pregnant customer enter the queue while it's in timeout/aging mode. Expected: both get priority boosts ahead of unflagged customers.

<img width="1920" height="1020" alt="Test Case 4a" src="https://github.com/user-attachments/assets/5b910b92-05f7-45d4-8a09-46b6292013ba" />
<img width="1017" height="287" alt="Test Case 4b" src="https://github.com/user-attachments/assets/261dc156-e5c3-477f-b4d1-003766f1165c" />
</details>

<details>
<summary><b>Test 5 — Multi-counter load balancing</b></summary>

Three normal tokens, multiple counters available. Expected: round-robin assignment across counters instead of all queuing at one.

<img width="1392" height="232" alt="Test Case 5a" src="https://github.com/user-attachments/assets/3129a794-43f8-4c63-9515-260e9a7d7355" />
<img width="807" height="307" alt="Test Case 5b" src="https://github.com/user-attachments/assets/b9eaa595-60a1-4ac7-b8fd-8ecb795c921f" />
</details>

## Running it locally

```bash
pip install -r requirements.txt
```
Set up a MySQL database named `bank_management` with a `bank_tokens` table (columns: `token_id`, `customer_name`, `transaction_type`, `amount`, `is_medical_emergency`, `is_financial_emergency`, `medical_urgency_score`, `special_category`, `allocated_time_mins`, `remaining_time_mins`, `token_status`, `created_at`, `current_counter_id`).

```bash
uvicorn api.index:app --reload
```
Then hit `http://127.0.0.1:8000/` to confirm it's up, and `http://127.0.0.1:8000/docs` for the interactive Swagger UI.

## What I'd improve next

- Move the DB credentials out of the source file and into environment variables — right now they're hardcoded, which is fine for a local prototype but not something I'd want in a repo I'm pointing recruiters to.
- The "shortest job first" estimate is just a flat bracket based on transaction amount right now (small/medium/large → fixed minutes). A real version would learn this from actual historical service times.
- No auth on the endpoints yet — anyone can create tokens or trigger a reschedule.
- This is backend-only — a small frontend showing the live queue would make the demo a lot easier to follow.
