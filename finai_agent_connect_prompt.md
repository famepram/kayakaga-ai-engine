# Prompt for Claude Code — Connect finai-agent ke kayakaga-api

Tugasmu adalah update `agent/tools.py` di project finai-agent.
Ganti semua implementasi yang baca dari JSON files lokal
menjadi HTTP calls ke kayakaga-api yang sudah berjalan.

---

## Environment Variables

Tambahkan ke `.env` finai-agent:
```
FINAI_API_URL=http://localhost:8080
FINAI_API_EMAIL=andi@finai.dev
FINAI_API_PASSWORD=finai123
FINAI_ACCESS_TOKEN=    # akan diisi otomatis saat login
```

---

## Auth Module (agent/auth.py) — BUAT BARU

Buat file baru `agent/auth.py` untuk handle login dan token refresh:

```python
import os
import requests
from datetime import datetime, timedelta

API_URL = os.getenv("FINAI_API_URL", "http://localhost:8080")

_access_token = None
_token_expires_at = None

def get_token() -> str:
    """Get valid access token, auto-login jika belum ada atau expired."""
    global _access_token, _token_expires_at
    
    if _access_token and _token_expires_at and datetime.now() < _token_expires_at:
        return _access_token
    
    return _login()

def _login() -> str:
    global _access_token, _token_expires_at
    
    response = requests.post(
        f"{API_URL}/api/v1/auth/login",
        json={
            "email": os.getenv("FINAI_API_EMAIL"),
            "password": os.getenv("FINAI_API_PASSWORD")
        },
        timeout=10
    )
    
    if response.status_code != 200:
        raise Exception(f"Login failed: {response.text}")
    
    data = response.json()["data"]
    _access_token = data["access_token"]
    # Access token expire 15 menit, refresh 1 menit sebelumnya
    _token_expires_at = datetime.now() + timedelta(minutes=14)
    
    return _access_token

def get_headers() -> dict:
    return {
        "Authorization": f"Bearer {get_token()}",
        "Content-Type": "application/json"
    }

def api_get(endpoint: str, params: dict = None) -> dict:
    """Helper untuk GET request ke API."""
    response = requests.get(
        f"{API_URL}{endpoint}",
        headers=get_headers(),
        params=params,
        timeout=10
    )
    if not response.ok:
        return {"error": f"API error {response.status_code}: {response.text}"}
    return response.json().get("data", {})
```

---

## Update tools.py — Ganti semua handler

Ganti semua tool handler functions. Jangan ubah TOOL_DEFINITIONS
(schema tetap sama). Hanya implementasi handler-nya yang berubah.

### Tool 1: get_transactions

```python
def handle_get_transactions(tool_input: dict) -> dict:
    params = {"period": tool_input.get("period", "month")}
    
    if tool_input.get("account_id"):
        # Support nama akun (BCA, GoPay) atau ID angka
        account_id = resolve_account_id(tool_input["account_id"])
        if account_id:
            params["account_id"] = account_id
    
    if tool_input.get("category"):
        category_id = resolve_category_id(tool_input["category"])
        if category_id:
            params["category_id"] = category_id
    
    if tool_input.get("merchant"):
        params["merchant"] = tool_input["merchant"]
    
    data = api_get("/api/v1/transactions", params)
    
    transactions = data.get("transactions", [])
    summary = data.get("summary", {})
    
    return {
        "transactions": transactions,
        "total_in": summary.get("total_in", 0),
        "total_out": summary.get("total_out", 0),
        "count": summary.get("count", 0)
    }
```

### Tool 2: calculate_budget

```python
def handle_calculate_budget(tool_input: dict) -> dict:
    params = {"period": tool_input.get("period", "month")}
    
    if tool_input.get("account_id"):
        account_id = resolve_account_id(tool_input["account_id"])
        if account_id:
            params["account_id"] = account_id
    
    data = api_get("/api/v1/analytics/budget", params)
    
    return {
        "income": data.get("income", 0),
        "expenses": data.get("expenses", 0),
        "savings_rate": data.get("savings_rate", 0),
        "breakdown": data.get("breakdown", [])
    }
```

### Tool 3: get_account_balances

```python
def handle_get_account_balances(tool_input: dict) -> dict:
    params = {}
    
    if tool_input.get("account_id"):
        account_id = resolve_account_id(tool_input["account_id"])
        if account_id:
            params["account_id"] = account_id
    
    data = api_get("/api/v1/accounts/balances", params)
    
    accounts = data.get("accounts", [])
    total = data.get("total", 0)
    
    # Enrich dengan nama account type
    return {
        "accounts": [
            {
                "id": acc["id"],
                "name": acc["name"],
                "balance": acc["balance"],
                "is_primary": acc["is_primary"]
            }
            for acc in accounts
        ],
        "total": total,
        "count": len(accounts)
    }
```

