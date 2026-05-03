"""
Finai Agent Tools - API Version with Per-Request Token
All tool handlers using HTTP calls to kayakaga-api with user_token
"""

import os
import requests
from typing import Dict, Optional

KAYAKAGA_API_URL = os.getenv("KAYAKAGA_API_URL", "http://localhost:8080")


# ============================================
# CACHE untuk master data
# ============================================

_accounts_cache = None
_categories_cache = None


def _get_headers(user_token: str) -> dict:
    """Build headers dengan user token."""
    return {
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json"
    }


def api_get(endpoint: str, params: dict = None, user_token: str = None) -> dict:
    """
    GET request ke kayakaga-api dengan user token.

    Args:
        endpoint: API endpoint path (contoh: "/api/v1/transactions")
        params: Query parameters (optional)
        user_token: JWT token dari user (required)

    Returns:
        Data dari response API, atau dict dengan error key
    """
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
            return {"error": f"API error {response.status_code}: {response.text}"}
        return response.json().get("data", {})
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to kayakaga-api"}
    except requests.exceptions.Timeout:
        return {"error": "Request timeout"}
    except Exception as e:
        return {"error": str(e)}


def _get_accounts(user_token: str) -> list:
    """Get accounts dari API dengan cache."""
    global _accounts_cache
    if not _accounts_cache:
        data = api_get("/api/v1/accounts", user_token=user_token)
        _accounts_cache = data.get("accounts", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    return _accounts_cache or []


def _get_categories(user_token: str) -> list:
    """Get categories dari API dengan cache."""
    global _categories_cache
    if not _categories_cache:
        data = api_get("/api/v1/masters/categories", user_token=user_token)
        _categories_cache = data if isinstance(data, list) else []
    return _categories_cache or []


def resolve_account_id(account_ref, user_token: str) -> Optional[int]:
    """
    Resolve nama akun atau ID ke account_id integer.

    Args:
        account_ref: Account ID (int) atau nama (string)
        user_token: JWT token untuk API call

    Returns:
        Integer account_id atau None
    """
    if isinstance(account_ref, int):
        return account_ref

    # Coba parse sebagai integer
    try:
        return int(account_ref)
    except (ValueError, TypeError):
        pass

    # Cari by nama (case-insensitive)
    accounts = _get_accounts(user_token)
    for acc in accounts:
        if acc["name"].lower() == str(account_ref).lower():
            return acc["id"]

    return None


def resolve_category_id(category_ref, user_token: str) -> Optional[int]:
    """
    Resolve nama kategori atau code ke category_id.

    Args:
        category_ref: Category ID (int) atau nama/code (string)
        user_token: JWT token untuk API call

    Returns:
        Integer category_id atau None
    """
    if isinstance(category_ref, int):
        return category_ref

    try:
        return int(category_ref)
    except (ValueError, TypeError):
        pass

    categories = _get_categories(user_token)
    ref_lower = str(category_ref).lower()
    for cat in categories:
        if cat["code"].lower() == ref_lower or cat["name"].lower() == ref_lower:
            return cat["id"]

    return None


# ============================================
# TOOL HANDLERS (dengan user_token)
# ============================================

def handle_get_transactions(tool_input: dict, user_token: str = None) -> dict:
    """Handler untuk get_transactions tool."""
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
        "net": summary.get("net", 0),
        "count": summary.get("count", 0)
    }


def handle_calculate_budget(tool_input: dict, user_token: str = None) -> dict:
    """Handler untuk calculate_budget tool."""
    params = {"period": tool_input.get("period", "month")}

    if tool_input.get("account_id"):
        account_id = resolve_account_id(tool_input["account_id"], user_token)
        if account_id:
            params["account_id"] = account_id

    data = api_get("/api/v1/analytics/budget", params, user_token)

    return {
        "income": data.get("income", 0),
        "expenses": data.get("expenses", 0),
        "savings": data.get("savings", 0),
        "savings_rate_pct": data.get("savings_rate", 0),
        "category_breakdown": data.get("breakdown", {}),
        "comparison": data.get("comparison", {})
    }


