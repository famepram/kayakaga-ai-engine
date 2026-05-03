"""
Test Finai Agent connection to API
"""

print("=" * 60)
print("FINAI AGENT - CONNECTION TEST")
print("=" * 60)

print("\n[TEST 1] Testing imports...")
try:
    from agent import FinaiAgent, TOOL_DEFINITIONS, TOOL_HANDLERS
    print("✅ Imports successful")
    print(f"   Tools available: {len(TOOL_HANDLERS)}")
    print(f"   Tool names: {list(TOOL_HANDLERS.keys())}")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n[TEST 2] Testing API connection...")
try:
    from agent.auth import get_token
    token = get_token()
    print(f"✅ Connected to API!")
    print(f"   Token (first 20 chars): {token[:20]}...")
except Exception as e:
    print(f"❌ API connection failed: {e}")
    import traceback
    traceback.print_exc()
    print("\nMake sure kayakaga-api is running at http://localhost:8080")
    exit(1)

print("\n[TEST 3] Testing FinaiAgent initialization...")
try:
    agent = FinaiAgent()
    print("✅ FinaiAgent initialized successfully")
    print(f"   Model: {agent.model}")
except Exception as e:
    print(f"❌ Agent init failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 60)
print("ALL TESTS PASSED! ✅")
print("=" * 60)
print("\nYou can now run: python main.py")
print("\nQuick test questions:")
print("1. 'Cek saldo semua akun'")
print("2. 'Pengeluaran bulan ini gimana?'")
print("3. 'Ada transaksi mencurigakan?'")
print("4. 'Langganan gw ada apa aja?'")
print("5. 'Kalau gw naikin DP rumah jadi 4jt/bulan, selesai kapan?'")
