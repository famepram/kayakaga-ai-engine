"""
Finai Agent Tools - API Version
All tool handlers using HTTP calls to kayakaga-api
"""

import requests
from typing import Dict

from .auth import api_get


# ============================================
# CACHE untuk master data
# ============================================

_accounts_cache = None
_categories_cache = None


def _get_accounts() -> list:
    """Get accounts dari API dengan cache."""
    global _accounts_cache
    if not _accounts_cache:
        data = api_get("/api/v1/accounts")
        _accounts_cache = data.get("accounts", []) if isinstance(data, dict) else data
    return _accounts_cache or []


def _get_categories() -> list:
    """Get categories dari API dengan cache."""
    global _categories_cache
    if not _categories_cache:
        data = api_get("/api/v1/masters/categories")
        _categories_cache = data if isinstance(data, list) else []
    return _categories_cache or []


def resolve_account_id(account_ref) -> int | None:
    """
    Resolve nama akun atau ID ke account_id integer.

    Args:
        account_ref: Account ID (int) atau nama (string)

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
    accounts = _get_accounts()
    for acc in accounts:
        if acc["name"].lower() == str(account_ref).lower():
            return acc["id"]

    return None


def resolve_category_id(category_ref) -> int | None:
    """
    Resolve nama kategori atau code ke category_id.

    Args:
        category_ref: Category ID (int) atau nama/code (string)

    Returns:
        Integer category_id atau None
    """
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


# ============================================
# TOOL HANDLERS (API Calls)
# ============================================

def handle_get_transactions(tool_input: dict) -> dict:
    """
    Handler untuk get_transactions tool.
    Ambil histori transaksi dari API.
    """
    params = {"period": tool_input.get("period", "month")}

    if tool_input.get("account_id"):
        # Support nama akun (BCA, GoPay) atau ID
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
        "net": summary.get("net", 0),
        "count": summary.get("count", 0)
    }


def handle_calculate_budget(tool_input: dict) -> dict:
    """
    Handler untuk calculate_budget tool.
    Hitung ringkasan budget dari API.
    """
    params = {"period": tool_input.get("period", "month")}

    if tool_input.get("account_id"):
        account_id = resolve_account_id(tool_input["account_id"])
        if account_id:
            params["account_id"] = account_id

    data = api_get("/api/v1/analytics/budget", params)

    return {
        "income": data.get("income", 0),
        "expenses": data.get("expenses", 0),
        "savings": data.get("savings", 0),
        "savings_rate_pct": data.get("savings_rate", 0),
        "category_breakdown": data.get("breakdown", {}),
        "comparison": data.get("comparison", {})
    }


def handle_get_account_balances(tool_input: dict) -> dict:
    """
    Handler untuk get_account_balances tool.
    Ambil saldo akun dari API.
    """
    params = {}

    if tool_input.get("account_id"):
        account_id = resolve_account_id(tool_input["account_id"])
        if account_id:
            params["account_id"] = account_id

    data = api_get("/api/v1/accounts/balances", params)

    accounts = data.get("accounts", [])
    total = data.get("total", 0)

    # Enrich dengan info tambahan
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


def handle_simulate_investment(tool_input: dict) -> dict:
    """
    Handler untuk simulate_investment tool.
    Simulasi investasi via API.
    """
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
        "yearly_breakdown": data.get("yearly_breakdown", [])
    }


def handle_get_goals(tool_input: dict) -> dict:
    """
    Handler untuk get_goals tool.
    Ambil goals dari API.
    """
    if tool_input.get("goal_id"):
        data = api_get(f"/api/v1/goals/{tool_input['goal_id']}")
        goals = [data] if data and not data.get("error") else []
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


def handle_categorize_transaction(tool_input: dict) -> dict:
    """
    Handler untuk categorize_transaction tool.
    Logic lokal tanpa API call.
    """
    merchant = tool_input["merchant"].lower()
    amount = tool_input.get("amount", 0)

    # Keyword matching logic
    keyword_map = {
        "income": ["gaji", "salary", "transfer masuk", "bonus"],
        "transport": ["grab", "gojek", "ojek", "taxi", "parkir", "transjakarta", "mrt", "krl", "bus"],
        "entertainment": ["netflix", "spotify", "youtube", "steam", "game", "cgv", "cgv", "xxi", "cinema", "bioskop"],
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

    # Default ke other jika tidak ada match
    return {
        "merchant": tool_input["merchant"],
        "amount": amount,
        "suggested_category": "other",
        "category_id": 8,
        "confidence_score": 50,
        "confidence_level": "Medium"
    }


def handle_detect_anomaly(tool_input: dict) -> dict:
    """
    Handler untuk detect_anomaly tool.
    Deteksi anomali dari API.
    """
    params = {"period": tool_input.get("period", "month")}

    if tool_input.get("account_id"):
        account_id = resolve_account_id(tool_input["account_id"])
        if account_id:
            params["account_id"] = account_id

    data = api_get("/api/v1/analytics/anomalies", params)
    anomalies = data.get("anomalies", [])

    return {
        "anomalies": anomalies,
        "period": params["period"],
        "account_id": tool_input.get("account_id") or "all",
        "total_checked": data.get("total_checked", 0),
        "anomalies_found": len(anomalies)
    }


def handle_compare_spending(tool_input: dict) -> dict:
    """
    Handler untuk compare_spending tool.
    Bandingkan spending dari API.
    """
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


def handle_get_recurring_transactions(tool_input: dict) -> dict:
    """
    Handler untuk get_recurring_transactions tool.
    Ambil langganan dari API.
    """
    params = {}

    if tool_input.get("account_id"):
        account_id = resolve_account_id(tool_input["account_id"])
        if account_id:
            params["account_id"] = account_id

    data = api_get("/api/v1/analytics/recurring", params)
    items = data.get("items", [])

    return {
        "subscriptions": items,
        "total_monthly": data.get("total_monthly", 0),
        "subscription_count": len(items),
        "account_id": tool_input.get("account_id") or "all"
    }


def handle_suggest_savings(tool_input: dict) -> dict:
    """
    Handler untuk suggest_savings tool.
    Saran hemat dari API.
    """
    params = {}
    if tool_input.get("target_savings"):
        params["target_savings"] = tool_input["target_savings"]

    data = api_get("/api/v1/analytics/savings-suggestion", params)

    return {
        "suggestions": data.get("suggestions", [])[:5],  # Top 5
        "total_potential_saving": data.get("total_potential_saving", 0),
        "impact_on_goals": data.get("impact_on_goals", "")
    }


def handle_calculate_goal_recommendation(tool_input: dict) -> dict:
    """
    Handler untuk calculate_goal_recommendation tool.
    Hitung goal scenarios dari API.
    """
    params = {"goal_id": tool_input["goal_id"]}

    if tool_input.get("target_months"):
        params["target_months"] = tool_input["target_months"]
    if tool_input.get("new_monthly_contribution"):
        params["new_monthly_contribution"] = tool_input["new_monthly_contribution"]

    data = api_get("/api/v1/analytics/goal-recommendation", params)

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
                        "enum": ["week", "month"],
                        "description": "Periode yang ingin dicek anomalinya"
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


# Tool handler mapping
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
    "calculate_goal_recommendation": handle_calculate_goal_recommendation
}
