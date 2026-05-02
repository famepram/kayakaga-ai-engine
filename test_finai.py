"""
Finai Agent Test Script
Test all 5 sample conversations from the spec
"""

from agent import FinaiAgent


def test_conversation(agent: FinaiAgent, question: str, test_name: str):
    """Test a single conversation"""
    print(f"\n{'=' * 70}")
    print(f"TEST: {test_name}")
    print(f"{'=' * 70}")
    print(f"\n👤 User: {question}")
    print(f"\n🤖 Finai: ")

    response = agent.run_with_thinking(question)
    print(response)

    print(f"\n✅ Test complete: {test_name}")


def main():
    """Run all test conversations"""
    print("\n" + "=" * 70)
    print("  FINAI AGENT - TEST SUITE")
    print("=" * 70)

    try:
        # Initialize agent
        print("\n🔧 Initializing Finai Agent...")
        agent = FinaiAgent()
        print(f"✅ Agent initialized")
        print(f"👤 User: {agent.user_context.get('profile', {}).get('name')}")
        print(f"📊 Model: {agent.model}")
        print(f"🏦 Accounts: {len(agent.user_context.get('accounts', []))} accounts")

        # Run 5 test conversations
        test_conversation(
            agent,
            "Pengeluaran gw bulan ini gimana?",
            "Test 1: Monthly spending analysis"
        )

        agent.reset_conversation()

        test_conversation(
            agent,
            "Gw punya berapa di semua akun?",
            "Test 2: Total balance check"
        )

        agent.reset_conversation()

        test_conversation(
            agent,
            "Kalau invest 2jt per bulan selama 10 tahun dengan return 10%, balik berapa?",
            "Test 3: Investment simulation"
        )

        agent.reset_conversation()

        test_conversation(
            agent,
            "GoPay gw masih cukup nggak sampai akhir bulan?",
            "Test 4: Specific account balance check"
        )

        agent.reset_conversation()

        test_conversation(
            agent,
            "Progress goals gw gimana?",
            "Test 5: Goals progress check"
        )

        print("\n" + "=" * 70)
        print("  🎉 ALL TESTS COMPLETED!")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()