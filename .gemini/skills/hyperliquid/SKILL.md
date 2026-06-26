---
name: hyperliquid
description: Hyperliquid DEX API 开发指南 - REST/WebSocket API 和 Python SDK 使用
---

# Hyperliquid 开发技能

## 概述

Hyperliquid 是一个高性能 L1 DEX，支持永续合约和现货交易。本技能提供 API 参考和 Python SDK 使用指南。

## 快速开始

### 安装 SDK
```bash
pip install hyperliquid-python-sdk
```

### 配置
```python
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants

# Info API (无需签名)
info = Info(constants.MAINNET_API_URL, skip_ws=True)

# Exchange API (需要签名)
exchange = Exchange(wallet, constants.MAINNET_API_URL)
```

### 环境变量
```
HYPERLIQUID_API=0x...          # API 钱包私钥
HYPERLIQUID_API_ADDRESS=0x...  # 主账户地址 (不是 API 钱包地址!)
```

## API 端点

| 环境 | REST API | WebSocket |
|------|----------|-----------|
| Mainnet | `https://api.hyperliquid.xyz` | `wss://api.hyperliquid.xyz/ws` |
| Testnet | `https://api.hyperliquid-testnet.xyz` | `wss://api.hyperliquid-testnet.xyz/ws` |

---

## Info API 参考

### 常用方法

```python
# 所有中间价
mids = info.all_mids()  # {"BTC": "42000.5", "ETH": "2500.0", ...}

# L2 订单簿 (最多20档)
book = info.l2_snapshot("BTC")
# {"coin": "BTC", "levels": [[bids], [asks]], "time": 1234567890}

# 用户账户状态
state = info.user_state(address)
# {"marginSummary": {...}, "assetPositions": [...], ...}

# 用户挂单
orders = info.open_orders(address)

# 用户成交记录
fills = info.user_fills(address)  # 最近 2000 条

# 永续元数据 (获取 asset index)
meta = info.meta()
# {"universe": [{"name": "BTC", "szDecimals": 5, ...}, ...]}

# 现货元数据
spot_meta = info.spot_meta()

# K线数据
candles = info.candles_snapshot("BTC", "1h", start_time, end_time)

# 订单状态查询
status = info.query_order_by_oid(address, oid)
```

### Rate Limit 权重

| 请求类型 | 权重 |
|---------|------|
| allMids, l2Book, clearinghouseState, orderStatus | 2 |
| userFills, candleSnapshot, 大多数其他 | 20 |
| userRole | 60 |

---

## Exchange API 参考

### 下单

```python
# 限价单 (GTC)
result = exchange.order("ETH", True, 0.1, 2500.0, {"limit": {"tif": "Gtc"}})

# 限价单 - Post Only (ALO)
result = exchange.order("ETH", True, 0.1, 2500.0, {"limit": {"tif": "Alo"}})

# 限价单 - IOC
result = exchange.order("ETH", True, 0.1, 2500.0, {"limit": {"tif": "Ioc"}})

# 市价单
result = exchange.market_order("ETH", True, 0.1, slippage=0.01)

# 带 cloid 下单
from hyperliquid.utils.types import Cloid
cloid = Cloid.from_str("0x" + "1234" * 8)
result = exchange.order("ETH", True, 0.1, 2500.0, {"limit": {"tif": "Gtc"}}, cloid=cloid)
```

**Order 参数说明:**
- `coin`: 交易对 (如 "ETH", "BTC")
- `is_buy`: True=买入, False=卖出
- `sz`: 数量 (以 coin 为单位)
- `px`: 价格
- `order_type`: `{"limit": {"tif": "Gtc|Alo|Ioc"}}` 或 trigger 订单

### 撤单

```python
# 按 oid 撤单
exchange.cancel("ETH", oid)

# 按 cloid 撤单
exchange.cancel_by_cloid("ETH", cloid)

# 批量撤单
exchange.bulk_cancel([{"coin": "ETH", "oid": oid1}, {"coin": "BTC", "oid": oid2}])
```

