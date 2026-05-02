"""
Finai - Personal Finance Advisor AI
CLI entry point
"""

from agent import FinaiAgent, build_welcome_message
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
        response = agent.run_with_thinking("Berapa total saldo di semua akun saya?")
        print(f"\n🤖 Finai: {response}\n")
        return True

    elif shortcut in ['/goals', 'goals', 'target']:
        print("\n🎯 Cek Goals...\n")
        response = agent.run_with_thinking("Bagaimana progress financial goals saya?")
        print(f"\n🤖 Finai: {response}\n")
        return True

    elif shortcut in ['reset', 'clear']:
        agent.reset_conversation()
        print("✅ Conversation history di-reset. Mulai percakapan baru!\n")
        return True

    elif shortcut in ['/help', 'help', 'bantuan']:
        print_help()
        return True

    return False


def main():
    """Main CLI loop for Finai"""
    try:
        # Initialize Finai Agent
        agent = FinaiAgent()

        # Print startup banner
        print_startup_banner()

        # Print welcome message
        welcome = build_welcome_message(agent.user_context)
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

    except Exception as e:
        print(f"\n❌ Fatal Error: {str(e)}")
        print("Pastikan:")
        print("  1. .env file sudah ada dengan OPENROUTER_API_KEY")
        print("  2. Semua data files ada di folder data/")
        print("  3. Internet connection aktif")


if __name__ == "__main__":
    main()