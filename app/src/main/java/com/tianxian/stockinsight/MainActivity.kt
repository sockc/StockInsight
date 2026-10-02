package com.tianxian.stockinsight

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.tianxian.stockinsight.model.*
import com.tianxian.stockinsight.ui.StockInsightTheme
import java.util.Locale

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            StockInsightTheme {
                val vm: StockViewModel = viewModel()
                StockInsightApp(vm)
            }
        }
    }
}

private enum class AppTab(val label: String, val glyph: String) {
    HOME("首页", "首"),
    MARKET("行情", "行"),
    EVENTS("事件", "事"),
    MODEL("模型", "模"),
    SETTINGS("设置", "设")
}

@Composable
private fun StockInsightApp(vm: StockViewModel) {
    var tab by remember { mutableStateOf(AppTab.HOME) }
    val state = vm.state

    Scaffold(
        topBar = {
            Surface(tonalElevation = 2.dp) {
                Row(
                    modifier = Modifier.fillMaxWidth().padding(horizontal = 18.dp, vertical = 14.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text("StockInsight 股析", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                        Text("ARM 单股验证版 V0.15", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                    TextButton(onClick = vm::refresh) { Text("刷新") }
                }
            }
        },
        bottomBar = {
            NavigationBar {
                AppTab.entries.forEach { item ->
                    NavigationBarItem(
                        selected = tab == item,
                        onClick = { tab = item },
                        icon = { Text(item.glyph, fontWeight = FontWeight.Bold) },
                        label = { Text(item.label) }
                    )
                }
            }
        }
    ) { padding ->
        Box(modifier = Modifier.fillMaxSize().padding(padding)) {
            if (state.loading && state.overview == null) {
                CircularProgressIndicator(modifier = Modifier.align(Alignment.Center))
            } else {
                when (tab) {
                    AppTab.HOME -> HomeScreen(state.overview, state.message)
                    AppTab.MARKET -> MarketScreen(state.overview)
                    AppTab.EVENTS -> EventsScreen(state.events, state.policy)
                    AppTab.MODEL -> ModelScreen(state.overview, state.backtest)
                    AppTab.SETTINGS -> SettingsScreen(state.serverUrl, vm::saveServerUrl)
                }
            }
            if (state.loading && state.overview != null) {
                LinearProgressIndicator(modifier = Modifier.fillMaxWidth().align(Alignment.TopCenter))
            }
        }
    }
}

@Composable
private fun HomeScreen(overview: OverviewResponse?, message: String?) {
    if (overview == null) { EmptyState(message ?: "暂无可验证的真实行情，请在设置中连接服务器。"); return }
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item {
            ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Text("${overview.symbol} · ${overview.name}", style = MaterialTheme.typography.titleMedium)
                            Text("\$${money(overview.price)}", style = MaterialTheme.typography.headlineLarge, fontWeight = FontWeight.Bold)
                        }
                        AssistChip(
                            onClick = {},
                            label = { Text(when (overview.dataMode) {
                                "historical_delayed" -> "历史日线"
                                "historical_cache" -> "服务器缓存"
                                "local_cache" -> "本机旧缓存"
                                "legacy_daily" -> "旧版日线"
                                else -> "数据状态未知"
                            }) }
                        )
                    }
                    Text(
                        signedPct(overview.changePct),
                        color = if (overview.changePct >= 0) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.error,
                        style = MaterialTheme.typography.titleMedium
                    )
                    Text(overview.statusText, color = MaterialTheme.colorScheme.onSurfaceVariant, style = MaterialTheme.typography.bodySmall)
                }
            }
        }

        item { SectionTitle("历史相似样本上涨占比 · 未校准") }
        item {
            LazyRow(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                items(overview.predictions) { p -> PredictionCard(p) }
            }
        }

        item { SectionTitle("技术状态") }
        item {
            ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    MetricLine("RSI(14)", one(overview.technicals.rsi14))
                    MetricLine("20日成交量倍率", "${two(overview.technicals.volumeRatio20)}×")
                    MetricLine("20日年化波动率", pct(overview.technicals.volatility20AnnualizedPct))
                    MetricLine("5日涨跌", signedPct(overview.technicals.return5dPct))
                    MetricLine("20日涨跌", signedPct(overview.technicals.return20dPct))
                    MetricLine("MA20 / MA50", "\$${money(overview.technicals.ma20)} / \$${money(overview.technicals.ma50)}")
                    MetricLine("MA100 / MA200", "\$${money(overview.technicals.ma100)} / \$${money(overview.technicals.ma200)}")
                }
            }
        }

        item { SectionTitle("关键价位") }
        item {
            ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    MetricLine("压力", overview.keyLevels.resistance.joinToString(" · ") { "\$${money(it)}" })
                    MetricLine("支撑", overview.keyLevels.support.joinToString(" · ") { "\$${money(it)}" })
                }
            }
        }

        items(overview.notices) { notice ->
            Text("• $notice", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@Composable
private fun PredictionCard(item: PredictionHorizon) {
    ElevatedCard(modifier = Modifier.width(150.dp)) {
        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
            Text(item.horizon, style = MaterialTheme.typography.labelLarge)
            Text("↑ ${one(item.upProbability)}%", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
            Text("期望 ${signedPct(item.expectedReturnPct)}", style = MaterialTheme.typography.bodySmall)
            HorizontalDivider()
            Text("样本外 ${one(item.backtestAccuracy)}%", style = MaterialTheme.typography.bodySmall)
            Text("n=${item.sampleSize} · ${if (item.confidence == "low") "低置信" else item.confidence}", color = MaterialTheme.colorScheme.onSurfaceVariant, style = MaterialTheme.typography.labelSmall)
        }
    }
}

@Composable
private fun MarketScreen(overview: OverviewResponse?) {
    if (overview == null) { EmptyState("真实市场数据不可用，请在设置中连接服务器。"); return }
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        item {
            Text("市场环境", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
            Text("用大盘、半导体板块和关联股解释 ARM 的涨跌是否属于独立行情。", color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        items(overview.marketContext) { item ->
            ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f)) {
                        Text(item.symbol, fontWeight = FontWeight.Bold)
                        Text(item.name, color = MaterialTheme.colorScheme.onSurfaceVariant, style = MaterialTheme.typography.bodySmall)
                        if (item.note.isNotBlank()) Text(item.note, color = MaterialTheme.colorScheme.onSurfaceVariant, style = MaterialTheme.typography.labelSmall)
                    }
                    Text(signedPct(item.changePct), fontWeight = FontWeight.SemiBold)
                }
            }
        }
    }
}

