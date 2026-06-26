"""
Hyperliquid SDK - Info API 测试
无需签名，可直接运行
"""
import os
import sys
import json
from hyperliquid.info import Info
from hyperliquid.utils import constants

# 使用 Mainnet
BASE_URL = constants.MAINNET_API_URL

# 测试用地址 (用户账户地址)
TEST_ADDRESS = os.getenv("HYPERLIQUID_API_ADDRESS", "0x5df5f623251f3661ca2c11ff0eae9c73f1214739")


def test_all_mids():
    """测试获取所有中间价"""
    print("\n=== Test: all_mids ===")
    info = Info(BASE_URL, skip_ws=True)
    mids = info.all_mids()
    print(f"Total coins: {len(mids)}")
    # 显示前5个
    for i, (coin, price) in enumerate(mids.items()):
        if i >= 5:
            break
        print(f"  {coin}: {price}")
    return True


def test_meta():
    """测试获取永续合约元数据"""
    print("\n=== Test: meta ===")
    info = Info(BASE_URL, skip_ws=True)
    meta = info.meta()
    universe = meta.get("universe", [])
    print(f"Total perp assets: {len(universe)}")
    # 显示前5个
    for i, asset in enumerate(universe[:5]):
        print(f"  [{i}] {asset['name']}: szDecimals={asset.get('szDecimals', 'N/A')}")
    return True


def test_spot_meta():
    """测试获取现货元数据"""
    print("\n=== Test: spot_meta ===")
    info = Info(BASE_URL, skip_ws=True)
    spot_meta = info.spot_meta()
    tokens = spot_meta.get("tokens", [])
    universe = spot_meta.get("universe", [])
    print(f"Total spot tokens: {len(tokens)}")
    print(f"Total spot pairs: {len(universe)}")
    # 显示前3个 pairs
    for i, pair in enumerate(universe[:3]):
        print(f"  [{i}] tokens={pair.get('tokens', [])}, name={pair.get('name', 'N/A')}")
    return True


def test_l2_snapshot():
    """测试获取 L2 订单簿快照"""
    print("\n=== Test: l2_snapshot ===")
    info = Info(BASE_URL, skip_ws=True)
    book = info.l2_snapshot("BTC")
    print(f"Coin: {book.get('coin', 'N/A')}")
    levels = book.get("levels", [[], []])
    bids, asks = levels
    print(f"Bids: {len(bids)} levels, Asks: {len(asks)} levels")
    if bids:
        print(f"  Best bid: {bids[0]}")
    if asks:
        print(f"  Best ask: {asks[0]}")
    return True


def test_user_state():
    """测试获取用户账户状态"""
    print("\n=== Test: user_state ===")
    info = Info(BASE_URL, skip_ws=True)
    state = info.user_state(TEST_ADDRESS)
    margin = state.get("marginSummary", {})
    print(f"Account value: {margin.get('accountValue', 'N/A')}")
    print(f"Total margin used: {margin.get('totalMarginUsed', 'N/A')}")
    positions = state.get("assetPositions", [])
    print(f"Open positions: {len(positions)}")
    for pos in positions[:3]:
        p = pos.get("position", {})
        print(f"  {p.get('coin', 'N/A')}: size={p.get('szi', 'N/A')}, entryPx={p.get('entryPx', 'N/A')}")
    return True


def test_open_orders():
    """测试获取用户挂单"""
    print("\n=== Test: open_orders ===")
    info = Info(BASE_URL, skip_ws=True)
    orders = info.open_orders(TEST_ADDRESS)
    print(f"Open orders: {len(orders)}")
    for order in orders[:3]:
        print(f"  {order.get('coin', 'N/A')}: side={order.get('side', 'N/A')}, "
              f"sz={order.get('sz', 'N/A')}, px={order.get('limitPx', 'N/A')}")
    return True


def test_user_fills():
    """测试获取用户成交记录"""
    print("\n=== Test: user_fills ===")
    info = Info(BASE_URL, skip_ws=True)
    fills = info.user_fills(TEST_ADDRESS)
    print(f"Recent fills: {len(fills)}")
    for fill in fills[:3]:
        print(f"  {fill.get('coin', 'N/A')}: side={fill.get('side', 'N/A')}, "
              f"sz={fill.get('sz', 'N/A')}, px={fill.get('px', 'N/A')}")
    return True


def test_user_rate_limit():
    """测试获取用户速率限制"""
    print("\n=== Test: user_rate_limit ===")
    info = Info(BASE_URL, skip_ws=True)
    rate_limit = info.user_rate_limit(TEST_ADDRESS)
    print(f"Rate limit info: {json.dumps(rate_limit, indent=2)}")
    return True


def test_candles_snapshot():
    """测试获取K线数据"""
    print("\n=== Test: candles_snapshot ===")
    info = Info(BASE_URL, skip_ws=True)
    import time
    end_time = int(time.time() * 1000)
    start_time = end_time - 3600 * 1000  # 1小时前
    candles = info.candles_snapshot("BTC", "1h", start_time, end_time)
    print(f"Candles received: {len(candles)}")
    if candles:
        c = candles[-1]
        print(f"  Latest: open={c.get('o', 'N/A')}, high={c.get('h', 'N/A')}, "
              f"low={c.get('l', 'N/A')}, close={c.get('c', 'N/A')}")
    return True


def main():
    print("=" * 50)
    print("Hyperliquid Info API Tests")
    print("=" * 50)
    print(f"Using address: {TEST_ADDRESS}")
    print(f"API URL: {BASE_URL}")
    
    tests = [
        ("all_mids", test_all_mids),
        ("meta", test_meta),
        ("spot_meta", test_spot_meta),
        ("l2_snapshot", test_l2_snapshot),
        ("user_state", test_user_state),
        ("open_orders", test_open_orders),
        ("user_fills", test_user_fills),
        ("user_rate_limit", test_user_rate_limit),
        ("candles_snapshot", test_candles_snapshot),
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