### 修改订单

```python
exchange.modify_order(oid, "ETH", True, 0.1, 2600.0, {"limit": {"tif": "Gtc"}})
```

### TP/SL 止盈止损

```python
# 止盈单
exchange.order("ETH", False, 0.1, 3000.0, {
    "trigger": {
        "isMarket": True,
        "triggerPx": "3000.0",
        "tpsl": "tp"
    }
}, reduce_only=True)

# 止损单
exchange.order("ETH", False, 0.1, 2000.0, {
    "trigger": {
        "isMarket": True,
        "triggerPx": "2000.0",
        "tpsl": "sl"
    }
}, reduce_only=True)
```

### 杠杆设置

```python
# 全仓杠杆
exchange.update_leverage(10, "ETH", is_cross=True)

# 逐仓杠杆
exchange.update_leverage(5, "ETH", is_cross=False)
```

### 资金转移

```python
# USDC 转账
exchange.usdc_transfer(100.0, "0x目标地址")

# Spot 转账
exchange.spot_transfer(10.0, "0x目标地址", token="HYPE")

# Spot → Perp 账户转移
exchange.class_transfer(100.0, True)  # True = spot_to_perp
```

---

## WebSocket API

### 订阅示例

```python
from hyperliquid.info import Info

info = Info(constants.MAINNET_API_URL, skip_ws=False)

# 订阅 BBO
def on_bbo(msg):
    print(f"BBO: {msg}")

info.subscribe({"type": "bbo", "coin": "BTC"}, on_bbo)

# 订阅 L2 Book
info.subscribe({"type": "l2Book", "coin": "ETH"}, callback)

# 订阅成交
info.subscribe({"type": "trades", "coin": "BTC"}, callback)

# 订阅所有中间价
info.subscribe({"type": "allMids"}, callback)

# 订阅用户订单更新
info.subscribe({"type": "orderUpdates", "user": address}, callback)

# 订阅用户成交
info.subscribe({"type": "userFills", "user": address}, callback)
```

### 订阅类型

| 类型 | 参数 | 描述 |
|-----|------|------|
| `allMids` | - | 所有中间价 |
| `l2Book` | coin | L2 订单簿 |
| `trades` | coin | 成交流 |
| `bbo` | coin | 最优报价 |
| `orderUpdates` | user | 订单状态更新 |
| `userFills` | user | 用户成交 |
| `candle` | coin, interval | K线 |

---

## Asset ID 规则

| 资产类型 | ID 计算 | 示例 |
|----------|--------|------|
| Perpetuals | `meta().universe` 索引 | BTC=0, ETH=1 |
| Spot | `10000 + spotMeta().universe` 索引 | PURR/USDC=10000 |
| Builder Perps (HIP-3) | `@` + 索引 | @182=GOLD, @156=SILVER |

---

## HIP-3 / xyz 市场 (Builder Perps)

HIP-3 市场是第三方部署的永续合约，在 Hyperliquid UI 中显示为 "xyz" 标签。

### 符号格式

支持两种格式：

| 格式 | 示例 | 说明 |
|------|------|------|
| `{dex}:{coin}` | `xyz:GOLD`, `xyz:SILVER` | **推荐**，可读性强 |
| `@{index}` | `@182`, `@156` | 数字索引 |

常用 xyz 市场：
| 符号 | 价格 |
|------|------|
| `xyz:GOLD` | ~$5168 |
| `xyz:SILVER` | ~$107 |
| `xyz:COPPER` | ~$6 |
| `xyz:PLATINUM` | ~$2421 |

### 使用方式

```bash
# runbot.py 直接使用 xyz:GOLD 格式
python runbot.py --exchange hyperliquid --ticker "xyz:GOLD" ...
```

```python
# SDK 直接下单
result = exchange.order("xyz:GOLD", True, 0.001, 5160.0, {"limit": {"tif": "Alo"}})
```

### SDK 配置 (重要!)

> [!CAUTION]
> Builder perps (xyz:GOLD 等) 需要特殊处理，SDK 默认不支持！

