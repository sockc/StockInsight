package com.tianxian.stockinsight.data

import android.content.Context

class SettingsStore(context: Context) {
    private val prefs = context.getSharedPreferences("stockinsight_settings", Context.MODE_PRIVATE)

    fun getServerUrl(): String = prefs.getString(KEY_SERVER_URL, "") ?: ""

    fun setServerUrl(value: String) {
        val next = value.trim()
        if (next != getServerUrl()) {
            prefs.edit().remove(KEY_LAST_VERIFIED_OVERVIEW).putString(KEY_SERVER_URL, next).apply()
        }
    }

    fun getVerifiedOverviewJson(): String? = prefs.getString(KEY_LAST_VERIFIED_OVERVIEW, null)

    fun saveVerifiedOverviewJson(json: String) {
        prefs.edit().putString(KEY_LAST_VERIFIED_OVERVIEW, json).apply()
    }

    companion object {
        private const val KEY_SERVER_URL = "server_url"
        private const val KEY_LAST_VERIFIED_OVERVIEW = "last_verified_overview"
    }
}
