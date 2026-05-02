import json
import os
from datetime import datetime
from typing import Dict, List


DATA_FILE = os.path.join(os.path.dirname(__file__), "../../data/transactions.json")


def _load_transactions() -> List[Dict]:
    """Load transactions dari JSON file"""
    if not os.path.exists(DATA_FILE):
        return []

    with open(DATA_FILE, 'r') as f:
        return json.load(f)


def _save_transactions(transactions: List[Dict]) -> None:
    """Save transactions ke JSON file"""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

    with open(DATA_FILE, 'w') as f:
        json.dump(transactions, f, indent=2, default=str)


def get_transactions(month: int = None, year: int = None, category: str = None) -> Dict:
    """
    Ambil data transaksi, bisa filter berdasarkan bulan/tahun/kategori

    Args:
        month: Filter by bulan (1-12)
        year: Filter by tahun
        category: Filter by kategori (makanan, transport, dll)

    Returns:
        Dict dengan list transaksi dan summary
    """
    transactions = _load_transactions()

    # Filter
    filtered = transactions
    if month or year:
        filtered = [
            t for t in transactions
            if (not month or t.get('month') == month) and
               (not year or t.get('year') == year)
        ]

    if category:
        filtered = [t for t in filtered if t.get('category') == category]

    # Calculate total
    total = sum(t.get('amount', 0) for t in filtered)

    return {
        "transactions": filtered,
        "total": total,
        "count": len(filtered)
    }


def add_transaction(amount: float, category: str, description: str, date: str = None) -> Dict:
    """
    Tambah transaksi baru

    Args:
        amount: Jumlah uang (positif untuk income, negatif untuk expense)
        category: Kategori transaksi
        description: Deskripsi transaksi
        date: Tanggal transaksi (YYYY-MM-DD), default hari ini

    Returns:
        Dict dengan transaksi yang baru ditambahkan
    """
    transactions = _load_transactions()

    # Parse date
    if date:
        dt = datetime.strptime(date, '%Y-%m-%d')
    else:
        dt = datetime.now()

    # Create transaction
    new_transaction = {
        "id": len(transactions) + 1,
        "amount": amount,
        "category": category,
        "description": description,
        "date": date or dt.strftime('%Y-%m-%d'),
        "month": dt.month,
        "year": dt.year,
        "created_at": dt.isoformat()
    }

    transactions.append(new_transaction)
    _save_transactions(transactions)

    return {
        "success": True,
        "transaction": new_transaction,
        "message": f"Transaksi berhasil ditambahkan: {description} - Rp {amount:,.0f}"
    }


def get_balance() -> Dict:
    """
    Hitung total balance (income - expense)

    Returns:
        Dict dengan total income, expense, dan balance
    """
    transactions = _load_transactions()

    income = sum(t.get('amount', 0) for t in transactions if t.get('amount', 0) > 0)
    expense = sum(t.get('amount', 0) for t in transactions if t.get('amount', 0) < 0)
    balance = income + expense  # expense is negative

    return {
        "income": income,
        "expense": abs(expense),
        "balance": balance,
        "transaction_count": len(transactions)
    }