package com.tianxian.stockinsight.model

data class PredictionHorizon(
    val horizon: String,
    val upProbability: Double,
    val expectedReturnPct: Double,
    val backtestAccuracy: Double,
    val sampleSize: Int,
    val confidence: String = "low"
)

data class MarketContextItem(
    val symbol: String,
    val name: String,
    val changePct: Double,
    val relativeToArmPct: Double? = null,
    val note: String = ""
)

data class TechnicalSummary(
    val rsi14: Double,
    val volumeRatio20: Double,
    val volatility20AnnualizedPct: Double,
    val return5dPct: Double,
    val return20dPct: Double,
    val ma20: Double,
    val ma50: Double,
    val ma100: Double,
    val ma200: Double
)

data class KeyLevels(
    val resistance: List<Double>,
    val support: List<Double>
)

data class OverviewResponse(
    val symbol: String,
    val name: String,
    val currency: String,
    val price: Double,
    val changePct: Double,
    val asOf: String,
    val dataMode: String,
    val statusText: String,
    val predictions: List<PredictionHorizon>,
    val marketContext: List<MarketContextItem>,
    val technicals: TechnicalSummary,
    val keyLevels: KeyLevels,
    val notices: List<String> = emptyList()
)

data class EventItem(
    val id: String,
    val time: String,
    val type: String,
    val title: String,
    val summary: String,
    val importance: String,
    val source: String? = null,
    val affectedSymbols: List<String> = emptyList(),
    val reaction1dPct: Double? = null,
    val reaction5dPct: Double? = null,
    val sectorRelative1dPct: Double? = null
)

data class EventsResponse(
    val symbol: String,
    val items: List<EventItem>,
    val dataMode: String
)

data class BacktestItem(
    val horizon: String,
    val tests: Int,
    val accuracy: Double,
    val highConfidenceTests: Int,
    val highConfidenceAccuracy: Double?,
    val brierScore: Double?,
    val baselineAccuracy: Double? = null,
    val baselineBrierScore: Double? = null,
    val nonOverlappingTests: Int = 0,
    val nonOverlappingAccuracy: Double? = null
)

data class BacktestResponse(
    val symbol: String,
    val items: List<BacktestItem>,
    val note: String,
    val dataMode: String
)

data class PolicyCategory(
    val key: String,
    val name: String,
    val status: String,
    val explanation: String
)

data class PolicyResponse(
    val symbol: String,
    val categories: List<PolicyCategory>,
    val recentEvents: List<EventItem>,
    val dataMode: String,
    val note: String
)
