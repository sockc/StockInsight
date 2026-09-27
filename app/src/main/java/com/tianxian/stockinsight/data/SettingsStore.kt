package com.tianxian.stockinsight.data

import android.content.Context

class SettingsStore(context: Context) {
    private val prefs = context.getSharedPreferences("stockinsight_settings", Context.MODE_PRIVATE)

    fun getServerUrl(): String = prefs.getString(KEY_SERVER_URL, "") ?: ""

    fun setServerUrl(value: String) {
        prefs.edit().putString(KEY_SERVER_URL, value.trim()).apply()
    }

    companion object {
        private const val KEY_SERVER_URL = "server_url"
    }
}
