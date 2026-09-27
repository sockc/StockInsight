package com.tianxian.stockinsight.data

import android.content.Context
import com.google.gson.FieldNamingPolicy
import com.google.gson.GsonBuilder
import com.tianxian.stockinsight.model.*
import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

class StockRepository(private val context: Context) {
    private val settingsStore = SettingsStore(context)

    private fun apiOrNull(): ApiService? {
        val raw = settingsStore.getServerUrl().trim()
        if (raw.isBlank()) return null
        val url = if (raw.endsWith('/')) raw else "$raw/"
        if (!url.startsWith("https://") && !url.startsWith("http://10.0.2.2") && !url.startsWith("http://127.0.0.1")) {
            return null
        }

        val gson = GsonBuilder()
            .setFieldNamingPolicy(FieldNamingPolicy.LOWER_CASE_WITH_UNDERSCORES)
            .create()
        val client = OkHttpClient.Builder()
            .connectTimeout(8, TimeUnit.SECONDS)
            .readTimeout(12, TimeUnit.SECONDS)
            .callTimeout(15, TimeUnit.SECONDS)
            .build()

        return Retrofit.Builder()
            .baseUrl(url)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create(gson))
            .build()
            .create(ApiService::class.java)
    }

    suspend fun overview(symbol: String = "ARM"): OverviewResponse {
        val api = apiOrNull() ?: return DemoData.overview()
        return runCatching { api.overview(symbol) }.getOrElse {
            DemoData.overview(
                status = "服务器连接失败，已切换演示数据",
                notice = "请在设置页检查 HTTPS 服务器地址。"
            )
        }
    }

    suspend fun events(symbol: String = "ARM"): EventsResponse {
        val api = apiOrNull() ?: return DemoData.events()
        return runCatching { api.events(symbol) }.getOrElse { DemoData.events() }
    }

    suspend fun backtest(symbol: String = "ARM"): BacktestResponse {
        val api = apiOrNull() ?: return DemoData.backtest()
        return runCatching { api.backtest(symbol) }.getOrElse { DemoData.backtest() }
    }

    suspend fun policy(symbol: String = "ARM"): PolicyResponse {
        val api = apiOrNull() ?: return DemoData.policy()
        return runCatching { api.policy(symbol) }.getOrElse { DemoData.policy() }
    }

    fun getServerUrl(): String = settingsStore.getServerUrl()
    fun setServerUrl(value: String) = settingsStore.setServerUrl(value)
}

object DemoData {
    fun overview(
        status: String = "演示模式 · 快照 2026-09-25",
        notice: String = "这是内置演示快照；配置服务器后自动切换实时/历史计算结果。"
    ) = OverviewResponse(
        symbol = "ARM",
        name = "Arm Holdings",
        currency = "USD",
        price = 310.32,
        changePct = 1.30,
        asOf = "2026-09-25",
        dataMode = "demo",
        statusText = status,
        predictions = listOf(
            PredictionHorizon("1D", 49.5, 0.79, 52.2, 410, "low"),
            PredictionHorizon("5D", 45.1, 0.46, 50.0, 406, "low"),
            PredictionHorizon("10D", 60.8, 6.61, 50.4, 401, "low"),
            PredictionHorizon("20D", 55.6, 6.24, 50.1, 391, "low")
        ),
        marketContext = listOf(
            MarketContextItem("QQQ", "Nasdaq-100 ETF", 0.0, null, "待服务器实时计算"),
            MarketContextItem("SMH", "Semiconductor ETF", 0.0, null, "待服务器实时计算"),
            MarketContextItem("NVDA", "NVIDIA", 0.0, null, "待服务器实时计算"),
            MarketContextItem("AMD", "AMD", 0.0, null, "待服务器实时计算"),
            MarketContextItem("SPY", "S&P 500 ETF", 0.0, null, "待服务器实时计算")
        ),
        technicals = TechnicalSummary(
            rsi14 = 65.9,
            volumeRatio20 = 1.32,
            volatility20AnnualizedPct = 88.8,
            return5dPct = 12.59,
            return20dPct = 21.59,
            ma20 = 268.03,
            ma50 = 264.32,
            ma100 = 289.68,
            ma200 = 211.83
        ),
        keyLevels = KeyLevels(
            resistance = listOf(325.0, 337.0),
            support = listOf(303.0, 293.0, 290.0, 268.0)
        ),
        notices = listOf(
            notice,
            "概率不是确定性预测；优先查看样本外回测准确率与样本数量。"
        )
    )

    fun events() = EventsResponse(
        symbol = "ARM",
        dataMode = "demo",
        items = listOf(
            EventItem(
                id = "module-policy",
                time = "V0.2",
                type = "POLICY",
                title = "政策事件自动采集",
                summary = "预留出口限制、关税、AI监管、半导体补贴与美联储政策分类。",
                importance = "planned"
            ),
            EventItem(
                id = "module-earnings",
                time = "V0.2",
                type = "EARNINGS",
                title = "财报预期差与市场反应",
                summary = "将记录营收/EPS/指引超预期幅度及1日、5日、20日真实反应。",
                importance = "planned"
            )
        )
    )

    fun backtest() = BacktestResponse(
        symbol = "ARM",
        dataMode = "demo",
        note = "Walk-forward 演示结果。方向准确率接近随机水平，当前模型只能用于状态识别，不能作为单独交易依据。",
        items = listOf(
            BacktestItem("1D", 410, 52.2, 144, 52.1, 0.259),
            BacktestItem("5D", 406, 50.0, 160, 45.6, 0.269),
            BacktestItem("10D", 401, 50.4, 226, 52.2, 0.268),
            BacktestItem("20D", 391, 50.1, 213, 49.3, 0.272)
        )
    )

    fun policy() = PolicyResponse(
        symbol = "ARM",
        dataMode = "demo",
        note = "V0.1 只建立政策分类与接口。V0.2 开始接入真实事件源，并用市场实际反应估计影响。",
        categories = listOf(
            PolicyCategory("export_control", "半导体出口限制", "待接入", "追踪对客户、地区与供应链的直接/间接影响"),
            PolicyCategory("tariff", "关税与贸易政策", "待接入", "追踪成本、需求与风险偏好传导"),
            PolicyCategory("ai_regulation", "AI监管", "待接入", "追踪数据中心、模型训练与芯片需求传导"),
            PolicyCategory("fed", "美联储与利率", "待接入", "统计利率/收益率变化时高估值成长股的历史反应"),
            PolicyCategory("subsidy", "半导体补贴", "待接入", "追踪产业投资与客户资本开支影响")
        ),
        recentEvents = emptyList()
    )
}
