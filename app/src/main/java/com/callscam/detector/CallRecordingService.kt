package com.callscam.detector.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import com.callscam.detector.audio.AudioProcessor
import com.callscam.detector.net.WebSocketSender

class CallRecordingService : Service() {

    companion object {
        const val CHANNEL_ID = "call_recording_channel"
        const val NOTIFICATION_ID = 1001
        const val ACTION_START = "com.callscam.detector.action.START_RECORDING"
        const val ACTION_STOP = "com.callscam.detector.action.STOP_RECORDING"
    }

    private val audioProcessor = AudioProcessor()
    private var wsSender: WebSocketSender? = null

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_START -> startRecording()
            ACTION_STOP -> stopRecordingAndStop()
        }
        return START_STICKY
    }

    private fun startRecording() {
        createNotificationChannel()
        val notification = buildNotification("Recording call audio")
        startForeground(NOTIFICATION_ID, notification)
        
        // Connect to Python server
        val wsUrl = intent?.getStringExtra("WS_URL") ?: "ws://10.0.2.2:8765/stream"
        wsSender = WebSocketSender(wsUrl).also { it.connect() }
        
        audioProcessor.startRecording()
    }

    private fun stopRecordingAndStop() {
        wsSender?.close()
        audioProcessor.stopRecording()
        if (Build.VERSION.SDK_INT >= 24) {
            stopForeground(STOP_FOREGROUND_REMOVE)
        } else {
            @Suppress("DEPRECATION")
            stopForeground(true)
        }
        stopSelf()
    }

    override fun onDestroy() {
        wsSender?.close()
        audioProcessor.stopRecording()
        super.onDestroy()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Call Recording",
                NotificationManager.IMPORTANCE_LOW
            )
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(channel)
        }
    }

    private fun buildNotification(content: String): Notification {
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("Spam Detector")
            .setContentText(content)
            .setSmallIcon(android.R.drawable.ic_btn_speak_now)
            .setOngoing(true)
            .build()
    }
}


