"""
Hyperliquid SDK - WebSocket 测试
测试各种 WebSocket 订阅
"""
import os
import time
import threading
from hyperliquid.info import Info
from hyperliquid.utils import constants

BASE_URL = constants.MAINNET_API_URL
TEST_ADDRESS = os.getenv("HYPERLIQUID_API_ADDRESS", "0x5df5f623251f3661ca2c11ff0eae9c73f1214739")


def test_all_mids_subscription():
    """测试订阅所有中间价"""
    print("\n=== Test: allMids subscription ===")
    received = []

    def callback(msg):
        received.append(msg)
        if len(received) <= 2:
            print(f"  Received: {str(msg)[:200]}...")

    info = Info(BASE_URL, skip_ws=False)
    info.subscribe({"type": "allMids"}, callback)

    print("Waiting for messages (3 seconds)...")
    time.sleep(3)
    info.unsubscribe({"type": "allMids"}, callback)
    print(f"Received {len(received)} messages")
    return len(received) > 0


def test_bbo_subscription():
    """测试订阅 BBO"""
    print("\n=== Test: bbo subscription (BTC) ===")
    received = []

    def callback(msg):
        received.append(msg)
        if len(received) <= 3:
            data = msg.get("data", {})
            print(f"  BBO: bid={data.get('bbo', [None, None])[0]}, ask={data.get('bbo', [None, None])[1]}")

    info = Info(BASE_URL, skip_ws=False)
    info.subscribe({"type": "bbo", "coin": "BTC"}, callback)

    print("Waiting for messages (3 seconds)...")
    time.sleep(3)
    info.unsubscribe({"type": "bbo", "coin": "BTC"}, callback)
    print(f"Received {len(received)} messages")
    return len(received) > 0


def test_l2book_subscription():
    """测试订阅 L2 订单簿"""
    print("\n=== Test: l2Book subscription (ETH) ===")
    received = []

    def callback(msg):
        received.append(msg)
        if len(received) == 1:
            data = msg.get("data", {})
            levels = data.get("levels", [[], []])
            print(f"  Bids: {len(levels[0])} levels, Asks: {len(levels[1])} levels")

    info = Info(BASE_URL, skip_ws=False)
    info.subscribe({"type": "l2Book", "coin": "ETH"}, callback)

    print("Waiting for messages (3 seconds)...")
    time.sleep(3)
    info.unsubscribe({"type": "l2Book", "coin": "ETH"}, callback)
    print(f"Received {len(received)} messages")
    return len(received) > 0


def test_trades_subscription():
    """测试订阅成交流"""
    print("\n=== Test: trades subscription (BTC) ===")
    received = []

    def callback(msg):
        received.append(msg)
        if len(received) <= 3:
            data = msg.get("data", [])
            if data:
                trade = data[0] if isinstance(data, list) else data
                print(f"  Trade: side={trade.get('side', 'N/A')}, sz={trade.get('sz', 'N/A')}, px={trade.get('px', 'N/A')}")

    info = Info(BASE_URL, skip_ws=False)
    info.subscribe({"type": "trades", "coin": "BTC"}, callback)

    print("Waiting for messages (5 seconds)...")
    time.sleep(5)
    info.unsubscribe({"type": "trades", "coin": "BTC"}, callback)
    print(f"Received {len(received)} messages")
    return True  # trades 可能不活跃


def test_order_updates_subscription():
    """测试订阅用户订单更新"""
    print("\n=== Test: orderUpdates subscription ===")
    received = []

    def callback(msg):
        received.append(msg)
        print(f"  Order update: {str(msg)[:150]}...")

    info = Info(BASE_URL, skip_ws=False)
    info.subscribe({"type": "orderUpdates", "user": TEST_ADDRESS}, callback)

    print("Waiting for messages (3 seconds)...")
    time.sleep(3)
    info.unsubscribe({"type": "orderUpdates", "user": TEST_ADDRESS}, callback)
    print(f"Received {len(received)} messages (may be 0 if no order activity)")
    return True


def test_user_fills_subscription():
    """测试订阅用户成交"""
    print("\n=== Test: userFills subscription ===")
    received = []

    def callback(msg):
        received.append(msg)
        print(f"  User fill: {str(msg)[:150]}...")

    info = Info(BASE_URL, skip_ws=False)
    info.subscribe({"type": "userFills", "user": TEST_ADDRESS}, callback)

    print("Waiting for messages (3 seconds)...")
    time.sleep(3)
    info.unsubscribe({"type": "userFills", "user": TEST_ADDRESS}, callback)
    print(f"Received {len(received)} messages (may be 0 if no fills)")
    return True


def main():
    print("=" * 50)
    print("Hyperliquid WebSocket Tests")
    print("=" * 50)
    print(f"Using address: {TEST_ADDRESS}")
    print(f"API URL: {BASE_URL}")

    tests = [
        ("allMids", test_all_mids_subscription),
        ("bbo", test_bbo_subscription),
        ("l2Book", test_l2book_subscription),
        ("trades", test_trades_subscription),
        ("orderUpdates", test_order_updates_subscription),
        ("userFills", test_user_fills_subscription),
    ]

    results = []
    for name, test_fn in tests:
        try:
            success = test_fn()
            results.append((name, "PASS" if success else "FAIL"))
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append((name, f"ERROR: {e}"))

    print("\n" + "=" * 50)
    print("Summary:")
    for name, status in results:
        print(f"  {name}: {status}")


if __name__ == "__main__":
    main()
