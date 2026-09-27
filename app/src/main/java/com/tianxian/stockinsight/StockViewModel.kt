package com.tianxian.stockinsight

import android.app.Application
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.tianxian.stockinsight.data.StockRepository
import com.tianxian.stockinsight.model.*
import kotlinx.coroutines.async
import kotlinx.coroutines.launch


data class StockUiState(
    val loading: Boolean = true,
    val overview: OverviewResponse? = null,
    val events: EventsResponse? = null,
    val backtest: BacktestResponse? = null,
    val policy: PolicyResponse? = null,
    val serverUrl: String = "",
    val message: String? = null
)

class StockViewModel(application: Application) : AndroidViewModel(application) {
    private val repository = StockRepository(application)

    var state by mutableStateOf(StockUiState(serverUrl = repository.getServerUrl()))
        private set

    init {
        refresh()
    }

    fun refresh() {
        viewModelScope.launch {
            state = state.copy(loading = true, message = null)
            val overview = async { repository.overview("ARM") }
            val events = async { repository.events("ARM") }
            val backtest = async { repository.backtest("ARM") }
            val policy = async { repository.policy("ARM") }
            state = state.copy(
                loading = false,
                overview = overview.await(),
                events = events.await(),
                backtest = backtest.await(),
                policy = policy.await(),
                serverUrl = repository.getServerUrl()
            )
        }
    }

    fun saveServerUrl(url: String) {
        repository.setServerUrl(url)
        state = state.copy(serverUrl = url.trim(), message = "服务器地址已保存")
        refresh()
    }
}
