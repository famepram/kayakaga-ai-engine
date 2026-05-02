"""
Test response length fixes
Verify that Finai gives concise responses for simple questions
"""

from agent import FinaiAgent


def test_question(agent: FinaiAgent, question: str, max_bars: int, test_name: str):
    """Test a single question and check response length"""
    print(f"\n{'=' * 70}")
    print(f"TEST: {test_name}")
    print(f"{'=' * 70}")
    print(f"\n👤 Question: {question}")
    print(f"📏 Max bars allowed: {max_bars}")
    print(f"\n🤖 Finai:")

    response = agent.run_with_thinking(question)
    print(response)

    # Count lines (excluding empty lines)
    lines = [line for line in response.split('\n') if line.strip()]
    line_count = len(lines)

    status = "✅ PASS" if line_count <= max_bars else "❌ FAIL"
    print(f"\n{status} Line count: {line_count}/{max_bars}")

    return line_count <= max_bars


def main():
    """Run all response length tests"""
    print("\n" + "=" * 70)
    print("  FINAI AGENT - RESPONSE LENGTH TEST SUITE")
    print("=" * 70)

    try:
        # Initialize agent
        print("\n🔧 Initializing Finai Agent...")
        agent = FinaiAgent()
        print(f"✅ Agent initialized")

        # Run 3 test questions
        results = []

        # Test 1: Simple balance check
        agent.reset_conversation()
        results.append(test_question(
            agent,
            "Cek saldo semua akun",
            5,
            "Test 1: Balance check (max 5 bars)"
        ))

        # Test 2: GoPay sufficiency check
        agent.reset_conversation()
        results.append(test_question(
            agent,
            "GoPay gw cukup sampai akhir bulan?",
            5,
            "Test 2: GoPay check (max 5 bars)"
        ))

        # Test 3: Goals list
        agent.reset_conversation()
        results.append(test_question(
            agent,
            "Gw punya goals apa aja?",
            6,
            "Test 3: Goals list (max 6 bars)"
        ))

        # Summary
        print("\n" + "=" * 70)
        print("  TEST SUMMARY")
        print("=" * 70)

        total_tests = len(results)
        passed_tests = sum(results)

        print(f"\nTotal: {passed_tests}/{total_tests} tests passed")

        if passed_tests == total_tests:
            print("✅ All response length tests PASSED!")
        else:
            print("❌ Some tests FAILED - responses too verbose")

        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()