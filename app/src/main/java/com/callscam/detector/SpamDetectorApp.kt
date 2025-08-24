package com.callscam.detector

import android.app.Application
import android.util.Log

class SpamDetectorApp : Application() {
    override fun onCreate() {
        super.onCreate()
        Log.d("SpamDetector", "Application created")
    }
}
