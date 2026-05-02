# Finai — Personal Finance Advisor Agent
## Project Specification for Claude Code

---

## Overview

Build a personal finance advisor agent called **Finai** using an agentic AI architecture. The agent helps users manage personal finances through natural conversation — analyzing spending, simulating investments, tracking goals, and providing proactive insights.

**Stack:**
- Python 3.13
- Anthropic SDK (via OpenRouter — same SDK, different base_url)
- Virtual environment (venv)
- Local JSON files as data store (MVP — no database yet)
- CLI interface (no frontend yet)

---

## Architecture: 3 Core Components

```
1. BRAIN   → Claude API (via OpenRouter) — thinks and decides
2. TOOLS   → Python functions the brain can call
3. LOOP    → Orchestrator: runs tools when brain requests them
```

The agent follows the **ReAct pattern**:
`User input → Brain thinks → Calls tool → Reads result → Thinks again → Answers`

---

## Project Structure

```
finai/
├── .env                    # API keys (never commit)
├── .gitignore
├── requirements.txt
├── main.py                 # CLI entry point
├── agent/
│   ├── __init__.py
│   ├── brain.py            # Claude API client + agentic loop
│   ├── tools.py            # Tool definitions (schema + handlers)
│   └── prompts.py          # System prompt builder
├── data/
│   ├── user_profile.json   # User profile + risk profile
│   ├── accounts.json       # Multiple bank accounts / e-wallets
│   ├── transactions.json   # Transaction history
│   └── goals.json          # Financial goals
└── tests/
    └── test_tools.py
```

---

## OpenRouter Configuration

```python
# agent/brain.py
import anthropic
import os

client = anthropic.Anthropic(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

MODEL = "anthropic/claude-sonnet-4-5"  # or whatever model is available
```

---

## Data Schemas (local JSON — MVP)

### user_profile.json
```json
{
  "name": "Andi Pratama",
  "city": "Jakarta",
  "profession": "Karyawan swasta",
  "dependents": "single",
  "monthly_income": 12000000,
  "monthly_expenses_estimate": 7000000,
  "current_savings": 30000000,
  "risk_profile": "undecided",
  "currency": "IDR"
}
```

### accounts.json
```json
[
  {
    "id": "acc_bca",
    "name": "BCA",
    "type": "savings",
    "balance": 12100000,
    "color": "#2563EB",
    "is_primary": true
  },
  {
    "id": "acc_jenius",
    "name": "Jenius",
    "type": "savings",
    "balance": 8300000,
    "color": "#7F77DD",
    "is_primary": false
  },
  {
    "id": "acc_gopay",
    "name": "GoPay",
    "type": "ewallet",
    "balance": 3000000,
    "color": "#1D9E75",
    "is_primary": false
  }
]
```

### transactions.json
```json
[
  {
    "id": "tx_001",
    "date": "2026-04-26",
    "time": "12:30",
    "merchant": "Warung Makan Padang",
    "amount": -32000,
    "category": "food_beverage",
    "account_id": "acc_bca",
    "notes": "",
    "source": "manual",
    "ai_categorized": false,
    "is_recurring": false
  }
]
```

**Categories enum:**
`food_beverage`, `transport`, `entertainment`, `bills`, `shopping`, `health`, `income`, `investment`, `other`

### goals.json
```json
[
  {
    "id": "goal_001",
    "name": "DP Rumah",
    "type": "house_dp",
    "target_amount": 100000000,
    "current_amount": 18000000,
    "monthly_contribution": 3000000,
    "account_id": "acc_bca",
    "target_date": "2028-12-01",
    "created_at": "2024-01-01",
    "milestones": [10000000, 20000000, 50000000, 100000000]
  },
  {
    "id": "goal_002",
    "name": "Dana Darurat",
    "type": "emergency_fund",
    "target_amount": 30000000,
    "current_amount": 12600000,
    "monthly_contribution": 1200000,
    "account_id": "acc_jenius",
    "target_date": "2027-06-01",
    "created_at": "2024-01-01",
    "milestones": [5000000, 10000000, 20000000, 30000000]
  }
]
```

