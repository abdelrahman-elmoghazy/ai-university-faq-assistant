"""
============================================================
  Comprehensive API Test Script
  Tests: Auth Service + FAQ Service + Security + DB Schema
============================================================
Run:  python test_api.py
============================================================
"""
import requests
import urllib3
import json
import time
import sys
import os
import subprocess
import random
import string

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Suppress SSL warnings for self-signed certificate
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://localhost"
DELAY = 2.5  # seconds between requests to avoid rate limiting

# Generate unique user suffix to avoid "already exists" errors on re-runs
SUFFIX = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))

# Counters
passed = 0
failed = 0
total = 0

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def test(name, condition, status_code=None, response=None):
    global passed, failed, total
    total += 1
    status = "[PASS]" if condition else "[FAIL]"
    if condition:
        passed += 1
    else:
        failed += 1
    print(f"  {status} | {name}")
    if status_code is not None:
        print(f"         Status Code: {status_code}")
    if response is not None and not condition:
        text = response.text[:300] if hasattr(response, 'text') else str(response)[:300]
        print(f"         Response: {text}")

def wait():
    """Wait to avoid NGINX rate limiting"""
    time.sleep(DELAY)

def run_tests():
    global passed, failed, total

    user_a_name = f"testusera_{SUFFIX}"
    user_a_email = f"usera_{SUFFIX}@test.com"
    user_b_name = f"testuserb_{SUFFIX}"
    user_b_email = f"userb_{SUFFIX}@test.com"
    password = "Password123!"

    print(f"\n  Using test users: {user_a_name}, {user_b_name}")

    # ========================================================
    # PART 1: AUTHENTICATION & AUTHORIZATION
    # ========================================================
    print_header("PART 1: AUTH SERVICE - Registration & Login")

    # --- 1.1 Register User A ---
    print("\n--- 1.1 Register User A ---")
    res = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"username": user_a_name, "email": user_a_email, "password": password, "full_name": "User A"},
        verify=False
    )
    test("Register User A -> 201 Created", res.status_code == 201, res.status_code, res)
    wait()

    # --- 1.2 Register User B ---
    print("\n--- 1.2 Register User B ---")
    res = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"username": user_b_name, "email": user_b_email, "password": password, "full_name": "User B"},
        verify=False
    )
    test("Register User B -> 201 Created", res.status_code == 201, res.status_code, res)
    wait()

    # --- 1.3 Duplicate Registration ---
    print("\n--- 1.3 Duplicate Registration (should fail) ---")
    res = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"username": user_a_name, "email": user_a_email, "password": password, "full_name": "User A"},
        verify=False
    )
    test("Duplicate registration blocked -> 400", res.status_code == 400, res.status_code, res)
    wait()

    # --- 1.4 Login User A ---
    print("\n--- 1.4 Login User A ---")
    res = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": user_a_email, "password": password},
        verify=False
    )
    test("Login User A -> 200 OK", res.status_code == 200, res.status_code, res)
    token_a = res.json().get('access_token') if res.status_code == 200 else None
    test("Login returns access_token", token_a is not None)
    wait()

    # --- 1.5 Login User B ---
    print("\n--- 1.5 Login User B ---")
    res = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": user_b_email, "password": password},
        verify=False
    )
    test("Login User B -> 200 OK", res.status_code == 200, res.status_code, res)
    token_b = res.json().get('access_token') if res.status_code == 200 else None
    wait()

    # ========================================================
    # PART 2: AUTH SECURITY TESTS
    # ========================================================
    print_header("PART 2: AUTH SECURITY - Invalid Login / Token / Expired / Unauthorized")

    # --- 2.1 Invalid Login (wrong password) ---
    print("\n--- 2.1 Invalid Login (wrong password) ---")
    res = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": user_a_email, "password": "WrongPassword999!"},
        verify=False
    )
    test("Wrong password -> 401 Unauthorized", res.status_code == 401, res.status_code, res)
    test("Returns safe error message (no stack trace)", "error" in res.json() and "traceback" not in res.text.lower())
    wait()

    # --- 2.2 Invalid Token ---
    print("\n--- 2.2 Invalid Token ---")
    res = requests.get(
        f"{BASE_URL}/api/auth/me",
        headers={"Authorization": "Bearer this.is.a.fake.token"},
        verify=False
    )
    test("Invalid token -> 401 Unauthorized", res.status_code == 401, res.status_code, res)
    wait()

    # --- 2.3 Missing Token ---
    print("\n--- 2.3 Missing Token (no Authorization header) ---")
    res = requests.get(
        f"{BASE_URL}/api/auth/me",
        verify=False
    )
    test("No token -> 401 Unauthorized", res.status_code == 401, res.status_code, res)
    wait()

    # --- 2.4 Expired Token ---
    print("\n--- 2.4 Expired Token ---")
    expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjB9.invalid"
    res = requests.get(
        f"{BASE_URL}/api/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
        verify=False
    )
    test("Expired/invalid token -> 401 Unauthorized", res.status_code == 401, res.status_code, res)
    wait()

    # --- 2.5 Regular user tries admin endpoint ---
    print("\n--- 2.5 Unauthorized Access - User tries admin endpoint ---")
    if token_a:
        res = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {token_a}"},
            verify=False
        )
        test("Regular user accessing /api/admin/users -> 403 Forbidden", res.status_code == 403, res.status_code, res)
    wait()

    # --- 2.6 Protected route with valid token ---
    print("\n--- 2.6 Valid token -> /api/auth/me works ---")
    if token_a:
        res = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token_a}"},
            verify=False
        )
        test("Valid token -> 200 OK on /api/auth/me", res.status_code == 200, res.status_code, res)
        if res.status_code == 200:
            user_data = res.json().get('user', {})
            test("Response contains user email", user_data.get('email') == user_a_email)
    wait()

    if not token_a:
        print("\n  WARNING: Skipping FAQ tests -- could not get Token A")
        return

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"} if token_b else {}

    # ========================================================
    # PART 3: FAQ SERVICE - Business Logic & Validation
    # ========================================================
    print_header("PART 3: FAQ SERVICE - Questions API & Input Validation")

    # --- 3.1 Ask a Valid Question ---
    print("\n--- 3.1 Ask a Valid Question (User A) ---")
    res = requests.post(
        f"{BASE_URL}/api/faq/ask",
        json={"question_text": "What are the requirements for a master degree?"},
        headers=headers_a,
        verify=False
    )
    test("Ask question -> 201 Created", res.status_code == 201, res.status_code, res)
    question_id = None
    if res.status_code == 201:
        body = res.json()
        question_id = body.get('question', {}).get('id')
        test("Response contains question data", body.get('question') is not None)
        test("Response contains answer data", body.get('answer') is not None)
        test("Answer text is present", body.get('answer', {}).get('answer_text') is not None)
        print(f"         Question ID: {question_id}")
        print(f"         Answer: {body.get('answer', {}).get('answer_text', '')[:100]}...")
    wait()

    # --- 3.2 Ask a second question (for history/conversations) ---
    print("\n--- 3.2 Ask another Question (User A) ---")
    res = requests.post(
        f"{BASE_URL}/api/faq/ask",
        json={"question_text": "How do I apply for a scholarship?", "conversation_id": "conv-001"},
        headers=headers_a,
        verify=False
    )
    test("Second question -> 201 Created", res.status_code == 201, res.status_code, res)
    wait()

    # --- 3.3 Empty Question Validation ---
    print("\n--- 3.3 Input Validation - Empty question ---")
    res = requests.post(
        f"{BASE_URL}/api/faq/ask",
        json={"question_text": "   "},
        headers=headers_a,
        verify=False
    )
    test("Empty question -> 400 Bad Request", res.status_code == 400, res.status_code, res)
    if res.status_code == 400:
        test("Safe error message returned", "empty" in res.text.lower())
    wait()

    # --- 3.4 Missing question_text field ---
    print("\n--- 3.4 Input Validation - Missing question_text ---")
    res = requests.post(
        f"{BASE_URL}/api/faq/ask",
        json={"wrong_field": "hello"},
        headers=headers_a,
        verify=False
    )
    test("Missing field -> 400 Bad Request", res.status_code == 400, res.status_code, res)
    wait()

    # --- 3.5 Question Too Long (>1000 chars) ---
    print("\n--- 3.5 Input Validation - Question too long ---")
    long_question = "A" * 1001
    res = requests.post(
        f"{BASE_URL}/api/faq/ask",
        json={"question_text": long_question},
        headers=headers_a,
        verify=False
    )
    test("Too-long question -> 400 Bad Request", res.status_code == 400, res.status_code, res)
    wait()

    # --- 3.6 Non-string question_text ---
    print("\n--- 3.6 Input Validation - Non-string question ---")
    res = requests.post(
        f"{BASE_URL}/api/faq/ask",
        json={"question_text": 12345},
        headers=headers_a,
        verify=False
    )
    test("Non-string question -> 400 Bad Request", res.status_code == 400, res.status_code, res)
    wait()

    # --- 3.7 Non-JSON request body ---
    print("\n--- 3.7 Input Validation - Non-JSON body ---")
    res = requests.post(
        f"{BASE_URL}/api/faq/ask",
        data="this is not json",
        headers={**headers_a, "Content-Type": "application/json"},
        verify=False
    )
    test("Non-JSON body -> 400 Bad Request", res.status_code == 400, res.status_code, res)
    wait()

    # --- 3.8 FAQ without token ---
    print("\n--- 3.8 FAQ endpoint without token -> 401 ---")
    res = requests.post(
        f"{BASE_URL}/api/faq/ask",
        json={"question_text": "test"},
        verify=False
    )
    test("No token on FAQ -> 401 Unauthorized", res.status_code == 401, res.status_code, res)
    wait()

    # ========================================================
    # PART 4: HISTORY & OWNERSHIP CHECKS
    # ========================================================
    print_header("PART 4: HISTORY, CONVERSATIONS & OWNERSHIP CHECKS")

    # --- 4.1 User A gets their questions ---
    print("\n--- 4.1 User A gets their questions ---")
    res = requests.get(
        f"{BASE_URL}/api/faq/questions",
        headers=headers_a,
        verify=False
    )
    test("Get questions -> 200 OK", res.status_code == 200, res.status_code, res)
    if res.status_code == 200:
        questions = res.json().get('questions', [])
        test("User A sees their own questions", len(questions) >= 2)
        print(f"         Questions found: {len(questions)}")
    wait()

    # --- 4.2 User B gets their questions (should be empty) ---
    print("\n--- 4.2 User B gets their questions (should be empty) ---")
    if headers_b:
        res = requests.get(
            f"{BASE_URL}/api/faq/questions",
            headers=headers_b,
            verify=False
        )
        test("User B questions -> 200 OK", res.status_code == 200, res.status_code, res)
        if res.status_code == 200:
            questions_b = res.json().get('questions', [])
            test("User B sees EMPTY questions (ownership isolation)", len(questions_b) == 0)
    wait()

    # --- 4.3 User A gets history ---
    print("\n--- 4.3 User A gets answer history ---")
    res = requests.get(
        f"{BASE_URL}/api/faq/history",
        headers=headers_a,
        verify=False
    )
    test("Get history -> 200 OK", res.status_code == 200, res.status_code, res)
    if res.status_code == 200:
        history = res.json().get('history', [])
        test("History contains questions with answers", len(history) >= 1)
    wait()

    # --- 4.4 User A gets conversations ---
    print("\n--- 4.4 User A gets conversations ---")
    res = requests.get(
        f"{BASE_URL}/api/faq/conversations",
        headers=headers_a,
        verify=False
    )
    test("Get conversations -> 200 OK", res.status_code == 200, res.status_code, res)
    if res.status_code == 200:
        convos = res.json().get('conversations', [])
        test("Conversations list contains conv-001", "conv-001" in convos)
    wait()

    # --- 4.5 User A gets specific question by ID ---
    if question_id:
        print(f"\n--- 4.5 User A gets their own question (ID={question_id}) ---")
        res = requests.get(
            f"{BASE_URL}/api/faq/questions/{question_id}",
            headers=headers_a,
            verify=False
        )
        test(f"Get own question {question_id} -> 200 OK", res.status_code == 200, res.status_code, res)
    wait()

    # --- 4.6 OWNERSHIP CHECK: User B tries to access User A's question ---
    if question_id and headers_b:
        print(f"\n--- 4.6 OWNERSHIP CHECK - User B tries to access User A's question (ID={question_id}) ---")
        res = requests.get(
            f"{BASE_URL}/api/faq/questions/{question_id}",
            headers=headers_b,
            verify=False
        )
        test(
            "User B blocked from User A's question -> 403 or 404",
            res.status_code in [403, 404],
            res.status_code, res
        )
        if res.status_code in [403, 404]:
            test("Safe error message (no data leaked)", "traceback" not in res.text.lower())
    wait()

    # ========================================================
    # PART 5: SAFE ERROR HANDLING
    # ========================================================
    print_header("PART 5: SAFE ERROR HANDLING - No Stack Traces Leaked")

    print("\n--- 5.1 Malformed JSON ---")
    res = requests.post(
        f"{BASE_URL}/api/faq/ask",
        data="{bad json",
        headers={**headers_a, "Content-Type": "application/json"},
        verify=False
    )
    test("Malformed JSON -> 400 (not 500)", res.status_code == 400, res.status_code, res)
    test("No Python traceback in response", "traceback" not in res.text.lower() and "File " not in res.text)
    wait()

    print("\n--- 5.2 Nonexistent question ID ---")
    res = requests.get(
        f"{BASE_URL}/api/faq/questions/999999",
        headers=headers_a,
        verify=False
    )
    test("Nonexistent question -> 404", res.status_code == 404, res.status_code, res)

    # ========================================================
    # PART 6: DATABASE SCHEMA VERIFICATION
    # ========================================================
    print_header("PART 6: DATABASE SCHEMA VERIFICATION")
    print("\n  Running SQL queries inside postgres container...\n")

    # Read .env for DB credentials
    env_db = None
    env_user = None
    try:
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("POSTGRES_DB"):
                    env_db = line.split("=", 1)[1]
                elif line.startswith("POSTGRES_USER"):
                    env_user = line.split("=", 1)[1]
    except:
        pass

    db_name = env_db or "faq_db"
    db_user = env_user or "postgres"

    def run_db(query):
        cmd = f'docker exec postgres_db psql -U {db_user} -d {db_name} -t -A -c "{query}"'
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            return result.stdout.strip()
        except Exception as e:
            return f"ERROR: {e}"

    # 6.1 Check tables exist
    tables_output = run_db("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;")
    tables = [t.strip() for t in tables_output.split('\n') if t.strip()] if tables_output else []
    print(f"  Tables found: {tables}")

    # Check required FAQ tables
    expected_tables = ['questions', 'answers', 'documents', 'chunks']
    for t in expected_tables:
        test(f"Table '{t}' exists in PostgreSQL", t in tables)

    # Check audit logs table
    audit_exists = 'audit_logs' in tables or 'faq_audit_logs' in tables
    test("Audit logs table exists", audit_exists)

    # Check auth tables
    auth_tables = ['users', 'roles', 'permissions', 'user_roles']
    for t in auth_tables:
        test(f"Auth table '{t}' exists in PostgreSQL", t in tables)

    # 6.2 Check questions table has data
    q_count = run_db("SELECT count(*) FROM questions;")
    print(f"\n  Questions in DB: {q_count}")
    try:
        test("Questions table has records from tests", q_count and int(q_count) >= 2)
    except ValueError:
        test("Questions table has records from tests", False)

    # 6.3 Check answers table has data
    a_count = run_db("SELECT count(*) FROM answers;")
    print(f"  Answers in DB: {a_count}")
    try:
        test("Answers table has records from tests", a_count and int(a_count) >= 2)
    except ValueError:
        test("Answers table has records from tests", False)

    # 6.4 Check audit logs have data
    audit_table = 'faq_audit_logs' if 'faq_audit_logs' in tables else 'audit_logs'
    audit_count = run_db(f"SELECT count(*) FROM {audit_table};")
    print(f"  Audit log entries: {audit_count}")
    try:
        test("Audit logs recorded test actions", audit_count and int(audit_count) >= 1)
    except ValueError:
        test("Audit logs recorded test actions", False)

    # 6.5 Show sample data
    print("\n  --- Sample Question Record ---")
    sample = run_db("SELECT id, user_id, question_text, created_at FROM questions ORDER BY id DESC LIMIT 2;")
    for line in (sample or "No data").split('\n'):
        print(f"  {line}")

    print("\n  --- Sample Answer Record ---")
    sample_ans = run_db("SELECT id, question_id, answer_text, answer_source FROM answers ORDER BY id DESC LIMIT 2;")
    for line in (sample_ans or "No data").split('\n'):
        print(f"  {line}")

    print("\n  --- Sample Audit Log ---")
    sample_audit = run_db(f"SELECT id, user_id, action, status, ip_address FROM {audit_table} ORDER BY id DESC LIMIT 3;")
    for line in (sample_audit or "No data").split('\n'):
        print(f"  {line}")

    # ========================================================
    # SUMMARY
    # ========================================================
    print_header("TEST SUMMARY")
    print(f"\n  Total tests:  {total}")
    print(f"  Passed:      {passed}")
    print(f"  Failed:      {failed}")
    print(f"\n  Result: {'ALL TESTS PASSED!' if failed == 0 else f'{failed} TEST(S) FAILED'}")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  AI University FAQ Assistant - Full Test Suite")
    print("  Testing: Auth + FAQ + Security + DB Schema")
    print("="*60)
    run_tests()
