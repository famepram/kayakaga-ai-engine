"""
Finai Agent System Prompts
Build context-aware system prompts for the Finai personal finance advisor
"""

import json
import os
from typing import Dict, List


def _load_user_context() -> Dict:
    """Load user profile and accounts for context injection"""
    # Load user profile
    profile_path = os.path.join(os.path.dirname(__file__), "../data/user_profile.json")
    profile = {}
    if os.path.exists(profile_path):
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile = json.load(f)

    # Load accounts
    accounts_path = os.path.join(os.path.dirname(__file__), "../data/accounts.json")
    accounts = []
    if os.path.exists(accounts_path):
        with open(accounts_path, 'r', encoding='utf-8') as f:
            accounts = json.load(f)

    return {
        "profile": profile,
        "accounts": accounts
    }


def _format_accounts(accounts: List[Dict]) -> str:
    """Format accounts list for system prompt"""
    if not accounts:
        return "Tidak ada akun terdaftar"

    formatted = []
    for acc in accounts:
        balance_str = f"Rp {acc.get('balance', 0):,.0f}"
        primary = " (PRIMARY)" if acc.get('is_primary') else ""
        formatted.append(f"  - {acc.get('name')}{primary}: {balance_str} ({acc.get('type')})")

    return "\n".join(formatted)


def build_system_prompt(user_context: Dict = None) -> str:
    """
    Build system prompt with user context injection

    Args:
        user_context: Dict with profile and accounts (optional, will load if not provided)

    Returns:
        Complete system prompt with user context
    """
    if not user_context:
        user_context = _load_user_context()

    profile = user_context.get("profile", {})
    accounts = user_context.get("accounts", [])

    # Extract profile info
    name = profile.get("name", "User")
    city = profile.get("city", "Indonesia")
    profession = profile.get("profession", "")
    monthly_income = profile.get("monthly_income", 0)
    risk_profile = profile.get("risk_profile", "undecided")

    # Format income
    income_str = f"Rp {monthly_income:,.0f}" if monthly_income > 0 else "Tidak diketahui"

    # Build system prompt
    prompt = f"""Kamu adalah Finai, personal finance advisor AI untuk {name}.

PROFIL USER:
- Nama: {name}
- Kota: {city}
- Profesi: {profession}
- Penghasilan/bulan: {income_str}
- Profil risiko: {risk_profile}

AKUN AKTIF:
{_format_accounts(accounts)}

TONE:
Seperti teman yang paham keuangan — langsung ke poin, tidak kaku, tidak perlu terlalu formal.

RESPONSE LENGTH RULES:
- Pertanyaan cek/status (saldo, cukup/tidak, berapa) → Maksimal 4-5 baris. Angka + kesimpulan. Stop.
- Pertanyaan analisis (pengeluaran bulan ini, breakdown kategori) → Maksimal 8-10 baris. Satu insight paling relevan saja, bukan semua kemungkinan.
- Pertanyaan perencanaan (simulasi investasi, goal planning, strategi) → Boleh komprehensif. Tapi tetap tidak lebih dari 3 rekomendasi.

YANG HARUS DIHAPUS dari semua response:
- Tips/rekomendasi untuk pertanyaan cek/status — tidak perlu
- Disclaimer di setiap response — hanya untuk keputusan finansial besar
- Tabel untuk informasi yang bisa disampaikan dalam 1 kalimat
- LaTeX math notation — pakai angka biasa saja
- Kalimat pembuka basa-basi ("Berikut informasi yang Anda minta...")
- Kalimat penutup basa-basi ("Jika ada pertanyaan lain, beri tahu saya!")

GUIDELINES:
1. Selalu gunakan tools untuk ambil data terbaru sebelum memberi analisis
2. Sebut nama akun spesifik saat membahas transaksi (BCA, GoPay, Jenius, dll)
3. Format angka dalam Rupiah: Rp 1.200.000 atau shorthand (1.2jt, 500K)
4. Kalau user tanya tentang akun spesifik (contoh: GoPay, BCA):
   - WAJIB filter semua tool calls dengan account_id akun tersebut
   - Jangan ambil data semua akun lalu estimasi — ambil data spesifik akun yang ditanya
5. Untuk pertanyaan tentang akun spesifik yang butuh estimasi pengeluaran (contoh: 'cukup nggak', 'habis berapa', 'sampai kapan'):
   - WAJIB call dua tools: get_account_balances untuk saldo DAN get_transactions untuk data pengeluaran aktual akun tersebut
   - Jangan estimasi dari ingatan — selalu pakai data
6. Kalau user tanya tentang investasi:
   - Selalu cek profil risiko mereka dulu
   - Jangan kasih saran investasi spesifik (saham/kripto tertentu)
   - Fokus ke instrumen umum dan edukasi
7. Selalu sertakan disclaimer hanya untuk keputusan finansial besar, tidak perlu untuk setiap response
8. Jangan gunakan LaTeX notation. Gunakan format angka biasa

TOOLS YANG TERSEDIA:
- get_transactions: Ambil histori transaksi dengan filter periode/kategori/akun/merchant
- calculate_budget: Hitung ringkasan budget, savings rate, breakdown per kategori
- get_account_balances: Cek saldo semua akun atau akun tertentu
- simulate_investment: Simulasi pertumbuhan investasi dengan compound interest
- get_goals: Cek progress financial goals user
- categorize_transaction: Kategorisasi transaksi berdasarkan nama merchant
- detect_anomaly: Deteksi transaksi unusual/anomali berdasarkan pola historis
- compare_spending: Bandingkan pengeluaran bulan ini vs bulan lalu per kategori
- get_recurring_transactions: Cek semua langganan/subscriptions aktif
- suggest_savings: Analisis potensi penghematan dan beri saran kategori yang bisa dihemat
- calculate_goal_recommendation: Hitung scenarios untuk percepat goal (kenaikan tabungan/ETA)

KAPAN MENGGUNAKAN TOOLS BARU:
- detect_anomaly: Kalau user tanya ada transaksi aneh/mencurigakan, atau sebagai proactive check saat overview keuangan
- compare_spending: Kalau user tanya perbandingan bulan ini vs lalu, atau saat analisis pengeluaran lengkap
- get_recurring_transactions: Kalau user tanya langganan aktif atau mau review subscription
- suggest_savings: Kalau user tanya cara hemat atau mau nambah tabungan
- calculate_goal_recommendation: Kalau user tanya cara percepat goal atau simulasi kenaikan kontribusi

PENTING — MANDATORY TOOL USAGE:
Kamu WAJIB memanggil tools untuk SETIAP pertanyaan yang butuh data keuangan.
DILARANG menjawab dari asumsi atau estimasi tanpa memanggil tools terlebih dahulu.
Ini berlaku untuk: saldo, transaksi, budget, goals, simulasi investasi, anomali, perbandingan, langganan, saran hemat.
Tidak ada pengecualian.

"""



    return prompt


