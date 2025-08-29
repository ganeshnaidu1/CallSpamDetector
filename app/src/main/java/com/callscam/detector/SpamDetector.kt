package com.callscam.detector

import android.content.Context
import com.callscam.detector.utils.VibrationUtils
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException
import kotlin.coroutines.suspendCoroutine

class SpamDetector(private val context: Context) {
    
    private val python = Python.getInstance()
    private var isInitialized = false
    
    init {
        // Initialize Python environment if not already initialized
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(context))
        }
    }
    
    suspend fun initialize(): Boolean = withContext(Dispatchers.IO) {
        try {
            // Initialize the Python analyzer
            val module = python.getModule("llm_analyzer")
            val analyzer = module.callAttr("LLMAnalyzer")
            analyzer.callAttr("initialize")
            isInitialized = true
            true
        } catch (e: Exception) {
            e.printStackTrace()
            false
        }
    }
    
    suspend fun analyzeConversation(text: String): AnalysisResult = withContext(Dispatchers.IO) {
        if (!isInitialized) {
            throw IllegalStateException("SpamDetector not initialized. Call initialize() first.")
        }
        
        try {
            val module = python.getModule("llm_analyzer")
            val analyzer = module.callAttr("LLMAnalyzer")
            val result = analyzer.callAttr("analyze_conversation", text)
            
            // Convert Python dict to Kotlin object
            val resultJson = result.toString()
            val json = JSONObject(resultJson)
            
            AnalysisResult(
                isSuspicious = json.getBoolean("is_suspicious"),
                confidence = json.getDouble("confidence").toFloat(),
                reasoning = json.getString("reasoning"),
                timestamp = json.optString("timestamp", "")
            )
        } catch (e: Exception) {
            e.printStackTrace()
            throw e
        }
    }
    
    fun onSpamDetected() {
        // Trigger vibration pattern for spam detection
        VibrationUtils.vibrateForSpam(context)
        
        // You can add additional spam handling logic here
        // For example, show a notification, log the event, etc.
    }
    
    suspend fun isSpam(conversationText: String): Boolean {
        val result = analyzeConversation(conversationText)
        return result.isSuspicious && result.confidence > 0.7f
    }
    
    data class AnalysisResult(
        val isSuspicious: Boolean,
        val confidence: Float,
        val reasoning: String,
        val timestamp: String
    )
}