### Tool 4: simulate_investment

```python
def handle_simulate_investment(tool_input: dict) -> dict:
    params = {
        "monthly_amount": tool_input["monthly_amount"],
        "annual_return_pct": tool_input["annual_return_pct"],
        "years": tool_input["years"]
    }
    
    data = api_get("/api/v1/simulate/investment", params)
    
    return {
        "future_value": data.get("future_value", 0),
        "total_invested": data.get("total_invested", 0),
        "profit": data.get("profit", 0),
        "roi_pct": round(data.get("roi_pct", 0), 1),
        "monthly_breakdown": data.get("monthly_breakdown", [])
    }
```

### Tool 5: get_goals

```python
def handle_get_goals(tool_input: dict) -> dict:
    if tool_input.get("goal_id"):
        data = api_get(f"/api/v1/goals/{tool_input['goal_id']}")
        goals = [data] if data else []
    else:
        data = api_get("/api/v1/goals")
        goals = data if isinstance(data, list) else []
    
    return {
        "goals": [
            {
                "id": g["id"],
                "name": g["name"],
                "target_amount": g["target_amount"],
                "current_amount": g["current_amount"],
                "monthly_contribution": g["monthly_contribution"],
                "progress_pct": g["progress_pct"],
                "eta_months": g["eta_months"],
                "eta_date": g["eta_date"],
                "target_date": g["target_date"]
            }
            for g in goals
        ],
        "count": len(goals)
    }
```

### Tool 6: categorize_transaction

```python
def handle_categorize_transaction(tool_input: dict) -> dict:
    # Keyword matching (tidak perlu API call, logic lokal sudah cukup)
    merchant = tool_input["merchant"].lower()
    
    keyword_map = {
        "income": ["gaji", "salary", "transfer masuk", "bonus"],
        "transport": ["grab", "gojek", "ojek", "taxi", "parkir", "transjakarta"],
        "entertainment": ["netflix", "spotify", "youtube", "steam", "game", "cgv", "cinema", "bioskop"],
        "bills": ["pln", "listrik", "pdam", "air", "internet", "wifi", "bpjs", "telkom", "indihome"],
        "shopping": ["indomaret", "alfamart", "supermarket", "mall", "tokopedia", "shopee", "lazada"],
        "health": ["apotek", "klinik", "dokter", "rumah sakit", "obat", "medis", "k24"],
        "food_beverage": ["warung", "makan", "resto", "restaurant", "cafe", "kopi", "mcd", "mcdonalds", "gofood", "grab food"],
        "investment": ["investasi", "saham", "reksa", "tabungan", "transfer tabungan"]
    }
    
    category_id_map = {
        "food_beverage": 1, "transport": 2, "entertainment": 3,
        "bills": 4, "shopping": 5, "health": 6,
        "investment": 7, "other": 8, "income": 9
    }
    
    for category, keywords in keyword_map.items():
        if any(kw in merchant for kw in keywords):
            return {
                "category": category,
                "category_id": category_id_map[category],
                "confidence": 0.85
            }
    
    return {
        "category": "other",
        "category_id": 8,
        "confidence": 0.5
    }
```

### Tool 7: detect_anomaly

```python
def handle_detect_anomaly(tool_input: dict) -> dict:
    params = {"period": tool_input.get("period", "month")}
    
    if tool_input.get("account_id"):
        account_id = resolve_account_id(tool_input["account_id"])
        if account_id:
            params["account_id"] = account_id
    
    data = api_get("/api/v1/analytics/anomalies", params)
    anomalies = data.get("anomalies", [])
    
    return {
        "anomalies": anomalies,
        "count": len(anomalies)
    }
```

### Tool 8: compare_spending

```python
def handle_compare_spending(tool_input: dict) -> dict:
    params = {}
    
    if tool_input.get("account_id"):
        account_id = resolve_account_id(tool_input["account_id"])
        if account_id:
            params["account_id"] = account_id
    
    data = api_get("/api/v1/analytics/compare", params)
    comparison = data.get("comparison", [])
    
    # Sort by absolute delta
    sorted_comparison = sorted(
        comparison,
        key=lambda x: abs(x.get("delta_pct", 0)),
        reverse=True
    )
    
    return {
        "comparison": sorted_comparison,
        "biggest_increase": next(
            (c for c in sorted_comparison if c.get("trend") == "up"), None
        ),
        "biggest_decrease": next(
            (c for c in sorted_comparison if c.get("trend") == "down"), None
        )
    }
```

