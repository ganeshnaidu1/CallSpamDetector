package com.callscam.detector.audio

import android.content.Context
import android.util.Log
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class WhisperHelper(private val context: Context) {
    private val TAG = "WhisperHelper"
    private var isInitialized = false
    private val python = Python.getInstance()
    private lateinit var whisperModule: com.chaquo.python.PyObject
    
    // Audio parameters - must match Python side
    private val SAMPLE_RATE = 16000
    private val CHUNK_SIZE_MS = 3000 // Process 3-second chunks
    private val SAMPLES_PER_CHUNK = SAMPLE_RATE * CHUNK_SIZE_MS / 1000
    
    init {
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(context))
        }
        initialize()
    }

    private fun initialize() {
        try {
            // Initialize Python modules
            val sys = python.getModule("sys")
            val os = python.getModule("os")
            
            // Set up paths
            val cacheDir = context.cacheDir.absolutePath
            sys.get("path").callAttr("append", cacheDir)
            
            // Initialize Whisper module
            whisperModule = python.getModule("whisper_processor")
            
            // Initialize the model
            whisperModule.callAttr("initialize")
            
            isInitialized = true
            Log.d(TAG, "Whisper module initialized successfully")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to initialize Whisper module", e)
        }
    }

    suspend fun transcribeAudio(audioData: ByteArray): String = withContext(Dispatchers.IO) {
        if (!isInitialized) {
            Log.e(TAG, "Whisper module not initialized")
            return@withContext ""
        }

        return@withContext try {
            // Convert byte array to Python bytes
            val pyBytes = python.builtins.callAttr("bytes", audioData.toList())
            
            // Call Python function to process audio chunk
            val result = whisperModule.callAttr("process_audio_chunk", pyBytes, SAMPLE_RATE)
            
            // Convert result to string and clean up
            val transcription = result?.toString()?.trim() ?: ""
            
            if (transcription.isNotEmpty()) {
                Log.d(TAG, "Transcription: $transcription")
            }
            
            transcription
        } catch (e: Exception) {
            Log.e(TAG, "Error in speech-to-text conversion", e)
            ""
        }
    }
    
    fun release() {
        try {
            if (isInitialized) {
                whisperModule.callAttr("cleanup")
                isInitialized = false
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error cleaning up Whisper module", e)
        }
    }
}
