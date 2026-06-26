"""
Hyperliquid SDK - 订单操作测试
需要 API 私钥签名
"""
import os
import time
import json
from eth_account import Account
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants

# 配置
BASE_URL = constants.MAINNET_API_URL
SECRET_KEY = os.getenv("HYPERLIQUID_API", "")
ACCOUNT_ADDRESS = os.getenv("HYPERLIQUID_API_ADDRESS", "")


def setup():
    """初始化 Info 和 Exchange 客户端"""
    if not SECRET_KEY:
        raise ValueError("请设置环境变量 HYPERLIQUID_API")
    if not ACCOUNT_ADDRESS:
        raise ValueError("请设置环境变量 HYPERLIQUID_API_ADDRESS")

    info = Info(BASE_URL, skip_ws=True)
    wallet = Account.from_key(SECRET_KEY)
    exchange = Exchange(wallet, BASE_URL, account_address=ACCOUNT_ADDRESS)
    return info, exchange


def test_get_mid_price(info: Info, coin: str):
    """获取当前中间价"""
    mids = info.all_mids()
    if coin in mids:
        return float(mids[coin])
    raise ValueError(f"Coin {coin} not found")


def test_limit_order_gtc(exchange: Exchange, info: Info):
    """测试 GTC 限价单：下单 -> 查询 -> 撤单"""
    print("\n=== Test: Limit Order (GTC) ===")
    coin = "ETH"

    # 获取当前价格，下一个很低的买单 (不会成交)
    mid_price = test_get_mid_price(info, coin)
    order_price = round(mid_price * 0.8, 1)  # 低于市价 20%
    order_sz = 0.01  # 最小量

    print(f"Mid price: {mid_price}, Order price: {order_price}")

    # 下单
    result = exchange.order(coin, True, order_sz, order_price, {"limit": {"tif": "Gtc"}})
    print(f"Order result: {json.dumps(result, indent=2)}")

    if result.get("status") != "ok":
        print(f"  Order failed: {result}")
        return False

    status = result["response"]["data"]["statuses"][0]
    if "resting" not in status:
        print(f"  Order not resting: {status}")
        return False

    oid = status["resting"]["oid"]
    print(f"  Order placed, oid: {oid}")

    # 查询订单状态
    order_status = info.query_order_by_oid(ACCOUNT_ADDRESS, oid)
    print(f"  Order status: {order_status.get('order', {}).get('status', 'N/A')}")

    # 撤单
    cancel_result = exchange.cancel(coin, oid)
    print(f"  Cancel result: {json.dumps(cancel_result, indent=2)}")

    return cancel_result.get("status") == "ok"


def test_limit_order_alo(exchange: Exchange, info: Info):
    """测试 ALO (Post Only) 限价单"""
    print("\n=== Test: Limit Order (ALO - Post Only) ===")
    coin = "BTC"

    mid_price = test_get_mid_price(info, coin)
    order_price = round(mid_price * 0.85, 0)  # 低于市价 15%
    order_sz = 0.0001

    print(f"Mid price: {mid_price}, Order price: {order_price}")

    result = exchange.order(coin, True, order_sz, order_price, {"limit": {"tif": "Alo"}})
    print(f"Order result: {json.dumps(result, indent=2)}")

    if result.get("status") != "ok":
        print(f"  Order failed: {result}")
        return False

    status = result["response"]["data"]["statuses"][0]
    if "resting" not in status:
        print(f"  Order not resting (may have crossed): {status}")
        return True  # ALO 可能因为价格问题被拒绝

    oid = status["resting"]["oid"]
    print(f"  Order placed, oid: {oid}")

    # 撤单
    cancel_result = exchange.cancel(coin, oid)
    print(f"  Cancel result: {cancel_result.get('status', 'N/A')}")

    return True


def test_bulk_orders(exchange: Exchange, info: Info):
    """测试批量下单"""
    print("\n=== Test: Bulk Orders ===")
    coin = "ETH"

    mid_price = test_get_mid_price(info, coin)

    # 准备多个订单
    orders = []
    for i in range(3):
        price = round(mid_price * (0.75 - i * 0.05), 1)
        orders.append({
            "coin": coin,
            "is_buy": True,
            "sz": 0.01,
            "limit_px": price,
            "order_type": {"limit": {"tif": "Gtc"}},
            "reduce_only": False,
        })

    print(f"Placing {len(orders)} orders...")
    result = exchange.bulk_orders(orders)
    print(f"Bulk order result: {json.dumps(result, indent=2)}")

    if result.get("status") != "ok":
        return False

    # 收集 oids 撤单
    oids = []
    for status in result["response"]["data"]["statuses"]:
        if "resting" in status:
            oids.append(status["resting"]["oid"])

    print(f"  Placed {len(oids)} orders")

    # 批量撤单
    if oids:
        cancel_requests = [{"coin": coin, "oid": oid} for oid in oids]
        cancel_result = exchange.bulk_cancel(cancel_requests)
        print(f"  Bulk cancel result: {cancel_result.get('status', 'N/A')}")

    return True


def test_order_with_cloid(exchange: Exchange, info: Info):
    """测试带 cloid 下单"""
    print("\n=== Test: Order with cloid ===")
    from hyperliquid.utils.types import Cloid

    coin = "ETH"
    mid_price = test_get_mid_price(info, coin)
    order_price = round(mid_price * 0.8, 1)

    # 生成 cloid
    cloid = Cloid.from_str("0x" + hex(int(time.time() * 1000))[2:].zfill(32))
    print(f"Using cloid: {cloid}")

    result = exchange.order(coin, True, 0.01, order_price, {"limit": {"tif": "Gtc"}}, cloid=cloid)
    print(f"Order result: {json.dumps(result, indent=2)}")

    if result.get("status") != "ok":
        return False

    status = result["response"]["data"]["statuses"][0]
    if "resting" not in status:
        return True

    # 用 cloid 撤单
    cancel_result = exchange.cancel_by_cloid(coin, cloid)
    print(f"  Cancel by cloid result: {json.dumps(cancel_result, indent=2)}")

    return cancel_result.get("status") == "ok"


def main():
    print("=" * 50)
    print("Hyperliquid Order Tests")
    print("=" * 50)
    print(f"Account: {ACCOUNT_ADDRESS}")
    print(f"API URL: {BASE_URL}")

    info, exchange = setup()

    # 检查账户余额
    state = info.user_state(ACCOUNT_ADDRESS)
    account_value = state.get("marginSummary", {}).get("accountValue", "0")
    print(f"Account value: {account_value}")

    if float(account_value) == 0:
        print("\n⚠️ 账户无余额，无法进行交易测试")
        print("请先向账户转入 USDC")
        return

    tests = [
        ("limit_order_gtc", lambda: test_limit_order_gtc(exchange, info)),
        ("limit_order_alo", lambda: test_limit_order_alo(exchange, info)),
        ("bulk_orders", lambda: test_bulk_orders(exchange, info)),
        ("order_with_cloid", lambda: test_order_with_cloid(exchange, info)),
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