@Composable
private fun EventsScreen(events: EventsResponse?, policy: PolicyResponse?) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        item {
            Text("事件与政策", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
            Text("事件本身和事件后的真实市场反应分开记录。", color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        if (events == null) item {
            Text("事件数据暂时不可用；不会用计划中的事件冒充实时新闻。",
                color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        events?.items?.let { list ->
            items(list) { event -> EventCard(event) }
        }
        if (policy != null) {
            item { SectionTitle("政策分类") }
            items(policy.categories) { p ->
                ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(p.name, modifier = Modifier.weight(1f), fontWeight = FontWeight.SemiBold)
                            AssistChip(onClick = {}, label = { Text(p.status) })
                        }
                        Text(p.explanation, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
            }
            item { Text(policy.note, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant) }
        }
    }
}

@Composable
private fun EventCard(event: EventItem) {
    ElevatedCard(modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
            Row {
                Text(event.type, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.primary)
                Spacer(Modifier.weight(1f))
                Text(event.time, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            Text(event.title, fontWeight = FontWeight.SemiBold)
            Text(event.summary, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            if (event.reaction1dPct != null || event.reaction5dPct != null) {
                HorizontalDivider()
                Text("1日 ${event.reaction1dPct?.let(::signedPct) ?: "--"} · 5日 ${event.reaction5dPct?.let(::signedPct) ?: "--"}", style = MaterialTheme.typography.bodySmall)
            }
        }
    }
}

@Composable
private fun ModelScreen(overview: OverviewResponse?, backtest: BacktestResponse?) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        item {
            Text("模型验证", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
            Text("预测当天只能使用此前已发生的数据，避免未来数据泄漏。", color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        backtest?.items?.let { rows ->
            items(rows) { row ->
                ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Row {
                            Text(row.horizon, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
                            Text("命中 ${one(row.accuracy)}%")
                        }
                        MetricLine("测试次数", row.tests.toString())
                        MetricLine("高置信样本", row.highConfidenceTests.toString())
                        MetricLine("高置信命中", row.highConfidenceAccuracy?.let { "${one(it)}%" } ?: "--")
                        MetricLine("模型 Brier", row.brierScore?.let(::three) ?: "--")
                        MetricLine("历史上涨率基准", row.baselineAccuracy?.let { one(it) + "%" } ?: "--")
                        MetricLine("基准 Brier", row.baselineBrierScore?.let(::three) ?: "--")
                        MetricLine("不重叠样本数", row.nonOverlappingTests.toString())
                        MetricLine("不重叠命中率", row.nonOverlappingAccuracy?.let { one(it) + "%" } ?: "--")
                    }
                }
            }
        }
        if (backtest != null) item {
            Text(backtest.note, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        } else item {
            Text("当前无法获取真实回测数据。", color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        if (overview != null) item {
            Text("历史相似样本（未经校准）", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
        }
        overview?.predictions?.let { predictions ->
            items(predictions) { p ->
                MetricLine("${p.horizon} 历史上涨占比", "${one(p.upProbability)}% · 样本外 ${one(p.backtestAccuracy)}%")
            }
        }
    }
}

@Composable
private fun SettingsScreen(currentUrl: String, onSave: (String) -> Unit) {
    var url by remember(currentUrl) { mutableStateOf(currentUrl) }
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item {
            Text("服务器设置", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
            Text("留空仅显示此前验证过的真实缓存；没有缓存时不显示行情。推荐使用 HTTPS，例如 https://stock.example.com/", color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        item {
            OutlinedTextField(
                value = url,
                onValueChange = { url = it },
                label = { Text("API Base URL") },
                placeholder = { Text("https://stock.example.com/") },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Uri),
                singleLine = true,
                modifier = Modifier.fillMaxWidth()
            )
        }
        item {
            Button(onClick = { onSave(url) }, modifier = Modifier.fillMaxWidth()) { Text("保存并刷新") }
        }
        item {
            ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text("V0.1 数据范围", fontWeight = FontWeight.Bold)
                    Text("ARM + QQQ + SMH + NVDA + AMD + SPY", style = MaterialTheme.typography.bodySmall)
                    Text("V0.2：新闻、财报、政策事件与事件后市场反应。", style = MaterialTheme.typography.bodySmall)
                    Text("Release APK 由 GitHub Actions 使用固定 JKS 签名。", style = MaterialTheme.typography.bodySmall)
                }
            }
        }
    }
}

@Composable
private fun EmptyState(message: String) {
    Box(Modifier.fillMaxSize().padding(24.dp), contentAlignment = Alignment.Center) {
        Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text("暂无真实行情", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
            Text(message, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text("切换到底部「设置」检查服务器地址后刷新。",
                color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@Composable
private fun SectionTitle(text: String) {
    Text(text, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
}

@Composable
private fun MetricLine(label: String, value: String) {
    Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        Text(label, modifier = Modifier.weight(1f), color = MaterialTheme.colorScheme.onSurfaceVariant)
        Text(value, fontWeight = FontWeight.SemiBold)
    }
}

private fun one(v: Double) = String.format(Locale.US, "%.1f", v)
private fun two(v: Double) = String.format(Locale.US, "%.2f", v)
private fun three(v: Double) = String.format(Locale.US, "%.3f", v)
private fun money(v: Double) = String.format(Locale.US, "%.2f", v)
private fun pct(v: Double) = "${one(v)}%"
private fun signedPct(v: Double) = String.format(Locale.US, "%+.2f%%", v)