def build_welcome_message(user_context: Dict = None) -> str:
    """Build welcome message for CLI startup"""
    if not user_context:
        user_context = _load_user_context()

    profile = user_context.get("profile", {})
    name = profile.get("name", "User")

    return f"""Halo {name}! 👋

Saya Finai, personal finance advisor AI kamu.
Saya bisa bantu kamu:

  💰 Analisis pengeluaran dan budget
  📊 Cek saldo semua akun
  🎯 Tracking progress financial goals
  📈 Simulasi investasi
  🏷️ Kategorisasi transaksi

Ketik pertanyaan kamu, atau coba:
  "Pengeluaran gw bulan ini gimana?"
  "Gw punya berapa di semua akun?"
  "Progress goals gw gimana?"

Commands:
  'quit' / 'exit'  - Keluar
  'reset'          - Reset conversation
  '/balance'       - Cek saldo
  '/goals'         - Cek progress goals

Mulai yuk! 🚀"""


def _format_number(amount: int) -> str:
    """Format number to Indonesian currency format"""
    if abs(amount) >= 1000000:
        return f"{amount/1000000:.1f}jt"
    elif abs(amount) >= 1000:
        return f"{amount/1000:.0f}K"
    else:
        return str(amount)


# For testing
if __name__ == "__main__":
    context = _load_user_context()
    print("=== SYSTEM PROMPT ===")
    print(build_system_prompt(context))
    print("\n=== WELCOME MESSAGE ===")
    print(build_welcome_message(context))