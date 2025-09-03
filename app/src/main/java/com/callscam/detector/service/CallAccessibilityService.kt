package com.callscam.detector.service

import android.accessibilityservice.AccessibilityService
import android.content.Intent
import android.os.Handler
import android.os.Looper
import android.telephony.TelephonyManager
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import com.callscam.detector.MainActivity
import com.callscam.detector.SpamDetectorApp

class CallAccessibilityService : AccessibilityService() {
    private val TAG = "CallAccessibility"
    private var lastCallState = TelephonyManager.CALL_STATE_IDLE
    private val handler = Handler(Looper.getMainLooper())
    private var isRecording = false

    override fun onServiceConnected() {
        super.onServiceConnected()
        Log.d(TAG, "Accessibility service connected")
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent) {
        when (event.eventType) {
            AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED -> {
                val className = event.className?.toString() ?: return
                
                // Handle call screen state changes
                when {
                    className.contains("InCallActivity") -> {
                        Log.d(TAG, "Call screen opened")
                        startCallRecording()
                    }
                    className.contains("InCallScreen") -> {
                        Log.d(TAG, "In call screen detected")
                        startCallRecording()
                    }
                }
            }
            AccessibilityEvent.TYPE_NOTIFICATION_STATE_CHANGED -> {
                // Handle call notifications
                val text = event.text.joinToString(" ")
                if (text.contains("call") || text.contains("Call")) {
                    Log.d(TAG, "Call notification detected: $text")
                    startCallRecording()
                }
            }
        }
    }

    private fun startCallRecording() {
        if (isRecording) return
        
        Log.d(TAG, "Starting call recording service")
        val intent = Intent(this, CallRecordingService::class.java).apply {
            action = CallRecordingService.ACTION_START_RECORDING
        }
        startService(intent)
        isRecording = true
        
        // Schedule a check to stop recording if not already stopped
        handler.postDelayed({
            if (isRecording) {
                stopCallRecording()
            }
        }, 5 * 60 * 1000) // Stop after 5 minutes if not stopped already
    }

    private fun stopCallRecording() {
        if (!isRecording) return
        
        Log.d(TAG, "Stopping call recording service")
        val intent = Intent(this, CallRecordingService::class.java).apply {
            action = CallRecordingService.ACTION_STOP_RECORDING
        }
        startService(intent)
        isRecording = false
    }

    override fun onInterrupt() {
        Log.d(TAG, "Accessibility service interrupted")
        stopCallRecording()
    }

    override fun onDestroy() {
        super.onDestroy()
        Log.d(TAG, "Accessibility service destroyed")
        stopCallRecording()
        handler.removeCallbacksAndMessages(null)
    }

    companion object {
        fun initializeSpamDetector(context: android.content.Context): Boolean {
            // This is a placeholder for any initialization needed for the spam detector
            // In a real implementation, this would initialize any required models or services
            return true
        }
    }
}
