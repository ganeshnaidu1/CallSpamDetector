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
            val filesDir = context.filesDir.absolutePath
            
            // Add necessary paths to Python path
            sys["path"]?.callAttr("append", cacheDir)
            sys["path"]?.callAttr("append", filesDir)
            
            // Set environment variables
            os["environ"]?.callAttr("__setitem__", "TORCH_HOME", filesDir)
            os["environ"]?.callAttr("__setitem__", "TRANSFORMERS_CACHE", "$filesDir/transformers")
            
            // Initialize Whisper module
            whisperModule = python.getModule("whisper_processor")
            
            isInitialized = true
            Log.d(TAG, "Whisper module initialized successfully")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to initialize Whisper module", e)
        }
    }

    suspend fun transcribeAudio(audioData: ByteArray, sampleRate: Int = SAMPLE_RATE): String {
        return withContext(Dispatchers.IO) {
            try {
                if (!isInitialized) {
                    Log.e(TAG, "Whisper module not initialized")
                    return@withContext ""
                }
                
                Log.d(TAG, "Starting transcription of ${audioData.size} bytes")
                
                // Convert to a format that can be passed to Python
                val pythonArray = python.builtins.callAttr("bytearray", audioData)
                
                // Call the Python function to process the audio
                val result = whisperModule.callAttr("process_audio_chunk", pythonArray, sampleRate)
                
                val transcription = result?.toString() ?: ""
                Log.d(TAG, "Transcription result: $transcription")
                return@withContext transcription
            } catch (e: Exception) {
                Log.e(TAG, "Error in transcription", e)
                return@withContext ""
            }
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
