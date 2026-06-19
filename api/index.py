import os
import datetime

import pymysql
from dotenv import load_dotenv
from fastapi import FastAPI, Query

# Loads variables from a local .env file when running locally.
# On Vercel (or any host that injects env vars directly), this is a no-op.
load_dotenv()

app = FastAPI()

# ── Database connection config ───────────────────────────────────────────
# No credentials live in source anymore — they come from the environment.
# Locally: put them in a .env file (see .env.example).
# On Vercel: set these as Environment Variables in the project settings.
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "bank_management")

if not DB_PASSWORD:
    # Fail loudly at startup instead of silently connecting with no password.
    raise RuntimeError(
        "DB_PASSWORD is not set. Create a .env file locally (see .env.example) "
        "or set DB_PASSWORD as an environment variable in your deployment."
    )


def get_db_connection():
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        print(f"Database Connection Failed: {e}")
        return None


@app.get("/")
def home():
    return {"message": "Adaptive Bank Queue Engine is Live!"}


@app.post("/api/tokens/create")
def create_token(
    customer_name: str,
    transaction_type: str,
    amount: int,
    is_medical_emergency: int,
    is_financial_emergency: int,
    special_category: str,
    medical_urgency_score: int = 0
):
    connection = get_db_connection()
    if not connection:
        return {"error": "Database down! Cannot issue token."}

    if amount <= 10000:
        allocated_time = 5
    elif amount <= 100000:
        allocated_time = 12
    else:
        allocated_time = 25

    try:
        with connection.cursor() as cursor:
            sql_query = """
                INSERT INTO bank_tokens 
                (customer_name, transaction_type, amount, is_medical_emergency, is_financial_emergency, medical_urgency_score, special_category, allocated_time_mins, token_status) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'WAITING')
            """
            cursor.execute(sql_query, (
                customer_name,
                transaction_type.upper(),
                amount,
                is_medical_emergency,
                is_financial_emergency,
                medical_urgency_score,
                special_category.upper(),
                allocated_time
            ))
            connection.commit()
            new_token_id = cursor.lastrowid

        return {
            "status": "Success",
            "token_id": new_token_id,
            "message": f"Token issued successfully for {customer_name}.",
            "allocated_time_mins": allocated_time
        }
    except Exception as e:
        return {"error": f"Failed to generate token: {e}"}
    finally:
        connection.close()


@app.get("/api/queue/dynamic-schedule")
def get_dynamic_scheduled_queue(
    available_counters: int = Query(default=1, alias="available_counters")
):
    """
    ### Adaptive Queue Scheduling Core Engine
    Explicit Query Binding helps track accurate query parameters during simulation.
    """
    connection = get_db_connection()
    if not connection:
        return {"error": "Database connection offline."}

    try:
        # Convert explicitly to prevent runtime query boundary escapes
        counters_count = int(available_counters)

        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as paused_count FROM bank_tokens WHERE token_status = 'PAUSED'")
            is_timeout_active = cursor.fetchone()['paused_count'] > 0

            cursor.execute("SELECT current_counter_id FROM bank_tokens WHERE token_status = 'PROCESSING' AND is_medical_emergency = 1")
            busy_medical_counters = [row['current_counter_id'] for row in cursor.fetchall() if row['current_counter_id'] is not None]

            sql = """
                SELECT token_id, customer_name, transaction_type, amount, 
                       is_medical_emergency, is_financial_emergency, medical_urgency_score, special_category, 
                       allocated_time_mins, remaining_time_mins, token_status, created_at, current_counter_id
                FROM bank_tokens
                WHERE token_status IN ('WAITING', 'PAUSED', 'PROCESSING')
            """
            cursor.execute(sql)
            all_tokens = cursor.fetchall()

        current_time = datetime.datetime.now()
        processed_queue = []

        for token in all_tokens:
            wait_duration = (current_time - token['created_at']).total_seconds() / 60
            effective_time = token['remaining_time_mins'] if token['remaining_time_mins'] is not None else token['allocated_time_mins']

            if token['is_medical_emergency'] == 1 or token['is_financial_emergency'] == 1:
                priority_score = 0 - (token['medical_urgency_score'] * 10) + effective_time
            elif is_timeout_active:
                priority_score = 100
                if wait_duration >= 35:
                    priority_score -= 80
                elif token['special_category'] in ['PREGNANT', 'SENIOR_CITIZEN']:
                    priority_score -= 50
                    priority_score += (effective_time * 0.5)
                else:
                    priority_score += effective_time
            else:
                priority_score = int(token['created_at'].timestamp())

            token['computed_priority_rank'] = priority_score
            token['live_wait_mins'] = round(wait_duration, 1)
            processed_queue.append(token)

        processed_queue.sort(key=lambda x: x['computed_priority_rank'])

        # ----------------------------------------------------
        # MULTI-COUNTER DISTRIBUTED BALANCING ENGINE
        # ----------------------------------------------------
        for index, token in enumerate(processed_queue):
            if counters_count == 1:
                token['current_counter_id'] = 1
                if index == 0 and token['token_status'] == 'WAITING':
                    token['token_status'] = 'PROCESSING'
            else:
                if token['is_medical_emergency'] == 1:
                    assigned_counter = None
                    for c_id in range(1, counters_count + 1):
                        if c_id not in busy_medical_counters:
                            assigned_counter = c_id
                            break
                    if assigned_counter is None:
                        assigned_counter = (index % counters_count) + 1
                    token['current_counter_id'] = assigned_counter
                else:
                    # Dynamic Round-Robin Distribution over Active Windows
                    token['current_counter_id'] = (index % counters_count) + 1

            # Active Processing Preemption Windows Mapping
            if index < counters_count and token['token_status'] == 'WAITING':
                token['token_status'] = 'PROCESSING'

        current_mode = "Multi-Emergency Interruption Mode" if any(t['is_medical_emergency'] == 1 for t in processed_queue) else ("Adaptive Priority Mode (Timeout Active)" if is_timeout_active else "Strict FIFO Mode")

        # ----------------------------------------------------
        # VISUAL TERMINAL BEAUTIFIER 
        # ----------------------------------------------------
        print("\n" + "=" * 95)
        print(f" 🏦 BANK OPERATIONAL MODE: {current_mode.upper()} ")
        print(f" Deployed Counters: {counters_count} | Timeout Preemption: {is_timeout_active}")
        print("=" * 95)
        print(f"{'Token ID':<10}{'Customer Name':<28}{'Status':<14}{'Counter':<10}{'Rank Score':<14}{'Wait Mins':<10}")
        print("-" * 95)
        for t in processed_queue:
            print(f"{t['token_id']:<10}{t['customer_name']:<28}{t['token_status']:<14}{t['current_counter_id']:<10}{round(t['computed_priority_rank'], 1):<14}{t['live_wait_mins']:<10}")
        print("=" * 95 + "\n")

        return {
            "bank_operational_mode": current_mode,
            "timeout_preemption_active": is_timeout_active,
            "live_counters_deployed": counters_count,
            "busy_medical_counters_log": busy_medical_counters,
            "optimized_queue_flow": processed_queue
        }

    except Exception as e:
        return {"error": f"Mission-Critical Scheduling Failed: {e}"}
    finally:
        connection.close()
