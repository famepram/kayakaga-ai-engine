"""
Test 5 new Finai tools
Verify all tools work correctly and produce expected output
"""

from agent import FinaiAgent


def test_new_tool(agent: FinaiAgent, question: str, expected_tool: str, test_name: str):
    """Test a single new tool"""
    print(f"\n{'=' * 70}")
    print(f"TEST: {test_name}")
    print(f"{'=' * 70}")
    print(f"\n👤 Question: {question}")
    print(f"🎯 Expected tool: {expected_tool}")
    print(f"\n🤖 Finai:")

    response = agent.run_with_thinking(question)
    print(response)

    print(f"\n✅ Test complete - verify {expected_tool} was called above")


def main():
    """Run all 5 new tool tests"""
    print("\n" + "=" * 70)
    print("  FINAI AGENT - NEW TOOLS TEST SUITE")
    print("=" * 70)

    try:
        # Initialize agent
        print("\n🔧 Initializing Finai Agent...")
        agent = FinaiAgent()
        print(f"✅ Agent initialized")

        # Test 1: detect_anomaly
        agent.reset_conversation()
        test_new_tool(
            agent,
            "Ada transaksi mencurigakan bulan ini?",
            "detect_anomaly",
            "Test 1: Anomaly Detection"
        )

        # Test 2: compare_spending
        agent.reset_conversation()
        test_new_tool(
            agent,
            "Pengeluaran gw naik atau turun dari bulan lalu?",
            "compare_spending",
            "Test 2: Spending Comparison"
        )

        # Test 3: get_recurring_transactions
        agent.reset_conversation()
        test_new_tool(
            agent,
            "Langganan gw ada apa aja?",
            "get_recurring_transactions",
            "Test 3: Recurring Transactions"
        )

        # Test 4: suggest_savings
        agent.reset_conversation()
        test_new_tool(
            agent,
            "Gw mau hemat 500rb per bulan, bisa dari mana?",
            "suggest_savings",
            "Test 4: Savings Suggestions"
        )

        # Test 5: calculate_goal_recommendation
        agent.reset_conversation()
        test_new_tool(
            agent,
            "Kalau gw naikin tabungan DP rumah jadi 4jt/bulan, selesai kapan?",
            "calculate_goal_recommendation",
            "Test 5: Goal Recommendation"
        )

        print("\n" + "=" * 70)
        print("  ALL NEW TOOLS TESTS COMPLETED!")
        print("=" * 70)
        print("\n✅ Verify:")
        print("  - detect_anomaly: Flagged unusual transactions (tx_020: Toko Mas 2.5jt)")
        print("  - compare_spending: Showed category breakdown with % changes")
        print("  - get_recurring_transactions: Listed Netflix, Spotify, PLN, etc.")
        print("  - suggest_savings: Suggested categories with potential savings")
        print("  - calculate_goal_recommendation: Showed scenarios for faster completion")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()