def handle_get_account_balances(tool_input: dict, user_token: str = None) -> dict:
    """Handler untuk get_account_balances tool."""
    params = {}

    if tool_input.get("account_id"):
        account_id = resolve_account_id(tool_input["account_id"], user_token)
        if account_id:
            params["account_id"] = account_id

    data = api_get("/api/v1/accounts/balances", params, user_token)

    accounts = data.get("accounts", [])
    total = data.get("total", 0)

    return {
        "accounts": [
            {
                "id": acc["id"],
                "name": acc["name"],
                "type": acc.get("type", "savings"),
                "balance": acc["balance"],
                "is_primary": acc.get("is_primary", False)
            }
            for acc in accounts
        ],
        "total_balance": total,
        "account_count": len(accounts),
        "primary_account": next((acc for acc in accounts if acc.get("is_primary")), None)
    }


def handle_simulate_investment(tool_input: dict, user_token: str = None) -> dict:
    """Handler untuk simulate_investment tool."""
    params = {
        "monthly_amount": tool_input["monthly_amount"],
        "annual_return_pct": tool_input["annual_return_pct"],
        "years": tool_input["years"]
    }

    data = api_get("/api/v1/simulate/investment", params, user_token)

    return {
        "future_value": data.get("future_value", 0),
        "total_invested": data.get("total_invested", 0),
        "profit": data.get("profit", 0),
        "roi_pct": round(data.get("roi_pct", 0), 1),
        "yearly_breakdown": data.get("yearly_breakdown", [])
    }


def handle_get_goals(tool_input: dict, user_token: str = None) -> dict:
    """Handler untuk get_goals tool."""
    if tool_input.get("goal_id"):
        data = api_get(f"/api/v1/goals/{tool_input['goal_id']}", user_token=user_token)
        goals = [data] if data and not data.get("error") else []
    else:
        data = api_get("/api/v1/goals", user_token=user_token)
        goals = data if isinstance(data, list) else []

    return {
        "goals": [
            {
                "id": g["id"],
                "name": g["name"],
                "target_amount": g["target_amount"],
                "current_amount": g["current_amount"],
                "monthly_contribution": g["monthly_contribution"],
                "progress_pct": g.get("progress_pct", 0),
                "eta_months": g.get("eta_months", 0),
                "eta_date": g.get("eta_date", ""),
                "target_date": g.get("target_date", "")
            }
            for g in goals
        ],
        "total_goals": len(goals),
        "completed_goals": len([g for g in goals if g.get("progress_pct", 0) >= 100])
    }


def handle_categorize_transaction(tool_input: dict, user_token: str = None) -> dict:
    """Handler untuk categorize_transaction tool (local logic, no API call)."""
    merchant = tool_input["merchant"].lower()
    amount = tool_input.get("amount", 0)

    # Keyword matching logic
    keyword_map = {
        "income": ["gaji", "salary", "transfer masuk", "bonus"],
        "transport": ["grab", "gojek", "ojek", "taxi", "parkir", "transjakarta", "mrt", "krl", "bus"],
        "entertainment": ["netflix", "spotify", "youtube", "steam", "game", "cgv", "xxi", "cinema", "bioskop"],
        "bills": ["pln", "listrik", "pdam", "air", "internet", "wifi", "bpjs", "telkom", "indihome"],
        "shopping": ["indomaret", "alfamart", "supermarket", "mall", "tokopedia", "shopee", "lazada", "blibli"],
        "health": ["apotek", "klinik", "dokter", "rumah sakit", "obat", "medis", "k24", "kimia farma"],
        "food_beverage": ["warung", "makan", "resto", "restaurant", "cafe", "kopi", "mcd", "mcdonalds", "gofood", "grab food", "starbucks", "coffee"],
        "investment": ["investasi", "saham", "reksa", "tabungan", "transfer tabungan"]
    }

    category_id_map = {
        "food_beverage": 1, "transport": 2, "entertainment": 3,
        "bills": 4, "shopping": 5, "health": 6,
        "investment": 7, "other": 8, "income": 9
    }

    # Check keyword matches
    for category, keywords in keyword_map.items():
        if any(kw in merchant for kw in keywords):
            return {
                "merchant": tool_input["merchant"],
                "amount": amount,
                "suggested_category": category,
                "category_id": category_id_map[category],
                "confidence_score": 85,
                "confidence_level": "High"
            }

    # Default ke other
    return {
        "merchant": tool_input["merchant"],
        "amount": amount,
        "suggested_category": "other",
        "category_id": 8,
        "confidence_score": 50,
        "confidence_level": "Medium"
    }