---

## Tools to Implement

### Tool 1: get_transactions
```python
{
    "name": "get_transactions",
    "description": "Ambil histori transaksi user. Bisa filter by periode, kategori, akun, atau merchant.",
    "input_schema": {
        "type": "object",
        "properties": {
            "period": {
                "type": "string",
                "enum": ["today", "week", "month", "last_month", "year"],
                "description": "Periode transaksi"
            },
            "category": {
                "type": "string",
                "description": "Filter by kategori (optional)"
            },
            "account_id": {
                "type": "string",
                "description": "Filter by akun tertentu (optional). Kalau tidak diisi, ambil semua akun."
            },
            "merchant": {
                "type": "string",
                "description": "Filter by nama merchant (optional, case-insensitive partial match)"
            }
        },
        "required": ["period"]
    }
}
```

### Tool 2: calculate_budget
```python
{
    "name": "calculate_budget",
    "description": "Hitung ringkasan budget: total pemasukan, pengeluaran, savings rate, breakdown per kategori.",
    "input_schema": {
        "type": "object",
        "properties": {
            "period": {
                "type": "string",
                "enum": ["month", "last_month", "year"]
            },
            "account_id": {
                "type": "string",
                "description": "Filter by akun (optional)"
            }
        },
        "required": ["period"]
    }
}
```

### Tool 3: get_account_balances
```python
{
    "name": "get_account_balances",
    "description": "Ambil saldo semua akun atau akun tertentu.",
    "input_schema": {
        "type": "object",
        "properties": {
            "account_id": {
                "type": "string",
                "description": "ID akun tertentu (optional). Kalau kosong, return semua akun."
            }
        }
    }
}
```

### Tool 4: simulate_investment
```python
{
    "name": "simulate_investment",
    "description": "Simulasi pertumbuhan investasi dengan compound interest.",
    "input_schema": {
        "type": "object",
        "properties": {
            "monthly_amount": {
                "type": "number",
                "description": "Jumlah investasi per bulan dalam IDR"
            },
            "annual_return_pct": {
                "type": "number",
                "description": "Return tahunan dalam persen (contoh: 10 untuk 10%)"
            },
            "years": {
                "type": "integer",
                "description": "Durasi investasi dalam tahun"
            }
        },
        "required": ["monthly_amount", "annual_return_pct", "years"]
    }
}
```

### Tool 5: get_goals
```python
{
    "name": "get_goals",
    "description": "Ambil semua financial goals user beserta progress-nya.",
    "input_schema": {
        "type": "object",
        "properties": {
            "goal_id": {
                "type": "string",
                "description": "ID goal tertentu (optional). Kalau kosong, return semua goals."
            }
        }
    }
}
```

### Tool 6: categorize_transaction
```python
{
    "name": "categorize_transaction",
    "description": "Kategorisasi otomatis sebuah transaksi berdasarkan nama merchant.",
    "input_schema": {
        "type": "object",
        "properties": {
            "merchant": {
                "type": "string",
                "description": "Nama merchant"
            },
            "amount": {
                "type": "number",
                "description": "Nominal transaksi"
            }
        },
        "required": ["merchant", "amount"]
    }
}
```

---

## Agentic Loop (brain.py)

```python
def run_agent(user_message: str, conversation_history: list, user_context: dict) -> str:
    """
    Main agentic loop.
    - Injects user context into system prompt
    - Handles tool calls automatically
    - Returns final text response
    """
    
    system_prompt = build_system_prompt(user_context)
    conversation_history.append({"role": "user", "content": user_message})
    
    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            system=system_prompt,
            tools=TOOL_DEFINITIONS,
            messages=conversation_history
        )
        
        # Agent finished — return answer
        if response.stop_reason == "end_turn":
            final_text = next(
                block.text for block in response.content 
                if hasattr(block, "text")
            )
            conversation_history.append({
                "role": "assistant", 
                "content": response.content
            })
            return final_text
        
        # Agent wants to use tools
        if response.stop_reason == "tool_use":
            conversation_history.append({
                "role": "assistant", 
                "content": response.content
            })
            
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    # Execute the tool
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, ensure_ascii=False)
                    })
            
            conversation_history.append({
                "role": "user", 
                "content": tool_results
            })
            # Loop continues — agent processes tool results
```

