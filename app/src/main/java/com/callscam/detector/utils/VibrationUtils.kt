package com.callscam.detector.utils

import android.content.Context
import android.os.Vibrator
import android.os.VibratorManager
import android.os.Build

object VibrationUtils {
    private const val VIBRATION_PATTERN_START_DELAY = 0
    private val VIBRATION_PATTERN = longArrayOf(0, 500, 200, 500, 200, 500) // Vibrate 3 times with 200ms intervals
    private const val VIBRATION_AMPLITUDE = 255 // Max amplitude

    fun vibrateForSpam(context: Context) {
        val vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            val vibratorManager = context.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as VibratorManager
            vibratorManager.defaultVibrator
        } else {
            @Suppress("DEPRECATION")
            context.getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
        }

        if (vibrator.hasVibrator()) {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                // Use the newer vibrate method with amplitude control on API 26+
                vibrator.vibrate(
                    android.os.VibrationEffect.createWaveform(
                        VIBRATION_PATTERN,
                        -1 // Don't repeat
                    )
                )
            } else {
                // Fallback for older versions
                @Suppress("DEPRECATION")
                vibrator.vibrate(VIBRATION_PATTERN, -1)
            }
        }
    }
}