def handle_detect_anomaly(tool_input: dict, user_token: str = None) -> dict:
    """Handler untuk detect_anomaly tool."""
    params = {"period": tool_input.get("period", "month")}

    if tool_input.get("account_id"):
        account_id = resolve_account_id(tool_input["account_id"], user_token)
        if account_id:
            params["account_id"] = account_id

    data = api_get("/api/v1/analytics/anomalies", params, user_token)
    anomalies = data.get("anomalies", [])

    return {
        "anomalies": anomalies,
        "period": params["period"],
        "account_id": tool_input.get("account_id") or "all",
        "total_checked": data.get("total_checked", 0),
        "anomalies_found": len(anomalies)
    }


def handle_compare_spending(tool_input: dict, user_token: str = None) -> dict:
    """Handler untuk compare_spending tool."""
    params = {}

    if tool_input.get("account_id"):
        account_id = resolve_account_id(tool_input["account_id"], user_token)
        if account_id:
            params["account_id"] = account_id

    data = api_get("/api/v1/analytics/compare", params, user_token)
    comparison = data.get("comparison", [])

    # Sort by absolute delta
    sorted_comparison = sorted(
        comparison,
        key=lambda x: abs(x.get("delta_pct", 0)),
        reverse=True
    )

    return {
        "categories": sorted_comparison,
        "this_month_total": data.get("this_month_total", 0),
        "last_month_total": data.get("last_month_total", 0),
        "total_change_pct": data.get("total_change_pct", 0),
        "highest_increase": next(
            (c for c in sorted_comparison if c.get("trend") == "up"), None
        ),
        "highest_decrease": next(
            (c for c in sorted_comparison if c.get("trend") == "down"), None
        )
    }


def handle_get_recurring_transactions(tool_input: dict, user_token: str = None) -> dict:
    """Handler untuk get_recurring_transactions tool."""
    params = {}

    if tool_input.get("account_id"):
        account_id = resolve_account_id(tool_input["account_id"], user_token)
        if account_id:
            params["account_id"] = account_id

    data = api_get("/api/v1/analytics/recurring", params, user_token)
    items = data.get("items", [])

    return {
        "subscriptions": items,
        "total_monthly": data.get("total_monthly", 0),
        "subscription_count": len(items),
        "account_id": tool_input.get("account_id") or "all"
    }


def handle_suggest_savings(tool_input: dict, user_token: str = None) -> dict:
    """Handler untuk suggest_savings tool."""
    params = {}
    if tool_input.get("target_savings"):
        params["target_savings"] = tool_input["target_savings"]

    data = api_get("/api/v1/analytics/savings-suggestion", params, user_token)

    return {
        "suggestions": data.get("suggestions", [])[:5],
        "total_potential_saving": data.get("total_potential_saving", 0),
        "impact_on_goals": data.get("impact_on_goals", "")
    }


def handle_calculate_goal_recommendation(tool_input: dict, user_token: str = None) -> dict:
    """Handler untuk calculate_goal_recommendation tool."""
    params = {"goal_id": tool_input["goal_id"]}

    if tool_input.get("target_months"):
        params["target_months"] = tool_input["target_months"]
    if tool_input.get("new_monthly_contribution"):
        params["new_monthly_contribution"] = tool_input["new_monthly_contribution"]

    data = api_get("/api/v1/analytics/goal-recommendation", params, user_token)

    return {
        "goal_id": tool_input["goal_id"],
        "goal_name": data.get("goal_name"),
        "remaining_amount": data.get("remaining_amount", 0),
        "current_contribution": data.get("current_contribution", 0),
        "current_eta_months": data.get("current_eta_months", 0),
        "current_eta_date": data.get("current_eta_date"),
        "scenarios": data.get("scenarios", [])
    }


# ============================================
# EXECUTE TOOL
# ============================================

def execute_tool(tool_name: str, tool_input: dict, user_token: str = None) -> dict:
    """
    Execute tool dengan user_token.

    Args:
        tool_name: Nama tool yang akan diexecute
        tool_input: Parameter untuk tool
        user_token: JWT token dari user untuk API calls

    Returns:
        Dict result dari tool execution
    """
    tool_map = {
        "get_transactions": handle_get_transactions,
        "calculate_budget": handle_calculate_budget,
        "get_account_balances": handle_get_account_balances,
        "simulate_investment": handle_simulate_investment,
        "get_goals": handle_get_goals,
        "categorize_transaction": handle_categorize_transaction,
        "detect_anomaly": handle_detect_anomaly,
        "compare_spending": handle_compare_spending,
        "get_recurring_transactions": handle_get_recurring_transactions,
        "suggest_savings": handle_suggest_savings,
        "calculate_goal_recommendation": handle_calculate_goal_recommendation,
    }

    handler = tool_map.get(tool_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name}"}

    try:
        return handler(tool_input, user_token=user_token)
    except Exception as e:
        return {"error": str(e)}


