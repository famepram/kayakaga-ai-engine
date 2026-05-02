"""
Finai Agent Tools
All tool definitions and handlers for the Finai personal finance advisor agent
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional


# ============================================
# DATA LOADING UTILITIES
# ============================================

def _load_json(filename: str) -> dict:
    """Load JSON file from data directory"""
    filepath = os.path.join(os.path.dirname(__file__), f"../data/{filename}")
    if not os.path.exists(filepath):
        return {}
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_json(filename: str, data: dict) -> None:
    """Save JSON file to data directory"""
    filepath = os.path.join(os.path.dirname(__file__), f"../data/{filename}")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _resolve_account_id(account_input: str) -> str:
    """
    Resolve account input to account ID.
    Matches by ID directly OR by name (case-insensitive).

    Args:
        account_input: Account ID (acc_bca) or name (BCA, gopay, etc.)

    Returns:
        Account ID if found, otherwise returns original input
    """
    if not account_input:
        return None

    # Load accounts
    accounts = _load_json("accounts.json")
    if not isinstance(accounts, list):
        return account_input

    # First try exact ID match
    for acc in accounts:
        if acc.get("id") == account_input:
            return account_input

    # Then try case-insensitive name match
    account_input_lower = account_input.lower()
    for acc in accounts:
        name = acc.get("name", "").lower()
        if name == account_input_lower or account_input_lower in name:
            return acc.get("id")

    # Return original if no match
    return account_input


# ============================================
# TOOL 1: GET_TRANSACTIONS
# ============================================

def get_transactions(period: str = "month", category: str = None,
                     account_id: str = None, merchant: str = None) -> Dict:
    """
    Ambil histori transaksi user. Bisa filter by periode, kategori, akun, atau merchant.

    Args:
        period: Periode transaksi (today, week, month, last_month, year)
        category: Filter by kategori (optional)
        account_id: Filter by akun tertentu (optional)
        merchant: Filter by nama merchant (optional, case-insensitive partial match)

    Returns:
        Dict dengan list transaksi + summary (total in, total out, count)
    """
    try:
        transactions = _load_json("transactions.json")
        if not isinstance(transactions, list):
            transactions = []

        # Filter by period
        today = datetime.now()
        filtered = []

        for tx in transactions:
            tx_date = datetime.strptime(tx.get("date", "2026-01-01"), "%Y-%m-%d")

            if period == "today":
                if tx_date.date() == today.date():
                    filtered.append(tx)
            elif period == "week":
                week_ago = today - timedelta(days=7)
                if tx_date >= week_ago:
                    filtered.append(tx)
            elif period == "month":
                if tx_date.month == today.month and tx_date.year == today.year:
                    filtered.append(tx)
            elif period == "last_month":
                last_month = today.replace(day=1) - timedelta(days=1)
                if tx_date.month == last_month.month and tx_date.year == last_month.year:
                    filtered.append(tx)
            elif period == "year":
                if tx_date.year == today.year:
                    filtered.append(tx)
            else:
                # Default to all transactions
                filtered.append(tx)

        # Filter by category
        if category:
            filtered = [tx for tx in filtered if tx.get("category") == category]

        # Filter by account_id (supports both ID and name)
        if account_id:
            resolved_id = _resolve_account_id(account_id)
            filtered = [tx for tx in filtered if tx.get("account_id") == resolved_id]

        # Filter by merchant (case-insensitive partial match)
        if merchant:
            filtered = [tx for tx in filtered
                       if merchant.lower() in tx.get("merchant", "").lower()]

        # Calculate summary
        total_in = sum(tx.get("amount", 0) for tx in filtered if tx.get("amount", 0) > 0)
        total_out = sum(abs(tx.get("amount", 0)) for tx in filtered if tx.get("amount", 0) < 0)

        return {
            "transactions": filtered,
            "total_in": total_in,
            "total_out": total_out,
            "net": total_in - total_out,
            "count": len(filtered),
            "period": period
        }

    except Exception as e:
        return {
            "error": str(e),
            "transactions": [],
            "total_in": 0,
            "total_out": 0,
            "net": 0,
            "count": 0
        }


# ============================================
# TOOL 2: CALCULATE_BUDGET
# ============================================

def calculate_budget(period: str = "month", account_id: str = None) -> Dict:
    """
    Hitung ringkasan budget: total pemasukan, pengeluaran, savings rate, breakdown per kategori.

    Args:
        period: Periode (month, last_month, year)
        account_id: Filter by akun (optional)

    Returns:
        Dict dengan budget summary + breakdown per kategori + vs previous period comparison
    """
    try:
        # Get current period data
        current_data = get_transactions(period=period, account_id=account_id)

        # Get previous period for comparison
        prev_period = "last_month" if period == "month" else "month"
        previous_data = get_transactions(period=prev_period, account_id=account_id)

        # Calculate category breakdown
        category_breakdown = {}
        for tx in current_data["transactions"]:
            category = tx.get("category", "other")
            amount = abs(tx.get("amount", 0))
            if tx.get("amount", 0) < 0:  # Only expenses
                category_breakdown[category] = category_breakdown.get(category, 0) + amount

        # Calculate savings rate
        income = current_data["total_in"]
        expenses = current_data["total_out"]
        savings_rate = ((income - expenses) / income * 100) if income > 0 else 0

        # Calculate change vs previous period
        prev_expenses = previous_data["total_out"]
        expense_change = ((expenses - prev_expenses) / prev_expenses * 100) if prev_expenses > 0 else 0

        return {
            "income": income,
            "expenses": expenses,
            "savings": income - expenses,
            "savings_rate_pct": round(savings_rate, 2),
            "category_breakdown": category_breakdown,
            "comparison": {
                "previous_expenses": prev_expenses,
                "expense_change_pct": round(expense_change, 2)
            },
            "period": period,
            "account_id": account_id or "all"
        }

    except Exception as e:
        return {
            "error": str(e),
            "income": 0,
            "expenses": 0,
            "savings": 0,
            "savings_rate_pct": 0,
            "category_breakdown": {},
            "comparison": {}
        }


# ============================================
# TOOL 3: GET_ACCOUNT_BALANCES
# ============================================

def get_account_balances(account_id: str = None) -> Dict:
    """
    Ambil saldo semua akun atau akun tertentu.

    Args:
        account_id: ID akun tertentu (optional). Kalau kosong, return semua akun.

    Returns:
        Dict dengan saldo akun-akun + total gabungan
    """
    try:
        accounts = _load_json("accounts.json")
        if not isinstance(accounts, list):
            accounts = []

        # Filter by account_id if specified (supports both ID and name)
        if account_id:
            resolved_id = _resolve_account_id(account_id)
            accounts = [acc for acc in accounts if acc.get("id") == resolved_id]

        # Calculate total
        total_balance = sum(acc.get("balance", 0) for acc in accounts)

        # Format accounts info
        accounts_info = []
        for acc in accounts:
            accounts_info.append({
                "id": acc.get("id"),
                "name": acc.get("name"),
                "type": acc.get("type"),
                "balance": acc.get("balance", 0),
                "is_primary": acc.get("is_primary", False),
                "color": acc.get("color", "#000000")
            })

        return {
            "accounts": accounts_info,
            "total_balance": total_balance,
            "account_count": len(accounts_info),
            "primary_account": next((acc for acc in accounts_info if acc.get("is_primary")), None)
        }

    except Exception as e:
        return {
            "error": str(e),
            "accounts": [],
            "total_balance": 0,
            "account_count": 0
        }


# ============================================
# TOOL 4: SIMULATE_INVESTMENT
# ============================================

def simulate_investment(monthly_amount: float, annual_return_pct: float,
                        years: int) -> Dict:
    """
    Simulasi pertumbuhan investasi dengan compound interest.

    Args:
        monthly_amount: Jumlah investasi per bulan dalam IDR
        annual_return_pct: Return tahunan dalam persen (contoh: 10 untuk 10%)
        years: Durasi investasi dalam tahun

    Returns:
        Dict dengan future_value, total_invested, profit, monthly breakdown
    """
    try:
        monthly_rate = (annual_return_pct / 100) / 12
        months = years * 12

        # Compound interest calculation
        future_value = 0
        monthly_breakdown = []

        for month in range(1, months + 1):
            future_value = (future_value + monthly_amount) * (1 + monthly_rate)

            # Add to breakdown every year
            if month % 12 == 0:
                monthly_breakdown.append({
                    "year": month // 12,
                    "month": month,
                    "value": round(future_value, 2)
                })

        total_invested = monthly_amount * months
        profit = future_value - total_invested

        return {
            "monthly_amount": monthly_amount,
            "annual_return_pct": annual_return_pct,
            "years": years,
            "future_value": round(future_value, 2),
            "total_invested": round(total_invested, 2),
            "profit": round(profit, 2),
            "roi_pct": round((profit / total_invested) * 100, 2) if total_invested > 0 else 0,
            "yearly_breakdown": monthly_breakdown
        }

    except Exception as e:
        return {
            "error": str(e),
            "future_value": 0,
            "total_invested": 0,
            "profit": 0
        }


# ============================================
# TOOL 5: GET_GOALS
# ============================================

def get_goals(goal_id: str = None) -> Dict:
    """
    Ambil semua financial goals user beserta progress-nya.

    Args:
        goal_id: ID goal tertentu (optional). Kalau kosong, return semua goals.

    Returns:
        Dict dengan semua goals + progress % + ETA berdasarkan monthly_contribution saat ini
    """
    try:
        goals = _load_json("goals.json")
        if not isinstance(goals, list):
            goals = []

        # Filter by goal_id if specified
        if goal_id:
            goals = [goal for goal in goals if goal.get("id") == goal_id]

        goals_info = []
        for goal in goals:
            target = goal.get("target_amount", 0)
            current = goal.get("current_amount", 0)
            monthly_contrib = goal.get("monthly_contribution", 0)
            target_date = goal.get("target_date", "")

            # Calculate progress percentage
            progress_pct = (current / target * 100) if target > 0 else 0

            # Calculate remaining amount
            remaining = target - current

            # Calculate ETA based on monthly contribution
            months_remaining = (remaining / monthly_contrib) if monthly_contrib > 0 else 0
            eta_years = int(months_remaining // 12)
            eta_months = int(months_remaining % 12)

            # Calculate if on track
            if target_date:
                target_dt = datetime.strptime(target_date, "%Y-%m-%d")
                months_until_target = max(0, (target_dt.year - datetime.now().year) * 12 +
                                        (target_dt.month - datetime.now().month))
                on_track = months_remaining <= months_until_target if monthly_contrib > 0 else False
            else:
                on_track = False

            # Milestone progress
            milestones = goal.get("milestones", [])
            achieved_milestones = [m for m in milestones if current >= m]
            next_milestone = next((m for m in milestones if m > current), None)

            goals_info.append({
                "id": goal.get("id"),
                "name": goal.get("name"),
                "type": goal.get("type"),
                "current_amount": current,
                "target_amount": target,
                "progress_pct": round(progress_pct, 2),
                "remaining_amount": remaining,
                "monthly_contribution": monthly_contrib,
                "eta": f"{eta_years}y {eta_months}m" if months_remaining > 0 else "Completed",
                "on_track": on_track,
                "achieved_milestones": achieved_milestones,
                "next_milestone": next_milestone,
                "target_date": target_date
            })

        return {
            "goals": goals_info,
            "total_goals": len(goals_info),
            "completed_goals": len([g for g in goals_info if g["progress_pct"] >= 100])
        }

    except Exception as e:
        return {
            "error": str(e),
            "goals": [],
            "total_goals": 0,
            "completed_goals": 0
        }


# ============================================
# TOOL 6: CATEGORIZE_TRANSACTION
# ============================================

def categorize_transaction(merchant: str, amount: float) -> Dict:
    """
    Kategorisasi otomatis sebuah transaksi berdasarkan nama merchant.

    Args:
        merchant: Nama merchant
        amount: Nominal transaksi

    Returns:
        Dict dengan suggested category + confidence score
    """
    try:
        merchant_lower = merchant.lower()

        # Category patterns and keywords
        category_patterns = {
            "food_beverage": [
                "kopi", "makan", "nasi", "ayam", "bakso", "sate", "warteg",
                "warung", "resto", "cafe", "starbucks", "jenius", "janji",
                "geprek", "padang", "seafood", "bubble", "teh", "jus"
            ],
            "transport": [
                "gojek", "grab", "uber", "ojek", "mrt", "trans", "bus",
                "kereta", "stasiun", "terminal", "bensin", "pertamina",
                "parkir", "tol"
            ],
            "entertainment": [
                "netflix", "spotify", "youtube", "disney", "xxi", "cgv",
                "bioskop", "steam", "game", "concert", "movie"
            ],
            "bills": [
                "pln", "pdam", "air", "listrik", "internet", "wifi",
                "pulsa", "data", "bpjs", "telepon", "token"
            ],
            "shopping": [
                "tokopedia", "shopee", "lazada", "blibli", "alfamart",
                "indomaret", "supermarket", "mall", "toko", "butik",
                "zara", "uniqlo", "h&m"
            ],
            "health": [
                "rs", "klinik", "apotik", "obat", "dokter", "rumah sakit",
                "sehat", "fitness", "gym"
            ],
            "investment": [
                "saham", "reksadana", "deposito", "emas", "crypto",
                "binance", "e-wallet", "topup"
            ],
            "income": [
                "gaji", "salary", "payroll", "pt ", "cv ", "bonus",
                "terima", "transfer masuk"
            ]
        }

        # Find matching category
        best_category = "other"
        best_score = 0

        for category, patterns in category_patterns.items():
            for pattern in patterns:
                if pattern in merchant_lower:
                    # More specific matches get higher scores
                    score = len(pattern) / len(merchant_lower)
                    if score > best_score:
                        best_score = score
                        best_category = category

        # Calculate confidence score (0-100)
        confidence = min(100, int(best_score * 100 + 20))

        # Adjust confidence based on amount patterns
        if amount > 0:
            # Income is usually positive and larger
            if best_category != "income" and amount > 1000000:
                confidence = max(30, confidence - 30)
                best_category = "income"
        else:
            # Expense should be negative
            amount_abs = abs(amount)
            if best_category == "income":
                confidence = 30
                best_category = "other"

            # Large amounts might be shopping or bills
            if amount_abs > 500000 and best_category in ["food_beverage", "transport"]:
                confidence = max(40, confidence - 20)
                best_category = "shopping"

        return {
            "merchant": merchant,
            "amount": amount,
            "suggested_category": best_category,
            "confidence_score": confidence,
            "confidence_level": "High" if confidence >= 70 else "Medium" if confidence >= 50 else "Low"
        }

    except Exception as e:
        return {
            "error": str(e),
            "merchant": merchant,
            "amount": amount,
            "suggested_category": "other",
            "confidence_score": 0,
            "confidence_level": "Low"
        }


# ============================================
# TOOL 7: DETECT_ANOMALY
# ============================================

def detect_anomaly(period: str = "month", account_id: str = None) -> Dict:
    """
    Deteksi transaksi yang unusual berdasarkan pola historis user.

    Args:
        period: Periode yang ingin dicek anomalinya (week, month)
        account_id: Filter by akun tertentu (optional)

    Returns:
        Dict dengan list anomali + severity level
    """
    try:
        # Get transactions for period
        tx_data = get_transactions(period=period, account_id=account_id)
        transactions = tx_data.get("transactions", [])

        if not transactions:
            return {
                "anomalies": [],
                "period": period,
                "account_id": account_id or "all",
                "total_checked": 0
            }

        # Get historical data for baseline (3x period)
        all_tx = _load_json("transactions.json")
        if not isinstance(all_tx, list):
            all_tx = []

        # Calculate category averages from history
        category_stats = {}
        for tx in all_tx:
            cat = tx.get("category", "other")
            amount = abs(tx.get("amount", 0))
            if amount > 0:  # Only expenses
                if cat not in category_stats:
                    category_stats[cat] = {"total": 0, "count": 0}
                category_stats[cat]["total"] += amount
                category_stats[cat]["count"] += 1

        # Calculate averages
        category_avg = {}
        for cat, stats in category_stats.items():
            if stats["count"] > 0:
                category_avg[cat] = stats["total"] / stats["count"]

        # Detect anomalies
        anomalies = []
        merchants_seen = {}

        for tx in transactions:
            amount = abs(tx.get("amount", 0))
            merchant = tx.get("merchant", "")
            category = tx.get("category", "other")

            # Skip income transactions
            if tx.get("amount", 0) > 0:
                continue

            reason = None
            severity = "low"

            # Check 1: Amount > 2x category average
            if category in category_avg:
                avg = category_avg[category]
                if amount > avg * 2:
                    ratio = int(amount / avg)
                    reason = f"Nominal {ratio}x lebih besar dari rata-rata kategori {category}"
                    severity = "high" if ratio >= 3 else "medium"

            # Check 2: New merchant > 100K
            if merchant not in merchants_seen and amount > 100000:
                # Check if merchant exists in historical transactions
                merchant_in_history = any(tx.get("merchant", "") == merchant for tx in all_tx)
                is_new = not merchant_in_history
                if is_new:
                    if reason:
                        reason += f"; Merchant baru dengan nominal besar"
                    else:
                        reason = "Merchant baru dengan nominal besar"
                    severity = "medium" if severity == "low" else severity

            # Check 3: Duplicate transactions (same merchant + amount within 24h)
            tx_date = datetime.strptime(tx.get("date", "2026-01-01"), "%Y-%m-%d")
            for other_tx in transactions:
                if (tx.get("id") != other_tx.get("id") and
                    merchant == other_tx.get("merchant") and
                    amount == abs(other_tx.get("amount", 0))):

                    other_date = datetime.strptime(other_tx.get("date", "2026-01-01"), "%Y-%m-%d")
                    diff = abs((tx_date - other_date).days)

                    if diff <= 1:
                        if reason:
                            reason += f"; Transaksi duplikat dalam 24 jam"
                        else:
                            reason = "Transaksi duplikat dalam 24 jam"
                        severity = "high"
                        break

            if reason:
                anomalies.append({
                    "transaction_id": tx.get("id"),
                    "merchant": merchant,
                    "amount": amount,
                    "category": category,
                    "date": tx.get("date"),
                    "reason": reason,
                    "severity": severity
                })

            merchants_seen[merchant] = merchants_seen.get(merchant, 0) + 1

        return {
            "anomalies": anomalies,
            "period": period,
            "account_id": account_id or "all",
            "total_checked": len(transactions),
            "anomalies_found": len(anomalies)
        }

    except Exception as e:
        return {
            "error": str(e),
            "anomalies": [],
            "total_checked": 0,
            "anomalies_found": 0
        }


# ============================================
# TOOL 8: COMPARE_SPENDING
# ============================================

def compare_spending(account_id: str = None) -> Dict:
    """
    Bandingkan pengeluaran bulan ini vs bulan lalu, breakdown per kategori.

    Args:
        account_id: Filter by akun tertentu (optional)

    Returns:
        Dict dengan perbandingan per kategori + summary
    """
    try:
        # Get this month and last month data
        this_month_data = get_transactions(period="month", account_id=account_id)
        last_month_data = get_transactions(period="last_month", account_id=account_id)

        # Calculate per category
        this_month_cat = {}
        for tx in this_month_data["transactions"]:
            cat = tx.get("category", "other")
            amount = abs(tx.get("amount", 0))
            if tx.get("amount", 0) < 0:  # Only expenses
                this_month_cat[cat] = this_month_cat.get(cat, 0) + amount

        last_month_cat = {}
        for tx in last_month_data["transactions"]:
            cat = tx.get("category", "other")
            amount = abs(tx.get("amount", 0))
            if tx.get("amount", 0) < 0:  # Only expenses
                last_month_cat[cat] = last_month_cat.get(cat, 0) + amount

        # Get all categories
        all_categories = set(list(this_month_cat.keys()) + list(last_month_cat.keys()))

        # Calculate comparison
        comparisons = []
        for cat in sorted(all_categories):
            this_val = this_month_cat.get(cat, 0)
            last_val = last_month_cat.get(cat, 0)

            # Calculate trend and delta
            if last_val == 0:
                if this_val > 0:
                    trend = "new"
                    delta_pct = 100
                else:
                    trend = "gone"
                    delta_pct = -100
            else:
                delta = this_val - last_val
                delta_pct = (delta / last_val) * 100
                trend = "up" if delta_pct > 0 else "down"

            comparisons.append({
                "category": cat,
                "this_month": this_val,
                "last_month": last_val,
                "delta_pct": round(delta_pct, 1),
                "trend": trend
            })

        # Find biggest changes
        increases = [c for c in comparisons if c["trend"] == "up"]
        decreases = [c for c in comparisons if c["trend"] == "down"]

        highest_increase = max(increases, key=lambda x: x["delta_pct"]) if increases else None
        highest_decrease = max(decreases, key=lambda x: x["delta_pct"]) if decreases else None

        return {
            "categories": comparisons,
            "this_month_total": this_month_data["total_out"],
            "last_month_total": last_month_data["total_out"],
            "total_change_pct": round(
                ((this_month_data["total_out"] - last_month_data["total_out"]) /
                 last_month_data["total_out"]) * 100, 1
            ) if last_month_data["total_out"] > 0 else 0,
            "highest_increase": highest_increase,
            "highest_decrease": highest_decrease,
            "account_id": account_id or "all"
        }

    except Exception as e:
        return {
            "error": str(e),
            "categories": []
        }


# ============================================
# TOOL 9: GET_RECURRING_TRANSACTIONS
# ============================================

def get_recurring_transactions(account_id: str = None) -> Dict:
    """
    Ambil semua transaksi recurring (langganan bulanan).

    Args:
        account_id: Filter by akun tertentu (optional)

    Returns:
        Dict dengan list langganan + total biaya per bulan
    """
    try:
        transactions = _load_json("transactions.json")
        if not isinstance(transactions, list):
            transactions = []

        # Filter recurring and by account
        recurring = []
        for tx in transactions:
            if not tx.get("is_recurring", False):
                continue

            if account_id and tx.get("account_id") != _resolve_account_id(account_id):
                continue

            # Only expenses (negative amounts)
            if tx.get("amount", 0) >= 0:
                continue

            recurring.append(tx)

        # Group by merchant
        subscriptions = {}
        for tx in recurring:
            merchant = tx.get("merchant", "")
            if not merchant:
                continue

            if merchant not in subscriptions:
                subscriptions[merchant] = {
                    "merchant": merchant,
                    "amount": abs(tx.get("amount", 0)),
                    "account_id": tx.get("account_id"),
                    "category": tx.get("category", "other"),
                    "occurrences": 0,
                    "last_charged": tx.get("date", "")
                }

            subscriptions[merchant]["occurrences"] += 1

            # Update last charged date
            tx_date = tx.get("date", "")
            if tx_date > subscriptions[merchant]["last_charged"]:
                subscriptions[merchant]["last_charged"] = tx_date

        # Calculate next renewal
        result = []
        total_monthly = 0

        for sub in subscriptions.values():
            # Calculate next renewal (last_charged + 30 days)
            try:
                last_date = datetime.strptime(sub["last_charged"], "%Y-%m-%d")
                from datetime import timedelta
                next_date = last_date + timedelta(days=30)
                sub["next_renewal"] = next_date.strftime("%Y-%m-%d")
            except:
                sub["next_renewal"] = "Unknown"

            total_monthly += sub["amount"]
            result.append(sub)

        # Sort by amount descending
        result.sort(key=lambda x: x["amount"], reverse=True)

        return {
            "subscriptions": result,
            "total_monthly": total_monthly,
            "subscription_count": len(result),
            "account_id": account_id or "all"
        }

    except Exception as e:
        return {
            "error": str(e),
            "subscriptions": [],
            "total_monthly": 0,
            "subscription_count": 0
        }


# ============================================
# TOOL 10: SUGGEST_SAVINGS
# ============================================

def suggest_savings(target_savings: int = None) -> Dict:
    """
    Analisis pola pengeluaran dan suggest kategori yang bisa dihemat.

    Args:
        target_savings: Target tambahan tabungan per bulan (optional)

    Returns:
        Dict dengan suggest kategori + potensi penghematan
    """
    try:
        # Get current and last month budget
        current_budget = calculate_budget(period="month")
        last_budget = calculate_budget(period="last_month")

        current_breakdown = current_budget.get("category_breakdown", {})
        last_breakdown = last_budget.get("category_breakdown", {})

        # Analyze each category
        suggestions = []

        # Exclude bills and income from reduction suggestions
        exclude_categories = ["bills", "income", "investment"]

        for category, current_spend in current_breakdown.items():
            if category in exclude_categories:
                continue

            last_spend = last_breakdown.get(category, 0)

            # Calculate change vs last month
            if last_spend > 0:
                change_pct = ((current_spend - last_spend) / last_spend) * 100
            else:
                change_pct = 0

            # Only suggest if category is significant (>100K)
            if current_spend < 100000:
                continue

            # Calculate potential saving (20% reduction)
            potential = int(current_spend * 0.2)
            suggested_limit = int(current_spend * 0.8)

            reasoning = ""
            if change_pct > 20:
                reasoning = f"{category.capitalize()} {int(change_pct)}% lebih tinggi dari bulan lalu"
            elif current_spend > 500000:
                reasoning = f"{category.capitalize()} pengeluaran besar ({current_spend/1000000:.1f}jt/bulan)"
            else:
                reasoning = f"{category.capitalize()} bisa dioptimalkan"

            suggestions.append({
                "category": category,
                "current_spend": current_spend,
                "suggested_limit": suggested_limit,
                "potential_saving": potential,
                "reasoning": reasoning,
                "change_pct_vs_last_month": round(change_pct, 1)
            })

        # Sort by potential saving
        suggestions.sort(key=lambda x: x["potential_saving"], reverse=True)

        # Calculate total potential
        total_potential = sum(s["potential_saving"] for s in suggestions)

        # Calculate impact on goals
        goals = _load_json("goals.json")
        impact_msg = ""

        if isinstance(goals, list) and len(goals) > 0:
            goal = goals[0]  # Use first goal
            goal_name = goal.get("name", "goal")
            remaining = goal.get("target_amount", 0) - goal.get("current_amount", 0)

            if total_potential > 0 and remaining > 0:
                months_faster = remaining / total_potential if total_potential > 0 else 0
                impact_msg = f"Dengan hemat Rp {total_potential:,}/bulan, {goal_name} bisa selesai {int(months_faster)} bulan lebih cepat"

        # If target_savings specified, find combination
        target_recommendation = None
        if target_savings and target_savings > 0:
            accumulated = 0
            selected = []

            for s in suggestions:
                if accumulated >= target_savings:
                    break
                selected.append(s)
                accumulated += s["potential_saving"]

            if accumulated >= target_savings:
                target_recommendation = {
                    "target_savings": target_savings,
                    "can_achieve": True,
                    "selected_categories": [s["category"] for s in selected],
                    "actual_potential": accumulated
                }
            else:
                target_recommendation = {
                    "target_savings": target_savings,
                    "can_achieve": False,
                    "max_potential": total_potential,
                    "shortfall": target_savings - total_potential
                }

        result = {
            "suggestions": suggestions[:5],  # Top 5
            "total_potential_saving": total_potential,
            "impact_on_goals": impact_msg
        }

        if target_recommendation:
            result["target_analysis"] = target_recommendation

        return result

    except Exception as e:
        return {
            "error": str(e),
            "suggestions": [],
            "total_potential_saving": 0
        }


# ============================================
# TOOL 11: CALCULATE_GOAL_RECOMMENDATION
# ============================================

def calculate_goal_recommendation(goal_id: str, target_months: int = None,
                                 new_monthly_contribution: int = None) -> Dict:
    """
    Hitung kontribusi bulanan yang dibutuhkan untuk mencapai goal,
    atau kapan goal selesai kalau kontribusi dinaikkan.

    Args:
        goal_id: ID goal yang ingin dihitung
        target_months: Ingin selesai dalam berapa bulan (optional)
        new_monthly_contribution: Simulasi kalau kontribusi dinaikkan (optional)

    Returns:
        Dict dengan scenarios dan recommendations
    """
    try:
        goals = _load_json("goals.json")
        if not isinstance(goals, list):
            goals = []

        # Find goal
        goal = None
        for g in goals:
            if g.get("id") == goal_id:
                goal = g
                break

        if not goal:
            return {
                "error": f"Goal dengan ID '{goal_id}' tidak ditemukan",
                "goal_id": goal_id
            }

        goal_name = goal.get("name", "Unknown")
        remaining = goal.get("target_amount", 0) - goal.get("current_amount", 0)
        current_contrib = goal.get("monthly_contribution", 0)
        target_date = goal.get("target_date", "")

        # Calculate current ETA
        current_eta_months = int(remaining / current_contrib) if current_contrib > 0 else 999

        # Calculate current ETA date
        try:
            from datetime import datetime, timedelta
            current_eta_date = (datetime.now() + timedelta(days=current_eta_months * 30)).strftime("%Y-%m-%d")
        except:
            current_eta_date = "Unknown"

        result = {
            "goal_id": goal_id,
            "goal_name": goal_name,
            "remaining_amount": remaining,
            "current_contribution": current_contrib,
            "current_eta_months": current_eta_months,
            "current_eta_date": current_eta_date
        }

        # Scenario 1: Target months specified
        if target_months and target_months > 0:
            required_monthly = int(remaining / target_months)
            result["target_months_analysis"] = {
                "target_months": target_months,
                "required_monthly_contribution": required_monthly,
                "increase_needed": required_monthly - current_contrib,
                "increase_pct": round(((required_monthly - current_contrib) / current_contrib) * 100, 1) if current_contrib > 0 else 0
            }

        # Scenario 2: New contribution specified - calculate multiple scenarios
        if new_monthly_contribution and new_monthly_contribution > 0:
            new_eta_months = int(remaining / new_monthly_contribution)
            months_faster = current_eta_months - new_eta_months

            try:
                from datetime import datetime, timedelta
                new_eta_date = (datetime.now() + timedelta(days=new_eta_months * 30)).strftime("%Y-%m-%d")
            except:
                new_eta_date = "Unknown"

            result["new_contribution_analysis"] = {
                "new_monthly_contribution": new_monthly_contribution,
                "new_eta_months": new_eta_months,
                "months_faster": months_faster,
                "new_eta_date": new_eta_date
            }

        # Scenario 3: Generate multiple scenarios (+500K, +1M, +1.5M, +2M)
        scenarios = []
        increments = [500000, 1000000, 1500000, 2000000]

        for increment in increments:
            new_contrib = current_contrib + increment
            if new_contrib <= 0:
                continue

            new_eta = int(remaining / new_contrib)
            faster = current_eta_months - new_eta

            try:
                from datetime import datetime, timedelta
                eta_date = (datetime.now() + timedelta(days=new_eta * 30)).strftime("%Y-%m-%d")
            except:
                eta_date = "Unknown"

            scenarios.append({
                "monthly_contribution": new_contrib,
                "eta_months": new_eta,
                "months_faster": faster,
                "eta_date": eta_date
            })

        result["scenarios"] = scenarios

        return result

    except Exception as e:
        return {
            "error": str(e),
            "goal_id": goal_id
        }

# ============================================
# TOOL DEFINITIONS FOR LLM FUNCTION CALLING
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
    "get_transactions": get_transactions,
    "calculate_budget": calculate_budget,
    "get_account_balances": get_account_balances,
    "simulate_investment": simulate_investment,
    "get_goals": get_goals,
    "categorize_transaction": categorize_transaction,
    "detect_anomaly": detect_anomaly,
    "compare_spending": compare_spending,
    "get_recurring_transactions": get_recurring_transactions,
    "suggest_savings": suggest_savings,
    "calculate_goal_recommendation": calculate_goal_recommendation
}