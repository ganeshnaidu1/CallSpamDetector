package com.callscam.detector.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.media.AudioManager
import android.media.MediaRecorder
import android.os.Build
import android.os.IBinder
import android.os.VibrationEffect
import android.os.Vibrator
import android.telephony.TelephonyManager
import android.util.Log
import androidx.core.app.NotificationCompat
import com.callscam.detector.MainActivity
import com.callscam.detector.R
import com.callscam.detector.audio.AudioProcessor
import com.callscam.detector.audio.WhisperHelper
import com.chaquo.python.PyObject
import com.chaquo.python.Python
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.collect
import java.io.ByteArrayInputStream
import java.io.File
import java.io.FileOutputStream

class CallRecordingService : Service() {
    private val CHANNEL_ID = "CallRecordingServiceChannel"
    private val NOTIFICATION_ID = 1
    private val TAG = "CallRecordingService"
    private val SCOPE = CoroutineScope(Dispatchers.IO + Job())

    private lateinit var audioProcessor: AudioProcessor
    private lateinit var whisperHelper: WhisperHelper
    private var transcriptionJob: Job? = null
    private var spamDetectionJob: Job? = null
    private var isSpam = false
    private val transcriptionBuffer = StringBuilder()
    
// Audio recording parameters
    private val SAMPLE_RATE = 16000
    private val CHANNEL_CONFIG = android.media.AudioFormat.CHANNEL_IN_MONO
    private val AUDIO_FORMAT = android.media.AudioFormat.ENCODING_PCM_16BIT
    private val BUFFER_SIZE = android.media.AudioRecord.getMinBufferSize(
        SAMPLE_RATE, 
        CHANNEL_CONFIG, 
        AUDIO_FORMAT
    )
    
    private var audioRecord: android.media.AudioRecord? = null
    private val audioManager by lazy { getSystemService(Context.AUDIO_SERVICE) as AudioManager }
    private val vibrator by lazy { getSystemService(Context.VIBRATOR_SERVICE) as Vibrator }
    private val notificationManager by lazy { getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager }

    override fun onCreate() {
        super.onCreate()
        audioProcessor = AudioProcessor()
        whisperHelper = WhisperHelper(this)
        createNotificationChannel()
        
        // Initialize AudioRecord
        audioRecord = try {
            android.media.AudioRecord.Builder()
                .setAudioSource(MediaRecorder.AudioSource.VOICE_COMMUNICATION)
                .setAudioFormat(
                    android.media.AudioFormat.Builder()
                        .setEncoding(AUDIO_FORMAT)
                        .setSampleRate(SAMPLE_RATE)
                        .setChannelMask(CHANNEL_CONFIG)
                        .build()
                )
                .setBufferSizeInBytes(BUFFER_SIZE)
                .build()
        } catch (e: Exception) {
            Log.e(TAG, "Error initializing AudioRecord", e)
            null
        }
        
        // Set up audio for call monitoring
        setupAudioForCall()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_START_RECORDING -> startRecording()
            ACTION_STOP_RECORDING -> stopRecordingAndStop()
            else -> return START_NOT_STICKY
        }
        return START_STICKY
    }

    private fun setupAudioForCall() {
        // Set audio mode for call recording
        audioManager.mode = AudioManager.MODE_IN_CALL
        audioManager.isSpeakerphoneOn = true
        audioManager.isMicrophoneMute = false
    }

    private fun startRecording() {
        if (transcriptionJob?.isActive == true) return
        
        startForeground(NOTIFICATION_ID, buildNotification("Monitoring call..."))
        audioProcessor.startRecording()
        
        // Start processing audio chunks
        transcriptionJob = SCOPE.launch {
            audioProcessor.getAudioFlow().collect { audioChunk ->
                try {
                    // Process audio chunk for transcription
                    val transcription = whisperHelper.transcribeAudio(audioChunk)
                    
                    if (transcription.isNotEmpty()) {
                        Log.d(TAG, "Transcription: $transcription")
                        withContext(Dispatchers.Main) {
                            updateNotification("Listening: ${transcription.take(30)}...")
                        }
                        
                        // Buffer transcriptions for spam detection
                        transcriptionBuffer.append(transcription).append(" ")
                        
                        // Check for spam if we have enough text
                        if (transcriptionBuffer.length > 50) {
                            checkForSpam(transcriptionBuffer.toString())
                            // Keep a reasonable buffer size
                            if (transcriptionBuffer.length > 1000) {
                                transcriptionBuffer.delete(0, 500)
                            }
                        }
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "Error in transcription flow", e)
                }
            }
        }
    }
    
    private fun checkForSpam(text: String) {
        if (spamDetectionJob?.isActive == true) return
        
        spamDetectionJob = SCOPE.launch {
            try {
                // Call Python spam detection
                val python = Python.getInstance()
                val pyModule = python.getModule("spam_detector")
                val result = pyModule.callAttr("is_spam", text)?.toBoolean() ?: false
                
                if (result) {
                    Log.d(TAG, "SPAM DETECTED!")
                    isSpam = true
                    triggerSpamAlert()
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error in spam detection", e)
            }
        }
    }
    
    private fun triggerSpamAlert() {
        // Vibrate to alert user
        if (Build.VERSION.SDK_INT >= 26) {
            vibrator.vibrate(
                VibrationEffect.createWaveform(
                    longArrayOf(0, 200, 100, 200, 100, 200), 
                    -1
                )
            )
        } else {
            @Suppress("DEPRECATION")
            vibrator.vibrate(500)
        }
        
        // Update notification
        updateNotification("⚠️ Potential spam call detected!")
    }

    private fun stopRecordingAndStop() {
        try {
            transcriptionJob?.cancel()
            spamDetectionJob?.cancel()
            audioProcessor.stopRecording()
            
            // Reset audio mode
            audioManager.mode = AudioManager.MODE_NORMAL
            
            if (Build.VERSION.SDK_INT >= 24) {
                stopForeground(STOP_FOREGROUND_REMOVE)
            } else {
                @Suppress("DEPRECATION")
                stopForeground(true)
            }
            stopSelf()
        } catch (e: Exception) {
            Log.e(TAG, "Error stopping recording", e)
        }
    }

    override fun onDestroy() {
        SCOPE.cancel()
        audioProcessor.stopRecording()
        super.onDestroy()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val serviceChannel = NotificationChannel(
                CHANNEL_ID,
                "Call Monitoring Service",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Shows when call monitoring is active"
            }
            notificationManager.createNotificationChannel(serviceChannel)
        }
    }
    
    private fun updateNotification(text: String) {
        val notification = buildNotification(text)
        notificationManager.notify(NOTIFICATION_ID, notification)
    }

    private fun buildNotification(text: String): Notification {
        val notificationIntent = Intent(this, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            this, 0, notificationIntent,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle(if (isSpam) "⚠️ Spam Detected!" else "Call Monitor Active")
            .setContentText(text)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .build()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    companion object {
        const val ACTION_START_RECORDING = "ACTION_START_RECORDING"
        const val ACTION_STOP_RECORDING = "ACTION_STOP_RECORDING"
        
        fun startService(context: Context) {
            val intent = Intent(context, CallRecordingService::class.java).apply {
                action = ACTION_START_RECORDING
            }
            context.startService(intent)
        }
        
        fun stopService(context: Context) {
            val intent = Intent(context, CallRecordingService::class.java).apply {
                action = ACTION_STOP_RECORDING
            }
            context.startService(intent)
        }
    }
}