# ============================================
# TOOL DEFINITIONS (unchanged - for LLM function calling)
# ============================================

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_transactions",
            "description": "Ambil histori transaksi user. Bisa filter by periode, kategori, akun, atau merchant.",
            "parameters": {
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
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_budget",
            "description": "Hitung ringkasan budget: total pemasukan, pengeluaran, savings rate, breakdown per kategori.",
            "parameters": {
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
    },
    {
        "type": "function",
        "function": {
            "name": "get_account_balances",
            "description": "Ambil saldo semua akun atau akun tertentu.",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "ID akun tertentu (optional). Kalau kosong, return semua akun."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "simulate_investment",
            "description": "Simulasi pertumbuhan investasi dengan compound interest.",
            "parameters": {
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
    },
    {
        "type": "function",
        "function": {
            "name": "get_goals",
            "description": "Ambil semua financial goals user beserta progress-nya.",
            "parameters": {
                "type": "object",
                "properties": {
                    "goal_id": {
                        "type": "string",
                        "description": "ID goal tertentu (optional). Kalau kosong, return semua goals."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "categorize_transaction",
            "description": "Kategorisasi otomatis sebuah transaksi berdasarkan nama merchant.",
            "parameters": {
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
    },
    {
        "type": "function",
        "function": {
            "name": "detect_anomaly",
            "description": "Deteksi transaksi yang unusual berdasarkan pola historis user. Flagging nominal jauh di atas rata-rata, merchant baru yang belum pernah muncul, atau transaksi duplikat mencurigakan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "enum": ["week", "month"]
                    },
                    "account_id": {
                        "type": "string",
                        "description": "Filter by akun tertentu (optional)"
                    }
                },
                "required": ["period"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compare_spending",
            "description": "Bandingkan pengeluaran bulan ini vs bulan lalu, breakdown per kategori dengan persentase perubahan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "Filter by akun tertentu (optional)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_recurring_transactions",
            "description": "Ambil semua transaksi recurring (langganan bulanan) yang terdeteksi dari histori. Tampilkan total biaya dan estimasi renewal berikutnya.",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "Filter by akun tertentu (optional)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "suggest_savings",
            "description": "Analisis pola pengeluaran dan suggest kategori mana yang bisa dihemat, berapa potensi penghematan, dan dampaknya ke goals.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_savings": {
                        "type": "number",
                        "description": "Target tambahan tabungan per bulan yang ingin dicapai (optional). Kalau tidak diisi, agent yang suggest angkanya."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_goal_recommendation",
            "description": "Hitung berapa kontribusi bulanan yang dibutuhkan untuk mencapai goal dalam target waktu tertentu, atau kapan goal selesai kalau kontribusi dinaikkan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "goal_id": {
                        "type": "string",
                        "description": "ID goal yang ingin dihitung"
                    },
                    "target_months": {
                        "type": "integer",
                        "description": "Ingin selesai dalam berapa bulan? (optional)"
                    },
                    "new_monthly_contribution": {
                        "type": "number",
                        "description": "Simulasi kalau kontribusi dinaikkan jadi X per bulan (optional)"
                    }
                },
                "required": ["goal_id"]
            }
        }
    }
]

# ============================================
# TOOL HANDLERS MAP (for backward compatibility)
# ============================================

TOOL_HANDLERS = {
    "get_transactions": handle_get_transactions,
    "calculate_budget": handle_calculate_budget,
    "get_account_balances": handle_get_account_balances,
    "simulate_investment": handle_simulate_investment,
    "get_goals": handle_get_goals,
    "categorize_transaction": handle_categorize_transaction,
    "detect_anomaly": handle_detect_anomaly,
    "compare_spending": handle_compare_spending,
    "get_recurring_transactions": handle_get_recurring_transactions,
    "suggest_savings": handle_suggest_savings,
    "calculate_goal_recommendation": handle_calculate_goal_recommendation,
}

# Export execute_tool for use in brain.py
__all__ = [
    "execute_tool",
    "TOOL_DEFINITIONS",
    "TOOL_HANDLERS"
]
