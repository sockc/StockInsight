package com.tianxian.stockinsight.data

import com.tianxian.stockinsight.model.BacktestResponse
import com.tianxian.stockinsight.model.EventsResponse
import com.tianxian.stockinsight.model.OverviewResponse
import com.tianxian.stockinsight.model.PolicyResponse
import retrofit2.http.GET
import retrofit2.http.Path

interface ApiService {
    @GET("api/v1/stocks/{symbol}/overview")
    suspend fun overview(@Path("symbol") symbol: String): OverviewResponse

    @GET("api/v1/stocks/{symbol}/events")
    suspend fun events(@Path("symbol") symbol: String): EventsResponse

    @GET("api/v1/stocks/{symbol}/backtest")
    suspend fun backtest(@Path("symbol") symbol: String): BacktestResponse

    @GET("api/v1/stocks/{symbol}/policy")
    suspend fun policy(@Path("symbol") symbol: String): PolicyResponse
}
