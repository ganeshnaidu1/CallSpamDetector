package com.callscam.detector.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import com.callscam.detector.service.CallRecordingService
import com.callscam.detector.utils.PreferenceHelper

/**
 * Receiver that starts the necessary services when the device boots up.
 * This is registered in the AndroidManifest.xml to receive the BOOT_COMPLETED intent.
 */
class BootCompletedReceiver : BroadcastReceiver() {
    
    companion object {
        private const val TAG = "BootCompletedReceiver"
    }
    
    override fun onReceive(context: Context, intent: Intent?) {
        if (intent?.action == Intent.ACTION_BOOT_COMPLETED || 
            intent?.action == "android.intent.action.QUICKBOOT_POWERON") {
            
            Log.d(TAG, "Boot completed received, checking if service should start")
            
            // Check if auto-start is enabled in preferences
            val prefs = PreferenceHelper.getPreferences(context)
            val autoStart = prefs.getBoolean("pref_auto_start", true)
            
            if (autoStart) {
                Log.i(TAG, "Auto-start is enabled, starting services...")
                // Start the call recording service
                val serviceIntent = Intent(context, CallRecordingService::class.java).apply {
                    action = CallRecordingService.ACTION_START_RECORDING
                }
                context.startForegroundService(serviceIntent)
            } else {
                Log.d(TAG, "Auto-start is disabled, not starting services")
            }
        }
    }
}
