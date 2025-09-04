package com.callscam.detector.audio

import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.util.Log
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow

class AudioProcessor {

    companion object {
        private const val TAG = "AudioProcessor"
        private const val SAMPLE_RATE = 16000
        private const val CHANNEL_CONFIG = AudioFormat.CHANNEL_IN_MONO
        private const val AUDIO_FORMAT = AudioFormat.ENCODING_PCM_16BIT
        private val BUFFER_SIZE = AudioRecord.getMinBufferSize(
            SAMPLE_RATE, CHANNEL_CONFIG, AUDIO_FORMAT
        ) * 2
    }

    private var audioRecord: AudioRecord? = null
    private var isRecording = false
    private var callStartTime: Long = 0

    fun startRecording() {
        if (isRecording) return
        
        try {
            // Try VOICE_COMMUNICATION first, fall back to MIC if needed
            audioRecord = try {
                AudioRecord.Builder()
                    .setAudioSource(MediaRecorder.AudioSource.VOICE_COMMUNICATION)
                    .setAudioFormat(
                        AudioFormat.Builder()
                            .setEncoding(AUDIO_FORMAT)
                            .setSampleRate(SAMPLE_RATE)
                            .setChannelMask(CHANNEL_CONFIG)
                            .build()
                    )
                    .setBufferSizeInBytes(BUFFER_SIZE)
                    .build()
            } catch (e: Exception) {
                Log.w(TAG, "VOICE_COMMUNICATION source failed, falling back to MIC", e)
                AudioRecord.Builder()
                    .setAudioSource(MediaRecorder.AudioSource.MIC)
                    .setAudioFormat(
                        AudioFormat.Builder()
                            .setEncoding(AUDIO_FORMAT)
                            .setSampleRate(SAMPLE_RATE)
                            .setChannelMask(CHANNEL_CONFIG)
                            .build()
                    )
                    .setBufferSizeInBytes(BUFFER_SIZE)
                    .build()
            }
            
            audioRecord?.startRecording()
            isRecording = true
            callStartTime = System.currentTimeMillis()
            
            Log.d(TAG, "Audio recording started")
            
        } catch (e: Exception) {
            Log.e(TAG, "Error starting audio recording", e)
        }
    }

    fun stopRecording() {
        if (!isRecording) return
        
        try {
            audioRecord?.stop()
            audioRecord?.release()
            audioRecord = null
            isRecording = false
            
            Log.d(TAG, "Audio recording stopped")
            
        } catch (e: Exception) {
            Log.e(TAG, "Error stopping audio recording", e)
        }
    }

    fun getNextAudioChunk(): ByteArray? {
        if (!isRecording || audioRecord == null) return null
        
        return try {
            val buffer = ByteArray(BUFFER_SIZE)
            val bytesRead = audioRecord?.read(buffer, 0, BUFFER_SIZE) ?: 0
            
            if (bytesRead > 0) {
                buffer.copyOf(bytesRead)
            } else {
                null
            }
            
        } catch (e: Exception) {
            Log.e(TAG, "Error reading audio chunk", e)
            null
        }
    }

    fun getCallDuration(): Long {
        return System.currentTimeMillis() - callStartTime
    }

    fun getAudioFlow(): Flow<ByteArray> = flow {
        while (isRecording) {
            val chunk = getNextAudioChunk()
            if (chunk != null) {
                emit(chunk)
            }
            kotlinx.coroutines.delay(50) // 50ms chunks
        }
    }
} 