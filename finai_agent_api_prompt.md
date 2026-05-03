# Prompt 1 — finai-agent-api (FastAPI)

Wrap finai-agent menjadi FastAPI service.
Tambahkan file baru tanpa mengubah struktur yang sudah ada.

---

## Tambahan struktur

```
finai-agent/
├── api.py                  # BARU — FastAPI entry point
├── agent/
│   ├── brain.py            # Update — terima user_token per request
│   ├── tools.py            # Update — pakai user_token bukan .env token
│   ├── auth.py             # Update — support per-request token
│   └── prompts.py          # Tetap sama
├── main.py                 # Tetap sama — CLI masih bisa jalan
├── requirements.txt        # Update — tambah fastapi, uvicorn
└── .env                    # Update — tambah config baru
```

---

## .env additions

```
# Existing
OPENROUTER_API_KEY=
FINAI_API_URL=http://localhost:8080

# New
AGENT_PORT=8000
AGENT_HOST=0.0.0.0
KAYAKAGA_API_URL=http://localhost:8080   # internal communication
```

---

## api.py — FastAPI entry point

```python
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Finai Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict di production
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    conversation_history: list = []
    user_token: str              # JWT token dari kayakaga-api
    user_context: dict = {}      # profile + accounts untuk system prompt

class ChatResponse(BaseModel):
    reply: str
    conversation_history: list
    tools_called: list = []

class ResetResponse(BaseModel):
    success: bool
    message: str

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "finai-agent-api"}

@app.post("/agent/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Process chat message dari user.
    user_token dipakai untuk tools call ke kayakaga-api.
    """
    try:
        from agent.brain import run_agent
        from agent.prompts import build_system_prompt

        # Build system prompt dari user_context yang dikirim
        system_prompt = build_system_prompt(request.user_context)

        # Track tools yang dipanggil
        tools_called = []

        reply, updated_history = run_agent(
            user_message=request.message,
            conversation_history=request.conversation_history,
            system_prompt=system_prompt,
            user_token=request.user_token,
            tools_called_tracker=tools_called
        )

        return ChatResponse(
            reply=reply,
            conversation_history=updated_history,
            tools_called=tools_called
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/agent/chat/reset")
def reset_chat():
    """Reset conversation — client handle history, ini hanya acknowledgment."""
    return ResetResponse(success=True, message="Conversation reset")

if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host=os.getenv("AGENT_HOST", "0.0.0.0"),
        port=int(os.getenv("AGENT_PORT", 8000)),
        reload=os.getenv("APP_ENV") == "development"
    )
```

---

## Update agent/brain.py

Tambah parameter `user_token` dan `tools_called_tracker`:

```python
def run_agent(
    user_message: str,
    conversation_history: list,
    system_prompt: str,
    user_token: str = None,
    tools_called_tracker: list = None
) -> tuple[str, list]:
    """
    Main agentic loop.
    user_token: JWT token untuk tools call ke kayakaga-api
    tools_called_tracker: list untuk track tool calls (untuk response)
    """
    conversation_history = conversation_history.copy()
    conversation_history.append({"role": "user", "content": user_message})

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            system=system_prompt,
            tools=TOOL_DEFINITIONS,
            messages=conversation_history
        )

        if response.stop_reason == "end_turn":
            final_text = next(
                block.text for block in response.content
                if hasattr(block, "text")
            )
            conversation_history.append({
                "role": "assistant",
                "content": response.content
            })
            return final_text, conversation_history

        if response.stop_reason == "tool_use":
            conversation_history.append({
                "role": "assistant",
                "content": response.content
            })

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  🔧 [TOOL] {block.name}({json.dumps(block.input)})")

                    # Pass user_token ke execute_tool
                    result = execute_tool(
                        block.name,
                        block.input,
                        user_token=user_token
                    )

                    print(f"  ✅ [RESULT] {json.dumps(result)[:100]}")

                    # Track tool calls
                    if tools_called_tracker is not None:
                        tools_called_tracker.append({
                            "tool": block.name,
                            "input": block.input,
                            "result_summary": str(result)[:200]
                        })

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, ensure_ascii=False)
                    })

            conversation_history.append({
                "role": "user",
                "content": tool_results
            })
```

---

## Update agent/tools.py

Ganti semua `api_get` calls untuk terima `user_token` per request.
Hapus dependency ke .env untuk token:

