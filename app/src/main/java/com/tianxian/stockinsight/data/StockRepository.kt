package com.tianxian.stockinsight.data

import android.content.Context
import com.google.gson.FieldNamingPolicy
import com.google.gson.GsonBuilder
import com.tianxian.stockinsight.model.*
import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

class StockRepository(context: Context) {
    private val settingsStore = SettingsStore(context)
    private val gson = GsonBuilder()
        .setFieldNamingPolicy(FieldNamingPolicy.LOWER_CASE_WITH_UNDERSCORES)
        .create()

    private fun apiOrNull(): ApiService? {
        val raw = settingsStore.getServerUrl().trim()
        if (raw.isBlank()) return null
        val url = if (raw.endsWith('/')) raw else raw + "/"
        if (!url.startsWith("https://") &&
            !url.startsWith("http://10.0.2.2") &&
            !url.startsWith("http://127.0.0.1")
        ) return null
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

    private fun lastVerifiedOverview(): OverviewResponse? {
        val json = settingsStore.getVerifiedOverviewJson() ?: return null
        val cached = runCatching { gson.fromJson(json, OverviewResponse::class.java) }.getOrNull()
            ?: return null
        if (cached.dataMode != "historical_delayed" && cached.dataMode != "historical_cache") {
            return null
        }
        return cached.copy(
            dataMode = "local_cache",
            statusText = "服务器不可用 · 本机最后一次真实历史行情截至 " + cached.asOf,
            notices = listOf("这是此前保存的真实行情，并非当前报价；联网恢复后请刷新。")
        )
    }

    suspend fun overview(symbol: String = "ARM"): OverviewResponse? {
        val api = apiOrNull() ?: return lastVerifiedOverview()
        val actual = runCatching { api.overview(symbol) }.getOrNull()
        if (actual != null &&
            (actual.dataMode == "historical_delayed" || actual.dataMode == "historical_cache")
        ) {
            settingsStore.saveVerifiedOverviewJson(gson.toJson(actual))
            return actual
        }
        if (actual?.dataMode == "live_delayed") {
            // Upgrade order is flexible: legacy backend values are shown as
            // historical daily data but never stored as a verified snapshot.
            return actual.copy(
                dataMode = "legacy_daily",
                statusText = "旧版服务端日线，尚未启用数据质量验证 · " + actual.statusText
            )
        }
        // Failed calls never manufacture a price or a fabricated model prediction.
        return lastVerifiedOverview()
    }

    suspend fun events(symbol: String = "ARM"): EventsResponse? =
        apiOrNull()?.let { api -> runCatching { api.events(symbol) }.getOrNull() }

    suspend fun backtest(symbol: String = "ARM"): BacktestResponse? =
        apiOrNull()?.let { api -> runCatching { api.backtest(symbol) }.getOrNull() }

    suspend fun policy(symbol: String = "ARM"): PolicyResponse? =
        apiOrNull()?.let { api -> runCatching { api.policy(symbol) }.getOrNull() }

    fun getServerUrl(): String = settingsStore.getServerUrl()
    fun setServerUrl(value: String) = settingsStore.setServerUrl(value)
}
