"""
Finai - Personal Finance Advisor AI
CLI entry point - API Version
"""

from agent import FinaiAgent
from agent.prompts import build_welcome_message
from agent.auth import get_token
import os


def print_startup_banner():
    """Print startup banner"""
    print("\n" + "=" * 60)
    print("  💰 Finai - Personal Finance Advisor AI")
    print("=" * 60)


def print_help():
    """Print available commands"""
    print("\n📋 Available Commands:")
    print("  'quit' / 'exit' / 'keluar'  - Keluar dari Finai")
    print("  'reset'                     - Reset conversation history")
    print("  '/balance'                  - Cek saldo semua akun")
    print("  '/goals'                    - Cek progress financial goals")
    print("  '/budget'                   - Pengeluaran bulan ini")
    print("  '/anomaly'                  - Cek transaksi mencurigakan")
    print("  '/help'                     - Tampilkan bantuan")
    print()


def handle_shortcut(agent: FinaiAgent, shortcut: str) -> bool:
    """
    Handle CLI shortcuts

    Returns:
        True jika shortcut di-handle, False jika bukan shortcut
    """
    shortcut = shortcut.lower().strip()

    if shortcut in ['/balance', 'balance', 'saldo']:
        print("\n💰 Cek Saldo...\n")
        response = agent.run_with_thinking("Cek saldo semua akun")
        print(f"\n🤖 Finai: {response}\n")
        return True

    elif shortcut in ['/goals', 'goals', 'target']:
        print("\n🎯 Cek Goals...\n")
        response = agent.run_with_thinking("Progress goals gw gimana?")
        print(f"\n🤖 Finai: {response}\n")
        return True

    elif shortcut in ['/budget', 'budget']:
        print("\n📊 Cek Budget...\n")
        response = agent.run_with_thinking("Pengeluaran bulan ini gimana?")
        print(f"\n🤖 Finai: {response}\n")
        return True

    elif shortcut in ['/anomaly', 'anomaly']:
        print("\n🔍 Cek Anomali...\n")
        response = agent.run_with_thinking("Ada transaksi mencurigakan bulan ini?")
        print(f"\n🤖 Finai: {response}\n")
        return True

    elif shortcut in ['reset', 'clear']:
        agent.reset_conversation()
        return True

    elif shortcut in ['/help', 'help', 'bantuan']:
        print_help()
        return True

    return False


def main():
    """Main CLI loop for Finai - API Version"""
    print("🚀 Memuat profil dari API...")

    # Test koneksi ke API
    try:
        get_token()
        print("✅ Terhubung ke kayakaga-api")
    except Exception as e:
        print(f"❌ Gagal terhubung ke API: {e}")
        print("\nPastikan:")
        print("  1. kayakaga-api berjalan di http://localhost:8080")
        print("  2. .env file sudah ada dengan konfigurasi API:")
        print("     - FINAI_API_URL=http://localhost:8080")
        print("     - FINAI_API_EMAIL=andi@finai.dev")
        print("     - FINAI_API_PASSWORD=finai123")
        return

    # Initialize Finai Agent
    try:
        agent = FinaiAgent()
    except Exception as e:
        print(f"❌ Gagal initialize agent: {e}")
        return

    # Print startup banner
    print_startup_banner()

    # Print welcome message
    welcome = build_welcome_message()
    print(welcome)

    # Print help
    print_help()

    # Main conversation loop
    while True:
        try:
            # Get user input
            user_input = input("👤 Kamu: ").strip()

            # Skip empty input
            if not user_input:
                continue

            # Handle quit commands
            if user_input.lower() in ['quit', 'exit', 'keluar']:
                print("\n👋 Sampai jumpa! Semoga keuangan kamu makin sehat! 💰\n")
                break

            # Handle shortcuts
            if handle_shortcut(agent, user_input):
                continue

            # Regular agent interaction
            response = agent.run_with_thinking(user_input)

            print(f"\n🤖 Finai: {response}\n")

        except KeyboardInterrupt:
            print("\n\n👋 Sampai jumpa! Semoga keuangan kamu makin sehat! 💰\n")
            break

        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")
            print("Coba lagi atau ketik '/help' untuk bantuan.\n")


if __name__ == "__main__":
    main()