### Tool 9: get_recurring_transactions

```python
def handle_get_recurring_transactions(tool_input: dict) -> dict:
    params = {}
    
    if tool_input.get("account_id"):
        account_id = resolve_account_id(tool_input["account_id"])
        if account_id:
            params["account_id"] = account_id
    
    data = api_get("/api/v1/analytics/recurring", params)
    
    return {
        "items": data.get("items", []),
        "total_monthly": data.get("total_monthly", 0),
        "count": len(data.get("items", []))
    }
```

### Tool 10: suggest_savings

```python
def handle_suggest_savings(tool_input: dict) -> dict:
    params = {}
    if tool_input.get("target_savings"):
        params["target_savings"] = tool_input["target_savings"]
    
    data = api_get("/api/v1/analytics/savings-suggestion", params)
    
    return {
        "suggestions": data.get("suggestions", []),
        "total_potential_saving": data.get("total_potential_saving", 0),
        "impact_on_goals": data.get("impact_on_goals", "")
    }
```

### Tool 11: calculate_goal_recommendation

```python
def handle_calculate_goal_recommendation(tool_input: dict) -> dict:
    params = {"goal_id": tool_input["goal_id"]}
    
    if tool_input.get("target_months"):
        params["target_months"] = tool_input["target_months"]
    if tool_input.get("new_monthly_contribution"):
        params["new_monthly_contribution"] = tool_input["new_monthly_contribution"]
    
    data = api_get("/api/v1/analytics/goal-recommendation", params)
    
    return {
        "goal_name": data.get("goal_name"),
        "remaining_amount": data.get("remaining_amount", 0),
        "current_contribution": data.get("current_contribution", 0),
        "current_eta_months": data.get("current_eta_months", 0),
        "current_eta_date": data.get("current_eta_date"),
        "scenarios": data.get("scenarios", [])
    }
```

---

## Helper Functions (tambahkan di tools.py)

```python
# Cache untuk master data — load sekali saja
_accounts_cache = None
_categories_cache = None

def _get_accounts() -> list:
    global _accounts_cache
    if not _accounts_cache:
        data = api_get("/api/v1/accounts")
        _accounts_cache = data.get("accounts", []) if isinstance(data, dict) else data
    return _accounts_cache or []

def _get_categories() -> list:
    global _categories_cache
    if not _categories_cache:
        data = api_get("/api/v1/masters/categories")
        _categories_cache = data if isinstance(data, list) else []
    return _categories_cache or []

def resolve_account_id(account_ref) -> int | None:
    """Resolve nama akun atau ID ke account_id integer."""
    if isinstance(account_ref, int):
        return account_ref
    
    # Coba parse sebagai integer
    try:
        return int(account_ref)
    except (ValueError, TypeError):
        pass
    
    # Cari by nama (case-insensitive)
    accounts = _get_accounts()
    for acc in accounts:
        if acc["name"].lower() == str(account_ref).lower():
            return acc["id"]
    
    return None

def resolve_category_id(category_ref) -> int | None:
    """Resolve nama kategori atau code ke category_id."""
    if isinstance(category_ref, int):
        return category_ref
    
    try:
        return int(category_ref)
    except (ValueError, TypeError):
        pass
    
    categories = _get_categories()
    ref_lower = str(category_ref).lower()
    for cat in categories:
        if cat["code"].lower() == ref_lower or cat["name"].lower() == ref_lower:
            return cat["id"]
    
    return None
```

---

## Update execute_tool() di brain.py

Ganti mapping di execute_tool():

```python
def execute_tool(tool_name: str, tool_input: dict) -> dict:
    tool_map = {
        "get_transactions":              handle_get_transactions,
        "calculate_budget":              handle_calculate_budget,
        "get_account_balances":          handle_get_account_balances,
        "simulate_investment":           handle_simulate_investment,
        "get_goals":                     handle_get_goals,
        "categorize_transaction":        handle_categorize_transaction,
        "detect_anomaly":                handle_detect_anomaly,
        "compare_spending":              handle_compare_spending,
        "get_recurring_transactions":    handle_get_recurring_transactions,
        "suggest_savings":               handle_suggest_savings,
        "calculate_goal_recommendation": handle_calculate_goal_recommendation,
    }
    
    handler = tool_map.get(tool_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name}"}
    
    try:
        return handler(tool_input)
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to API. Make sure kayakaga-api is running."}
    except requests.exceptions.Timeout:
        return {"error": "API request timed out. Please try again."}
    except Exception as e:
        return {"error": str(e)}
```

