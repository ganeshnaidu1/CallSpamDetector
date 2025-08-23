package com.callscam.detector

import android.Manifest
import android.content.SharedPreferences
import android.content.pm.PackageManager
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat

class MainActivity : AppCompatActivity() {

    private val requestPermissions = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { _ ->
        // No-op; user can enable Accessibility Service manually in settings
    }

    private lateinit var serverUrlInput: EditText
    private lateinit var statusText: TextView
    private lateinit var startServerButton: Button
    private lateinit var prefs: SharedPreferences

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Simple layout
        setContentView(R.layout.activity_main)
        
        prefs = getSharedPreferences("SpamDetector", MODE_PRIVATE)
        
        serverUrlInput = findViewById(R.id.server_url_input)
        statusText = findViewById(R.id.status_text)
        startServerButton = findViewById(R.id.start_server_button)
        
        // Load saved URL
        val savedUrl = prefs.getString("server_url", "ws://10.0.2.2:8765/stream")
        serverUrlInput.setText(savedUrl)
        
        startServerButton.setOnClickListener {
            saveServerUrl()
            statusText.text = "Server URL saved: ${serverUrlInput.text}"
        }
        
        ensurePermissions()
    }

    private fun ensurePermissions() {
        val needsRecord = ContextCompat.checkSelfPermission(
            this, Manifest.permission.RECORD_AUDIO
        ) != PackageManager.PERMISSION_GRANTED

        val permissions = mutableListOf<String>()
        if (needsRecord) permissions.add(Manifest.permission.RECORD_AUDIO)

        if (permissions.isNotEmpty()) {
            requestPermissions.launch(permissions.toTypedArray())
        }
    }
    
    private fun saveServerUrl() {
        val url = serverUrlInput.text.toString()
        prefs.edit().putString("server_url", url).apply()
    }
}


