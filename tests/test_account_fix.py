"""
Test script to verify the 3 fixes
"""

from agent import FinaiAgent


def test_account_matching():
    """Test ISSUE 1: Account matching by ID OR name"""
    from agent.tools import _resolve_account_id

    print("\n" + "=" * 70)
    print("TEST: Account Matching (ISSUE 1)")
    print("=" * 70)

    test_cases = [
        ("acc_bca", "acc_bca", "Exact ID match"),
        ("acc_gopay", "acc_gopay", "Exact ID match"),
        ("BCA", "acc_bca", "Name match (uppercase)"),
        ("gopay", "acc_gopay", "Name match (lowercase)"),
        ("GoPay", "acc_gopay", "Name match (mixed case)"),
        ("Jenius", "acc_jenius", "Name match (Jenius)")
    ]

    for input_val, expected, description in test_cases:
        result = _resolve_account_id(input_val)
        status = "✅" if result == expected else "❌"
        print(f"{status} {description:30s} '{input_val}' → '{result}' (expected: '{expected}')")

    print()


def test_gopay_question():
    """Test complete flow with GoPay question"""
    print("\n" + "=" * 70)
    print("TEST: GoPay Question (ISSUE 2 & 3)")
    print("=" * 70)

    try:
        agent = FinaiAgent()

        question = "GoPay gw cukup nggak sampai akhir bulan?"
        print(f"\n👤 User: {question}")
        print(f"\n🤖 Finai: ")

        response = agent.run_with_thinking(question)

        print(response)

        print("\n" + "=" * 70)
        print("Expected behavior:")
        print("  🔧 get_account_balances({\"account_id\": \"acc_gopay\"})")
        print("  🔧 get_transactions({\"period\": \"month\", \"account_id\": \"acc_gopay\"})")
        print("  Response: Singkat, langsung jawab, 3-4 baris")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  FINAI AGENT - FIX VERIFICATION TEST SUITE")
    print("=" * 70)

    # Test 1: Account matching
    test_account_matching()

    # Test 2: GoPay question
    test_gopay_question()

    print("\n" + "=" * 70)
    print("  TEST SUITE COMPLETED")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()