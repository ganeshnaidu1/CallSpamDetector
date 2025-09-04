package com.callscam.detector.utils

import android.content.Context
import android.content.SharedPreferences

/**
 * Helper class for managing SharedPreferences in the application.
 * Provides easy access to common preference operations.
 */
object PreferenceHelper {
    
    private const val PREF_NAME = "SpamDetectorPrefs"
    
    // Preference keys
    private const val KEY_FIRST_RUN = "is_first_run"
    private const val KEY_SERVICE_ENABLED = "service_enabled"
    private const val KEY_AUTO_START = "auto_start"
    private const val KEY_SHOW_NOTIFICATIONS = "show_notifications"
    private const val KEY_VIBRATE_ON_DETECTION = "vibrate_on_detection"
    private const val KEY_LAST_PHONE_NUMBER = "last_phone_number"
    private const val KEY_LAST_ANALYSIS_RESULT = "last_analysis_result"
    
    /**
     * Get the SharedPreferences instance
     */
    fun getPreferences(context: Context): SharedPreferences {
        return context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE)
    }
    
    /**
     * Check if it's the first run of the app
     */
    fun isFirstRun(context: Context): Boolean {
        val prefs = getPreferences(context)
        val isFirstRun = prefs.getBoolean(KEY_FIRST_RUN, true)
        if (isFirstRun) {
            // Set it to false so next time it won't be the first run
            prefs.edit().putBoolean(KEY_FIRST_RUN, false).apply()
        }
        return isFirstRun
    }
    
    /**
     * Check if the service is enabled
     */
    fun isServiceEnabled(context: Context): Boolean {
        return getPreferences(context).getBoolean(KEY_SERVICE_ENABLED, false)
    }
    
    /**
     * Set whether the service is enabled
     */
    fun setServiceEnabled(context: Context, enabled: Boolean) {
        getPreferences(context).edit()
            .putBoolean(KEY_SERVICE_ENABLED, enabled)
            .apply()
    }
    
    /**
     * Check if auto-start is enabled
     */
    fun isAutoStartEnabled(context: Context): Boolean {
        return getPreferences(context).getBoolean(KEY_AUTO_START, true)
    }
    
    /**
     * Set whether auto-start is enabled
     */
    fun setAutoStartEnabled(context: Context, enabled: Boolean) {
        getPreferences(context).edit()
            .putBoolean(KEY_AUTO_START, enabled)
            .apply()
    }
    
    /**
     * Check if notifications are enabled
     */
    fun areNotificationsEnabled(context: Context): Boolean {
        return getPreferences(context).getBoolean(KEY_SHOW_NOTIFICATIONS, true)
    }
    
    /**
     * Set whether notifications are enabled
     */
    fun setNotificationsEnabled(context: Context, enabled: Boolean) {
        getPreferences(context).edit()
            .putBoolean(KEY_SHOW_NOTIFICATIONS, enabled)
            .apply()
    }
    
    /**
     * Check if vibration is enabled for detections
     */
    fun isVibrationEnabled(context: Context): Boolean {
        return getPreferences(context).getBoolean(KEY_VIBRATE_ON_DETECTION, true)
    }
    
    /**
     * Set whether vibration is enabled for detections
     */
    fun setVibrationEnabled(context: Context, enabled: Boolean) {
        getPreferences(context).edit()
            .putBoolean(KEY_VIBRATE_ON_DETECTION, enabled)
            .apply()
    }
    
    /**
     * Save the last analyzed phone number
     */
    fun saveLastPhoneNumber(context: Context, phoneNumber: String) {
        getPreferences(context).edit()
            .putString(KEY_LAST_PHONE_NUMBER, phoneNumber)
            .apply()
    }
    
    /**
     * Get the last analyzed phone number
     */
    fun getLastPhoneNumber(context: Context): String? {
        return getPreferences(context).getString(KEY_LAST_PHONE_NUMBER, null)
    }
    
    /**
     * Save the last analysis result
     */
    fun saveLastAnalysisResult(context: Context, isSpam: Boolean) {
        getPreferences(context).edit()
            .putBoolean(KEY_LAST_ANALYSIS_RESULT, isSpam)
            .apply()
    }
    
    /**
     * Get the last analysis result
     */
    fun getLastAnalysisResult(context: Context): Boolean {
        return getPreferences(context).getBoolean(KEY_LAST_ANALYSIS_RESULT, false)
    }
    
    /**
     * Clear all preferences (for logout or reset)
     */
    fun clearAll(context: Context) {
        getPreferences(context).edit().clear().apply()
    }
}
