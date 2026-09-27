# Architecture

```text
Android APK
   |
   | HTTPS JSON
   v
FastAPI Analysis Server
   |-- Market data provider (V0.1: yfinance prototype)
   |-- Feature engine
   |-- Similar-state model
   |-- Walk-forward validator
   |-- Event / policy service
   |
   +--> PostgreSQL
        |-- events
        |-- event_reactions
        +-- policy_exposure
```

## Design rule

APK 是展示和交互层；行情源、模型、政策规则和回测全部放在服务器。以后更换行情供应商或算法时无需重新设计 APK 数据模型。

## Event model

```text
event
  -> event_reaction
  -> policy_exposure
```

事件和市场反应必须分开存储。事件的“好/坏”不直接等于股价后续反应。
