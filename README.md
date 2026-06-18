# 🏦 Adaptive Banking Queue Core Engine (ABQE)
### Dynamic Interrupt-Driven Hybrid Priority & Distributed Load-Balancing Scheduler

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![MySQL](https://img.shields.io/badge/MySQL-00000F?style=for-the-badge&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

---

## 📖 The Origin Story: My Real-World Observation at Canara Bank

This project was born out of pure, genuine frustration while I was personally trapped inside a heavily crowded **Canara Bank** branch for over an hour. 

I had walked into the branch just to make a simple, routine **₹3,000 cash deposit**—a transaction that realistically takes less than 2 minutes at the counter window. The branch was physically premium, equipped with proper waiting sofas, chairs, and centralized air conditioning. I walked up to the electronic touchscreen kiosk machine, tapped the screen, generated my sequential token, and took a seat. 

But as I sat there for **more than an hour**, watching my life tick away while tracking the token display board, I witnessed the entire backend system operationally break down due to its rigid, primitive routing logic:

1. **The Counter-Blocking & High-Volume Avalanche:** While I was waiting for my quick 2-minute turn, an elderly senior citizen walked in. He had a massive transaction pipeline—**₹4 Lakhs in cash** that required manual counting, security verification, and extensive bundle auditing. His token number was generated **way after mine**. However, because of a flawed implementation of dynamic priority or a single counter window lockup, his high-volume task completely stalled the thread. 
2. **The 5-Min vs. 30-Min Penalty:** My 5-minute processing window was instantly delayed by an extra 30+ minutes because the system forced a tiny ₹3,000 deposit thread to sleep while a massive ₹4 Lakh financial processing thread held a monopoly over the teller resource. This is a text-book definition of **Head-of-Line (HOL) Blocking**, **Convoy Effects**, and severe **Thread Starvation**.
3. **The Invisible Emergency Dilemma:** During this exact chaos, another man rushed into the branch, visibly panicked, needing immediate manager clearance for a medical draft to release funds for a family member in a critical hospital emergency nearby. The electronic kiosk blindly printed a standard routine token for him, stacking him behind 40 relaxed customers sitting on the couches. Watching a critical life-and-death emergency get treated with the exact same system weight as a routine account update felt fundamentally broken.

As an engineer sitting on that bank chair, I couldn't unsee these architectural flaws. I realized that physical banking floors suffer from the exact same resource allocation, priority inversion, and deadlock problems that operating systems face when scheduling concurrent processes on a CPU. I walked back home, mapped core **OS Kernel Scheduling Concepts** to banking operations, and engineered the **Adaptive Banking Queue Core Engine (ABQE)**.

---

## 🛑 Problem Statement

Conventional banking routers rely on naive, static FIFO scheduling arrays. These legacy architectures fail catastrophically because they treat queue management as a fixed stream rather than a fluid, unpredictable human ecosystem. They completely lack the mathematical infrastructure to handle:
1. **Dynamic Priority Interruption:** Injecting unexpected high-urgency events cleanly without breaking or crashing the existing sequence.
2. **Resource Lockups / Counter Blocking:** Gracefully shifting resources when a transaction gets paused, delayed, or timed out at a teller window.
3. **Operational Load Imbalance:** Efficiently spreading workload across multiple physical branch counters during sudden traffic spikes.

---

## 📈 Macro-Scale Industry Analysis: How Today's Banking Tech Fails

After returning home, I analyzed how modern fintech and enterprise banking industries tackle queue logistics. Currently, the commercial banking industry relies on two primary methods:
* **Static Token Multi-Channelling:** Dividing queues by transaction types (e.g., separate lines for 'Loans' vs. 'Deposits'). This fails when a single channel gets blocked, leaving other counters completely underutilized.
* **Linear FIFO Overflows:** Blindly routing the next token to the next free teller, which completely fails to handle state alterations like a transaction getting `PAUSED` mid-way or handling high-urgency preemptive bypasses cleanly.

### 🧠 Why My Code is Unique & Outsmarts Conventional Banking Systems

While industry tech giants design queue systems as simple database logging software, I designed **ABQE** by treating bank floor mechanics as a **low-level Operating System Kernel**. Here is what makes my architecture completely unique and superior to existing commercial setups:

* **Shortest-Job-First (SJF) Mitigation for Small Tokens:** To ensure that a guy depositing ₹3,000 never gets stuck behind a ₹4 Lakh transaction thread again, my engine uses transaction amount brackets to accurately predict processing times (`allocated_time_mins`). When the counter enters an optimization sweep, shorter tasks are dispatched first to clear bheed instantly.
* **Stateful Preemption vs. Static Separation:** Industry systems force users into fixed lines. My engine dynamically intercepts the existing execution stack. When a medical emergency token is created, it triggers a system software interrupt, dropping all non-urgent priorities to index 0.
* **Mathematical Demographic Aging Core:** To prevent healthy or large-amount customers from facing infinite starvation while vulnerable classes or short transactions are prioritized, my engine utilizes an integrated **Aging Algorithm**. If a regular token's waiting metric passes 35 minutes, its priority dynamically decays its placement constraint, moving it forward smoothly to maintain system fairness.
* **Dynamic Multi-Counter Balancing:** Instead of simple static routing, the engine runs a real-time distributed routing calculation. It automatically tracks counter load shifts and deploys round-robin allocations across multiple active teller windows seamlessly.

---

## 🛠️ System Architecture & Mathematical Ranking Matrix

The scheduler continuously computes a real-time `computed_priority_rank` using a custom hybrid execution pipeline:

1. **Absolute Emergency State:** Triggered when `is_medical_emergency = 1`.
   $$Priority\_Score = 0 - (Urgency\_Score \times 10) + Effective\_Service\_Time$$
2. **Timeout Preemption Mode:** Activated when an active transaction is marked as `PAUSED`.
   $$Priority\_Score = 100 - Demographic\_Boost + (Effective\_Service\_Time \times 0.5)$$
3. **Strict Standard State:** Falls back to timestamp-based epoch serialization.
   $$Priority\_Score = \lfloor Epoch\_Timestamp \rfloor$$

---

## 🚀 Live Simulation & Verified Test Cases (Visual Proofs)

### 🧹 Preparation: Flush System Memory
Before executing any test scenario, clear the database storage layer:
```sql
TRUNCATE TABLE bank_tokens;
🧪 Test Case 1: Standard Serialized FIFO Execution Flow
Scenario: Normal operations; tokens enter chronologically with no special constraints.

SQL Insert Command:

SQL
INSERT INTO bank_tokens (customer_name, transaction_type, amount, is_medical_emergency, is_financial_emergency, special_category, allocated_time_mins, token_status, created_at)
VALUES 
('Rahul Sharma', 'DEPOSIT', 45000, 0, 0, 'NONE', 12, 'WAITING', '2026-06-18 12:45:00'),
('Ramesh Uncle', 'WITHDRAWAL', 250000, 0, 0, 'NONE', 25, 'WAITING', '2026-06-18 12:46:00'),
('Suresh Kumar', 'DEPOSIT', 5000, 0, 0, 'NONE', 5, 'WAITING', '2026-06-18 12:47:00');
Execution Trigger: http://127.0.0.1:8000/api/queue/dynamic-schedule?available_counters=1

Execution Proof:
<img width="737" height="522" alt="image" src="https://github.com/user-attachments/assets/fed633d5-ef2a-4888-8682-c5b4ffce5090" />

🧪 Test Case 2: Emergency Interrupt-Driven Preemption
Scenario: High-risk medical records intercepting an active normal queue thread.

SQL Insert Command:
INSERT INTO bank_tokens (customer_name, transaction_type, amount, is_medical_emergency, is_financial_emergency, medical_urgency_score, special_category, allocated_time_mins, token_status, created_at)
VALUES 
('Patient A (Low Urgency)', 'WITHDRAWAL', 20000, 1, 0, 3, 'NONE', 12, 'WAITING', '2026-06-18 12:50:00'),
('Patient B (Accident Critical)', 'WITHDRAWAL', 80000, 1, 0, 9, 'NONE', 5, 'WAITING', '2026-06-18 12:51:00');
Execution Proof:
<img width="1920" height="1020" alt="image" src="https://github.com/user-attachments/assets/ffe762df-b38f-48f8-9702-9c0647e7e3f1" />
<img width="1037" height="421" alt="image" src="https://github.com/user-attachments/assets/afdc0f08-298c-4ecb-a9f1-5a2f16e6d87d" />

🧪 Test Case 3: Counter-Blocking Timeout (SJF Activation)
Scenario: A counter operator halts a transaction, triggering the fallback aging and Shortest-Job-First (SJF) balancing layer.

SQL Configuration Commands
DELETE FROM bank_tokens WHERE is_medical_emergency = 1;
UPDATE bank_tokens SET token_status = 'PAUSED' WHERE customer_name = 'Ramesh Uncle';
UPDATE bank_tokens SET token_status = 'WAITING' WHERE customer_name = 'Rahul Sharma';
Execution Proof:
<img width="1920" height="1020" alt="image" src="https://github.com/user-attachments/assets/da1b3632-1dc7-4be5-ba94-53c69bcd2e5d" />
<img width="1092" height="282" alt="image" src="https://github.com/user-attachments/assets/8c576620-0b79-4b9d-9008-285f03963536" />


🧪 Test Case 4: Vulnerable Demographic Routing Preemption
Scenario: Senior citizens and pregnant individuals entering the pipeline during system timeouts.

SQL Setup Block:
TRUNCATE TABLE bank_tokens;
INSERT INTO bank_tokens (customer_name, transaction_type, amount, is_medical_emergency, is_financial_emergency, special_category, allocated_time_mins, token_status, created_at)
VALUES 
('Normal Customer 1', 'DEPOSIT', 50000, 0, 0, 'NONE', 12, 'WAITING', '2026-06-18 13:00:00'),
('Ramesh Uncle (System Pauser)', 'WITHDRAWAL', 200000, 0, 0, 'NONE', 25, 'PAUSED', '2026-06-18 13:01:00'),
('Seema Ji (Pregnant)', 'DEPOSIT', 10000, 0, 0, 'PREGNANT', 5, 'WAITING', '2026-06-18 13:02:00'),
('Verma Ji (Senior Citizen)', 'WITHDRAWAL', 15000, 0, 0, 'SENIOR_CITIZEN', 12, 'WAITING', '2026-06-18 13:03:00');
Execution Proof:
<img width="1920" height="1020" alt="image" src="https://github.com/user-attachments/assets/07e28163-97a8-49d8-9ea4-b7cb7b084ba9" />
blob:https://gemini.google.com/7be1687e-94ec-4ba4-8fbf-6ceff06e164d

🧪 Test Case 5: Horizontal Multi-Counter Load Balancing
Scenario: The banking facility deploys multiple operational processing windows to handle heavy traffic loads dynamically.

SQL Setup Block:
TRUNCATE TABLE bank_tokens;
INSERT INTO bank_tokens (customer_name, transaction_type, amount, is_medical_emergency, is_financial_emergency, special_category, allocated_time_mins, token_status, created_at)
VALUES 
('Amit Kumar', 'DEPOSIT', 30000, 0, 0, 'NONE', 12, 'WAITING', '2026-06-18 13:10:00'),
('Sumit Singh', 'WITHDRAWAL', 45000, 0, 0, 'NONE', 12, 'WAITING', '2026-06-18 13:11:00'),
('Vikas Yuvraj', 'DEPOSIT', 8000, 0, 0, 'NONE', 5, 'WAITING', '2026-06-18 13:12:00');

Execution Proof:
<img width="1392" height="232" alt="image" src="https://github.com/user-attachments/assets/3fbe17fb-a2b5-4582-bd06-d11bf05c485d" />
<img width="807" height="307" alt="image" src="https://github.com/user-attachments/assets/ee941c5f-7984-4616-8f9b-88b37248a60b" />