---

## Update prompts.py — Load context dari API

```python
def build_system_prompt() -> str:
    """Build system prompt dengan data user dari API."""
    from agent.auth import api_get
    
    # Load user profile
    profile = api_get("/api/v1/users/profile") or {}
    
    # Load accounts
    balances_data = api_get("/api/v1/accounts/balances") or {}
    accounts = balances_data.get("accounts", [])
    
    accounts_text = "\n".join([
        f"- {acc['name']}: Rp {acc['balance']:,} {'(primary)' if acc['is_primary'] else ''}"
        for acc in accounts
    ])
    
    return f"""
Kamu adalah Finai, personal finance advisor AI untuk {profile.get('name', 'User')}.
Kamu berbicara dalam Bahasa Indonesia, ramah tapi profesional.
Selalu kasih advice yang actionable dan spesifik berdasarkan data keuangan user.

PROFIL USER:
- Nama: {profile.get('name', '-')}
- Kota: {profile.get('city', '-')}
- Penghasilan/bulan: Rp {profile.get('monthly_income', 0):,}
- Profil risiko: {profile.get('risk_profile', 'undecided')}

AKUN AKTIF:
{accounts_text if accounts_text else '- Belum ada akun'}

RESPONSE RULES:
- Pertanyaan cek/status → maksimal 4-5 baris, langsung ke poin
- Pertanyaan analisis → maksimal 8-10 baris, satu insight utama
- Pertanyaan perencanaan → boleh detail, maksimal 3 rekomendasi
- Jangan gunakan LaTeX notation
- Jangan basa-basi di awal atau akhir response
- Sebut nama akun spesifik (BCA, GoPay, Jenius)
- Format angka: Rp 1.200.000 atau shorthand (1.2jt, 500K)

MANDATORY TOOL USAGE:
- WAJIB call tools untuk setiap pertanyaan yang butuh data keuangan
- DILARANG jawab dari asumsi atau ingatan
- Untuk pertanyaan akun spesifik: filter semua tool calls dengan account_id

DISCLAIMER:
- Sertakan disclaimer HANYA untuk keputusan investasi besar atau utang
- Untuk cek saldo/transaksi: tidak perlu disclaimer
"""
```

---

## Update main.py

```python
def main():
    print("🚀 Memuat profil dari API...")
    
    # Test koneksi ke API
    try:
        from agent.auth import get_token
        get_token()
        print("✅ Terhubung ke kayakaga-api")
    except Exception as e:
        print(f"❌ Gagal terhubung ke API: {e}")
        print("Pastikan kayakaga-api berjalan di http://localhost:8080")
        return
    
    # Build system prompt dari API
    system_prompt = build_system_prompt()
    
    print("\n💬 Finai siap! Ketik 'quit' untuk keluar, 'reset' untuk mulai ulang.\n")
    
    conversation_history = []
    
    while True:
        user_input = input("👤 Kamu: ").strip()
        
        if not user_input:
            continue
        if user_input.lower() in ["quit", "exit"]:
            print("👋 Sampai jumpa!")
            break
        if user_input.lower() == "reset":
            conversation_history = []
            print("🔄 Conversation direset.\n")
            continue
        
        # Shortcuts
        shortcuts = {
            "/balance": "Cek saldo semua akun",
            "/goals": "Progress goals gw gimana?",
            "/budget": "Pengeluaran bulan ini gimana?",
            "/anomaly": "Ada transaksi mencurigakan?"
        }
        if user_input in shortcuts:
            user_input = shortcuts[user_input]
        
        print("🤖 Finai sedang berpikir...")
        response = run_agent(user_input, conversation_history, system_prompt)
        print(f"\n🤖 Finai: {response}\n")
```

---

## Requirements.txt — Pastikan ada

```
anthropic
python-dotenv
requests
```

---

## Test setelah update

Jalankan dan test 5 pertanyaan ini:

1. "Cek saldo semua akun"
   → harus call get_account_balances, return 3 akun total 23.4jt

2. "Pengeluaran bulan ini gimana?"
   → harus call calculate_budget, return income 12jt expenses 7.6jt

3. "Ada transaksi mencurigakan?"
   → harus call detect_anomaly, return Steam Games + Seafood Ancol

4. "Langganan gw ada apa aja?"
   → harus call get_recurring_transactions, return Netflix, Spotify, PLN, dll

5. "Kalau gw naikin DP rumah jadi 4jt/bulan, selesai kapan?"
   → harus call get_goals lalu calculate_goal_recommendation