```python
import os
import requests
from typing import Optional

KAYAKAGA_API_URL = os.getenv("KAYAKAGA_API_URL", "http://localhost:8080")

def _get_headers(user_token: str) -> dict:
    """Build headers dengan user token."""
    return {
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json"
    }

def api_get(endpoint: str, params: dict = None, user_token: str = None) -> dict:
    """GET request ke kayakaga-api dengan user token."""
    if not user_token:
        return {"error": "No user token provided"}

    try:
        response = requests.get(
            f"{KAYAKAGA_API_URL}{endpoint}",
            headers=_get_headers(user_token),
            params=params,
            timeout=15
        )
        if not response.ok:
            return {"error": f"API error {response.status_code}"}
        return response.json().get("data", {})
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to kayakaga-api"}
    except requests.exceptions.Timeout:
        return {"error": "Request timeout"}
    except Exception as e:
        return {"error": str(e)}

# Semua handler terima user_token sebagai parameter
def handle_get_transactions(tool_input: dict, user_token: str = None) -> dict:
    params = {"period": tool_input.get("period", "month")}
    if tool_input.get("account_id"):
        account_id = resolve_account_id(tool_input["account_id"], user_token)
        if account_id:
            params["account_id"] = account_id
    if tool_input.get("category"):
        category_id = resolve_category_id(tool_input["category"], user_token)
        if category_id:
            params["category_id"] = category_id
    if tool_input.get("merchant"):
        params["merchant"] = tool_input["merchant"]

    data = api_get("/api/v1/transactions", params, user_token)
    transactions = data.get("transactions", [])
    summary = data.get("summary", {})
    return {
        "transactions": transactions,
        "total_in": summary.get("total_in", 0),
        "total_out": summary.get("total_out", 0),
        "count": summary.get("count", 0)
    }

# Pattern yang sama untuk semua handler lainnya:
# def handle_xxx(tool_input: dict, user_token: str = None) -> dict:

def execute_tool(tool_name: str, tool_input: dict, user_token: str = None) -> dict:
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
        return handler(tool_input, user_token=user_token)
    except Exception as e:
        return {"error": str(e)}
```

---

## Update agent/prompts.py

Terima `user_context` dict sebagai parameter (bukan load dari API):

```python
def build_system_prompt(user_context: dict = None) -> str:
    """
    Build system prompt dari user_context yang dikirim kayakaga-api.
    user_context berisi: name, city, monthly_income, risk_profile, accounts
    """
    if not user_context:
        user_context = {}

    name = user_context.get("name", "User")
    city = user_context.get("city", "-")
    monthly_income = user_context.get("monthly_income", 0)
    risk_profile = user_context.get("risk_profile", "undecided")
    accounts = user_context.get("accounts", [])

    accounts_text = "\n".join([
        f"- {acc.get('name', '-')}: Rp {acc.get('balance', 0):,}"
        f"{'(primary)' if acc.get('is_primary') else ''}"
        for acc in accounts
    ]) if accounts else "- Belum ada akun"

    return f"""
Kamu adalah Finai, personal finance advisor AI untuk {name}.
Kamu berbicara dalam Bahasa Indonesia, ramah tapi profesional.
Selalu kasih advice yang actionable dan spesifik berdasarkan data keuangan user.

PROFIL USER:
- Nama: {name}
- Kota: {city}
- Penghasilan/bulan: Rp {monthly_income:,}
- Profil risiko: {risk_profile}

AKUN AKTIF:
{accounts_text}

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

## Update requirements.txt

```
anthropic
python-dotenv
requests
fastapi
uvicorn[standard]
pydantic
```

---

## Cara run

```bash
# Development
python api.py

# Atau dengan uvicorn langsung
uvicorn api:app --host 0.0.0.0 --port 8000 --reload

# CLI tetap bisa jalan seperti biasa
python main.py
```

---

## Test setelah build

```bash
# Health check
curl http://localhost:8000/health

# Chat test (butuh valid JWT token dari kayakaga-api)
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Cek saldo semua akun",
    "conversation_history": [],
    "user_token": "eyJ...",
    "user_context": {
      "name": "Andi Pratama",
      "city": "Jakarta",
      "monthly_income": 12000000,
      "risk_profile": "undecided",
      "accounts": [
        {"name": "BCA", "balance": 12100000, "is_primary": true},
        {"name": "Jenius", "balance": 8300000, "is_primary": false},
        {"name": "GoPay", "balance": 3000000, "is_primary": false}
      ]
    }
  }'

# Expected response:
# {
#   "reply": "Total saldo kamu Rp 23.4jt...",
#   "conversation_history": [...],
#   "tools_called": [{"tool": "get_account_balances", ...}]
# }
```

---

## Build order

1. Update requirements.txt
2. Update agent/tools.py — tambah user_token ke semua handlers
3. Update agent/brain.py — tambah user_token + tools_called_tracker params
4. Update agent/prompts.py — terima user_context dict
5. Buat api.py
6. Test health check
7. Test chat endpoint
