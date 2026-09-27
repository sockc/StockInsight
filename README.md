# StockInsight 股析 V0.1

ARM-first 美股分析 APK + FastAPI 分析服务器原型。

> 当前版本的目标不是给出“必涨/必跌”结论，而是把历史状态、市场环境、事件、政策和样本外回测统一起来。预测概率必须和历史样本外准确率一起展示。

## V0.1 已包含

### Android APK

- 包名：`com.tianxian.stockinsight`
- Android：Kotlin + Jetpack Compose
- 页面：首页 / 行情 / 事件 / 模型 / 设置
- ARM 首页：价格、1/5/10/20 日概率、回测命中率、技术状态、关键价位
- 市场环境：QQQ / SMH / NVDA / AMD / SPY
- 事件与政策：已预留事件反应和政策分类
- 后端不可用时自动进入内置演示数据，不影响首次安装验证
- 设置页可填写自己的 HTTPS API 地址

### Analysis Server

- FastAPI + PostgreSQL（可选）
- 原型行情源：`yfinance`
- ARM + QQQ + SMH + NVDA + AMD + SPY 历史日线
- RSI、均线、成交量倍率、历史波动率
- 历史相似状态 KNN
- 1 / 5 / 10 / 20 日概率
- Walk-forward 样本外回测
- `events` / `event_reactions` / `policy_exposure` 数据库表
- 政策分类：出口限制、关税、AI监管、美联储/利率、半导体补贴

`yfinance` 仅用于第一版验证算法与数据链路。正式长期使用建议换成有授权、稳定 SLA 的行情/新闻数据源。

---

# GitHub 直接构建 APK

仓库已经包含 GitHub Actions：

- `.github/workflows/build-debug.yml`：push 到 `main/master` 自动编译 Debug APK，不需要签名 Secret。
- `.github/workflows/build-release.yml`：手动运行或推送 `v*` 标签时编译**固定签名 Release APK**。
- `.github/workflows/server-test.yml`：后端单元测试。

## 1. 固定包名

当前：

```text
com.tianxian.stockinsight
```

正式开始使用后尽量不要改包名。

## 2. 固定签名：JKS 只创建一次

### Windows PowerShell

在仓库目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\generate-keystore.ps1
```

脚本会生成：

```text
stockinsight-release.jks
stockinsight-release.jks.base64.txt
```

**不要把这两个文件提交到 Git。** `.gitignore` 已经阻止常见 keystore 文件进入仓库。

请把 JKS 和密码至少备份到两个安全位置。丢失固定签名后，已经安装的正式 APK 将无法用新签名直接覆盖升级。


### 已提供的固定签名包

如果你使用本次一并提供的 `StockInsight-Signing-KeepPrivate.zip`，**不要再运行生成脚本创建另一把正式签名**。解压后按照其中 `github-secrets.txt` 的四项值填写 GitHub Repository Secrets，并把 `stockinsight-release.jks` 做离线备份。签名包永远不要上传到仓库。

## 3. 添加 GitHub Repository Secrets

仓库 → `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

必须创建：

```text
SIGNING_KEY_BASE64
SIGNING_STORE_PASSWORD
SIGNING_KEY_ALIAS
SIGNING_KEY_PASSWORD
```

其中：

```text
SIGNING_KEY_BASE64
```

填入：

```text
stockinsight-release.jks.base64.txt
```

整个文件的一行内容。

默认脚本 Alias：

```text
stockinsight
```

因此：

```text
SIGNING_KEY_ALIAS=stockinsight
```

其余两个密码填创建 JKS 时输入的密码。

Release 工作流只要缺少任意一个 Secret 就直接失败，不会生成临时签名 APK。

## 4. 构建正式 APK

进入：

```text
GitHub → Actions → Build Signed Release APK → Run workflow
```

构建成功后，在该次 Actions 的 `Artifacts` 下载：

```text
StockInsight-signed-release
```

里面包括：

```text
StockInsight-*.apk
signature.txt
SHA256SUMS.txt
```

`signature.txt` 会保存 APK 的签名证书信息。以后每一版都应该保持同一个证书 SHA-256 指纹。V0.1 已固定为：

```text
5D:19:74:AB:CB:0D:B5:C8:D7:25:0C:02:39:71:37:FC:1A:35:4F:0C:9E:2C:3F:35:BD:79:6C:D9:66:C9:88:64
```

Release 工作流会强制比对此指纹；即使 GitHub Secrets 被误换成另一把 JKS，也会直接构建失败，避免签名悄悄变化。

如果推送标签：

```bash
git tag v0.1.0
git push origin v0.1.0
```

工作流还会自动创建/更新 GitHub Release，并上传 APK、签名信息和 SHA256。

---

# 服务器快速部署

先修改 `docker-compose.yml` 里的 PostgreSQL 密码，然后：

```bash
docker compose up -d --build
```

检查：

```bash
curl http://127.0.0.1:8787/api/v1/health
```

预期：

```json
{"ok":true,"version":"0.1.0"}
```

ARM 首页接口：

```bash
curl http://127.0.0.1:8787/api/v1/stocks/ARM/overview
```

Swagger：

```text
http://服务器IP:8787/docs
```

实际给 APK 使用时建议通过 Nginx / Caddy / Cloudflare 暴露 HTTPS，例如：

```text
https://stock.example.com/
```

然后在 APK → 设置 → `API Base URL` 填入该地址。

Android 正式版默认不允许普通公网 HTTP 明文请求。

---

# API V0.1

```text
GET /api/v1/health
GET /api/v1/stocks/ARM/overview
GET /api/v1/stocks/ARM/candles?limit=120
GET /api/v1/stocks/ARM/technical
GET /api/v1/stocks/ARM/market-context
GET /api/v1/stocks/ARM/prediction
GET /api/v1/stocks/ARM/backtest
GET /api/v1/stocks/ARM/events
GET /api/v1/stocks/ARM/policy
```

详细说明见 `docs/API.md`。

---

# V0.2 计划

下一版优先加入：

1. 新闻/政策真实数据源。
2. 财报实际值 vs 一致预期 vs 指引。
3. 事件发生后 5m / 30m / 1h / 1d / 5d / 10d / 20d 真实反应。
4. ARM 相对 SMH/QQQ 的超额反应，区分“板块一起跌”和“ARM独立异常”。
5. FOMC、CPI、PCE、非农、2Y/10Y 美债收益率、VIX、美元指数。
6. 期权 IV、Put/Call、OI。
7. 历史相似政策事件统计，不使用主观“利好 +10 / 利空 -10”评分。