#### 1. 初始化 - 传入 perp_dexs 参数
```python
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info

# ❌ 这样 xyz:GOLD 下单会报错
exchange = Exchange(wallet, url, account_address=addr)

# ✅ 必须传入 perp_dexs
exchange = Exchange(
    wallet, url, 
    account_address=addr,
    perp_dexs=["xyz"]  # 关键！
)
info = Info(url, skip_ws=True, perp_dexs=["xyz"])
```

#### 2. 查询 API - 必须传 dex 参数
SDK 的 Info 方法不支持 builder perps，必须直接调用 REST API 并传入 `dex` 参数：

```python
import requests

# ❌ SDK 方法不支持 builder perps
info.l2_snapshot("xyz:GOLD")      # KeyError
info.user_state(address)          # 返回空
info.open_orders(address)         # 返回空

# ✅ 必须直接调用 API 并传入 dex 参数
url = "https://api.hyperliquid.xyz/info"

# L2 orderbook
resp = requests.post(url, json={"type": "l2Book", "coin": "xyz:GOLD"})

# Positions (clearinghouseState)
resp = requests.post(url, json={
    "type": "clearinghouseState", 
    "user": address, 
    "dex": "xyz"  # 关键！
})

# Open orders
resp = requests.post(url, json={
    "type": "openOrders", 
    "user": address, 
    "dex": "xyz"  # 关键！
})
```

#### 3. Side 映射
Builder perps API 返回的 side 格式：
#### 4. 常见错误处理

**"Post only order would have immediately matched"**
- **原因**: 使用 ALO (Post Only) 下单时，价格穿过对手价（即试图吃单）。
- **处理**: 
    - 不要当做 fatal error 处理
    - 应该捕获此错误并重试（可能需要调整价格或等待）
    - 错误消息不一定包含 "crossed"，必须检查 "post order" 或 "immediately matched" 关键字

**Position Mismatch**
- **原因**: 
    1. 平仓单下单失败（如 Post Only 失败）且未及时重试
    2. WebSocket 更新延迟
    3. `clearinghouseState` 查询未传 `dex` 参数导致仓位显示 0
- **处理**:
    - 确保下单失败有完善的重试机制
    - 确保 `get_account_positions` 和 `get_active_orders` 在使用 builder perps 时传入 `dex` 参数

---

## Rate Limits

**IP 级别 (每分钟 1200 权重):**
- Exchange API: 1 + floor(batch_len / 40)
- Info API: 2-60 (视请求类型)

**地址级别:**
- 起始配额: 10,000 请求
- 补充: 每 1 USDC 交易量 = 1 请求
- 被限制时: 每 10 秒 1 请求

**WebSocket:**
- 最大连接: 100
- 最大订阅: 1000
- 消息速率: 2000/分钟

---

## 常见问题

### Q: 下单返回 `{"error": "User does not exist"}`
**A:** 账户需要先入金才能交易。在 Testnet 可使用 Faucet。

### Q: 如何获取正确的 Asset ID?
```python
meta = info.meta()
for i, asset in enumerate(meta["universe"]):
    print(f"{asset['name']}: {i}")
```

### Q: 价格精度问题?
使用 SDK 的 `float_to_wire` 或参考 tick size:
```python
from hyperliquid.utils import float_to_wire
px = float_to_wire(2500.0, sz_decimals)
```