---

## System Prompt Structure (prompts.py)

```python
def build_system_prompt(user_context: dict) -> str:
    return f"""
Kamu adalah Finai, personal finance advisor AI untuk {user_context['name']}.
Kamu berbicara dalam Bahasa Indonesia, ramah tapi profesional.
Selalu kasih advice yang actionable dan spesifik berdasarkan data keuangan user.

PROFIL USER:
- Nama: {user_context['name']}
- Kota: {user_context['city']}
- Penghasilan/bulan: Rp {user_context['monthly_income']:,}
- Profil risiko: {user_context['risk_profile']}

AKUN AKTIF:
{format_accounts(user_context['accounts'])}

GUIDELINES:
- Selalu gunakan tools untuk ambil data terbaru sebelum memberi analisis
- Sebut nama akun spesifik saat membahas transaksi (BCA, GoPay, dll)
- Format angka dalam Rupiah: Rp X.XXX.XXX atau shorthand (1.2jt, 500K)
- Kalau user tanya tentang investasi, selalu tanyakan atau cek profil risiko mereka
- Jangan kasih saran investasi spesifik (saham/kripto tertentu) — fokus ke instrumen umum
- Selalu sertakan disclaimer kalau relevan dengan keputusan finansial besar
"""
```

---

## CLI Interface (main.py)

```python
def main():
    """
    Simple CLI loop for testing the agent.
    Commands:
      'quit' or 'exit' — keluar
      'reset'          — reset conversation history
      'balance'        — shortcut cek saldo
    """
```

---

## Key Behaviors to Implement

1. **Multi-account awareness** — agent selalu tahu transaksi dari akun mana, bisa filter by account
2. **Context injection** — setiap conversation bawa user profile + account list di system prompt
3. **Tool chaining** — agent bisa panggil multiple tools dalam satu response (contoh: get_transactions lalu calculate_budget)
4. **Number formatting** — semua angka IDR diformat konsisten: Rp 1.200.000 atau 1.2jt
5. **Error handling** — kalau tool gagal, agent tetap bisa jawab dengan graceful fallback

---

## Seed Data

Buat dummy data yang realistis untuk testing:
- Minimal **30 transaksi** bulan April 2026 tersebar di semua akun
- Mix kategori: food (40%), transport (15%), bills (20%), entertainment (15%), other (10%)
- Include beberapa recurring transactions (Netflix, Spotify, PLN)
- Income entry: gaji tanggal 25
- Satu anomaly: transaksi besar yang tidak biasa (untuk test anomaly detection nanti)

---

## What to Build First (Phase 1)

1. Project structure + venv setup
2. .env + .gitignore
3. Seed JSON data files
4. Tool handler functions (tools.py)
5. Agentic loop (brain.py)
6. System prompt builder (prompts.py)
7. CLI main loop (main.py)
8. Test with 5 sample conversations:
   - "Pengeluaran gw bulan ini gimana?"
   - "Gw punya berapa di semua akun?"
   - "Kalau invest 2jt per bulan 10 tahun, balik berapa?"
   - "GoPay gw cukup nggak sampai akhir bulan?"
   - "Progress goals gw gimana?"

---

## Out of Scope for Phase 1

- Database (SQLite/PostgreSQL) — Phase 2
- REST API — Phase 2
- Frontend — Phase 3
- Receipt OCR — Phase 3
- Bank API integration — Phase 3
- Authentication — Phase 2

---

## Notes for Claude Code

- Keep each file under 200 lines — split if needed
- Add docstrings to all functions
- Print tool calls to console so developer can see agent thinking
- Use `python-dotenv` for env management
- All monetary amounts stored as integers (IDR, no decimals)
- Dates stored as ISO strings: "2026-04-26"
