package com.callscam.detector.api

import retrofit2.http.Body
import retrofit2.http.POST

interface ApiService {
    @POST("detect_spam")
    suspend fun detectSpam(@Body callData: CallData): SpamDetectionResult
}

data class CallData(
    val call_text: String,
    val call_duration: Double? = null,
    val caller_number: String? = null
)

data class SpamDetectionResult(
    val is_spam: Boolean,
    val confidence: Double,
    val keywords_found: List<String>
)
