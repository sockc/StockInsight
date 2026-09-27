package com.tianxian.stockinsight.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val StockInsightColors = darkColorScheme(
    primary = Color(0xFF89E6A5),
    onPrimary = Color(0xFF05210F),
    primaryContainer = Color(0xFF173A23),
    onPrimaryContainer = Color(0xFFB5F4C6),
    secondary = Color(0xFFA9D7B5),
    background = Color(0xFF0D1712),
    onBackground = Color(0xFFE4EEE7),
    surface = Color(0xFF121F18),
    onSurface = Color(0xFFE4EEE7),
    surfaceVariant = Color(0xFF1B2A21),
    onSurfaceVariant = Color(0xFFB8C7BD),
    error = Color(0xFFFFB4AB),
    outline = Color(0xFF728278)
)

@Composable
fun StockInsightTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = StockInsightColors,
        content = content
    )
}