### Q: WebSocket 断线重连?
SDK 内置自动重连。手动处理:
```python
info = Info(url, skip_ws=False)
# SDK 会自动处理断线重连
---

## 实测经验 (2026-01-30)

### Info API 测试结果 (9/9 PASS)

| 方法 | 结果 | 备注 |
|------|------|------|
| `all_mids()` | ✅ | 返回 505 个交易对 |
| `meta()` | ✅ | 返回 228 个永续合约 |
| `spot_meta()` | ✅ | 435 tokens, 260 pairs |
| `l2_snapshot()` | ✅ | 20 档深度 |
| `user_state()` | ✅ | 返回账户状态 |
| `open_orders()` | ✅ | - |
| `user_fills()` | ✅ | - |
| `user_rate_limit()` | ✅ | 初始 10,000 请求配额 |
| `candles_snapshot()` | ✅ | - |

### WebSocket 测试结果 (6/6 PASS)

| 订阅 | 结果 | 备注 |
|------|------|------|
| `allMids` | ✅ | 约每秒更新 |
| `bbo` | ✅ | 高频更新 |
| `l2Book` | ✅ | 20 档深度 |
| `trades` | ✅ | 实时成交流 |
| `orderUpdates` | ✅ | 无订单时返回空 |
| `userFills` | ✅ | 初始返回 snapshot |

### 关键发现

1. **API 钱包 vs 主账户**: `secret_key` 是 API 钱包私钥，但 `account_address` 必须是主账户地址
2. **无余额限制**: 账户需要入金才能下单，查询 `user_state().accountValue == 0` 时无法交易
3. **BBO 数据格式**: `{bid: {px, sz, n}, ask: {px, sz, n}}`，n 是订单数量
4. **L2 Book**: 固定返回 20 档，格式 `{px, sz, n}`
5. **最小订单金额**: 订单价值必须 >= $10，否则报错 `Order must have minimum value of $10`
6. **cloid 格式**: 32 字符 hex 字符串，如 `0x00000000000000000000019c0df4c71b`

### 订单测试结果 (4/4 PASS)

| 测试 | 结果 | 备注 |
|------|------|------|
| `limit_order_gtc` | ✅ | 下单 -> 查询 -> 撤单 流程正常 |
| `limit_order_alo` | ✅ | Post Only 订单正常 |
| `bulk_orders` | ✅ | 批量下单/撤单正常 |
| `order_with_cloid` | ✅ | 带客户端订单ID下单/撤单正常 |

### 测试脚本

测试脚本位于 `tests/` 目录：
- `test_info_api.py` - Info API 测试 (无需签名)
- `test_websocket.py` - WebSocket 订阅测试
- `test_orders.py` - 订单操作测试 (需要余额)

运行方式：
```bash
# Info API (无需配置)
python tests/test_info_api.py

# Order tests (需要环境变量)
HYPERLIQUID_API=0x... HYPERLIQUID_API_ADDRESS=0x... python tests/test_orders.py
```

---

## 客户端开发经验 (HyperliquidClient)

### API 响应结构

**`query_order_by_oid` 响应:**
```json
{
  "status": "order",
  "order": {
    "order": {
      "coin": "ETH",
      "side": "B",  // B=Buy, A=Sell
      "limitPx": "2745.5",
      "sz": "0.0",  // 剩余数量
      "origSz": "0.01",  // 原始数量
      "oid": 306389343798,
      "tif": "Alo"
    },
    "status": "filled",  // open/filled/canceled
    "statusTimestamp": 1769761246736
  }
}
```

### 关键实现细节

1. **Side 映射**: API 用 `B`/`A` 表示 buy/sell
2. **嵌套结构**: `order.order` 包含订单详情，`order.status` 是状态
3. **剩余数量**: `sz` 是剩余，`origSz` 是原始，filled = origSz - sz
4. **Tick Size**: 根据价格动态设置 (>10000=1, >100=0.1, >1=0.01, else=0.0001)
5. **Post Only**: 使用 `{"limit": {"tif": "Alo"}}` 确保 maker 订单

### 环境变量

```bash
HYPERLIQUID_API_SECRET_KEY=0x...  # API 钱包私钥
HYPERLIQUID_API_ADDRESS=0x...     # 主账户地址 (非 API 钱包地址!)
HYPERLIQUID_TESTNET=false         # 可选，使用 testnet
```

---

## 资源链接

- [官方文档](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api)
- [Python SDK](https://github.com/hyperliquid-dex/hyperliquid-python-sdk)
- [API Wallet 生成](https://app.hyperliquid.xyz/API)
- [Testnet Faucet](https://app.hyperliquid-testnet.xyz/faucet)

