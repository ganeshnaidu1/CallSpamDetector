package com.callscam.detector.service

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import android.content.Intent
import com.callscam.detector.service.CallRecordingService

class CallAccessibilityService : AccessibilityService() {

    // Delegate recording to a foreground service for OS compliance

    companion object {
        private const val TAG = "CallAccessibilityService"
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        
        val info = AccessibilityServiceInfo().apply {
            eventTypes = AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED or
                        AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED
            feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC
            flags = AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS
            notificationTimeout = 100
        }
        
        serviceInfo = info
        Log.d(TAG, "Accessibility service connected")
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent) {
        when (event.eventType) {
            AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED -> {
                handleWindowStateChange(event)
            }
            AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED -> {
                handleWindowContentChange(event)
            }
        }
    }

    private fun handleWindowStateChange(event: AccessibilityEvent) {
        val className = event.className?.toString() ?: return
        
        when {
            className.contains("InCallScreen") -> {
                Log.d(TAG, "Call screen detected")
                val intent = Intent(this, CallRecordingService::class.java).apply {
                    action = CallRecordingService.ACTION_START
                }
                startForegroundService(intent)
            }
            className.contains("DialerActivity") -> {
                Log.d(TAG, "Dialer activity detected")
                val intent = Intent(this, CallRecordingService::class.java).apply {
                    action = CallRecordingService.ACTION_STOP
                }
                startService(intent)
            }
        }
    }

    private fun handleWindowContentChange(event: AccessibilityEvent) {
        // Handle content changes that might indicate call state
        val text = event.text?.joinToString(" ") ?: ""
        
        if (text.contains("Call ended", ignoreCase = true) || text.contains("Call disconnected", ignoreCase = true)) {
            Log.d(TAG, "Call ended detected")
            val intent = Intent(this, CallRecordingService::class.java).apply {
                action = CallRecordingService.ACTION_STOP
            }
            startService(intent)
        }
    }

    override fun onInterrupt() {
        Log.d(TAG, "Accessibility service interrupted")
    }

    override fun onDestroy() {
        super.onDestroy()
        Log.d(TAG, "Accessibility service destroyed")
    }
} 