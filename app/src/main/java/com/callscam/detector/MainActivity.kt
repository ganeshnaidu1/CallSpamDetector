package com.callscam.detector

import android.Manifest
import android.content.Intent
import android.content.SharedPreferences
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.util.Log
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat

class MainActivity : AppCompatActivity() {
    private val TAG = "SpamDetector"

    private val requiredPermissions = arrayOf(
        Manifest.permission.RECORD_AUDIO,
        Manifest.permission.READ_PHONE_STATE,
        Manifest.permission.READ_CALL_LOG
    )

    private val requestPermissions = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val allGranted = permissions.entries.all { it.value }
        if (!allGranted) {
            showPermissionRationale()
        } else {
            checkAndRequestAccessibilityService()
        }
    }

    private lateinit var serverUrlInput: EditText
    private lateinit var statusText: TextView
    private lateinit var startServerButton: Button
    private lateinit var prefs: SharedPreferences

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        Log.d(TAG, "onCreate: Starting MainActivity")
        
        try {
            Log.d(TAG, "Setting content view...")
            setContentView(R.layout.activity_main)
            Log.d(TAG, "Content view set successfully")
            
            Log.d(TAG, "Initializing SharedPreferences...")
            prefs = getSharedPreferences("SpamDetector", MODE_PRIVATE)
            Log.d(TAG, "SharedPreferences initialized")
            
            try {
                Log.d(TAG, "Finding views...")
                serverUrlInput = findViewById(R.id.server_url_input)
                statusText = findViewById(R.id.status_text)
                startServerButton = findViewById(R.id.start_server_button)
                Log.d(TAG, "All views found successfully")
            } catch (e: Exception) {
                Log.e(TAG, "Error finding views: ${e.message}", e)
                showError("Error initializing UI: ${e.message}")
                finish()
                return
            }
            
            try {
                Log.d(TAG, "Loading saved URL...")
                val savedUrl = prefs.getString("server_url", "ws://10.0.2.2:8765/stream")
                serverUrlInput.setText(savedUrl)
                Log.d(TAG, "URL loaded: $savedUrl")
            } catch (e: Exception) {
                Log.e(TAG, "Error loading URL: ${e.message}", e)
                // Continue even if URL loading fails
            }
            
            try {
                Log.d(TAG, "Setting up button click listener...")
                startServerButton.setOnClickListener {
                    try {
                        Log.d(TAG, "Save button clicked")
                        saveServerUrl()
                        statusText.text = "Server URL saved: ${serverUrlInput.text}"
                    } catch (e: Exception) {
                        Log.e(TAG, "Error in startServerButton click: ${e.message}", e)
                        showError("Error saving URL: ${e.message}")
                    }
                }
                Log.d(TAG, "Button click listener set up")
            } catch (e: Exception) {
                Log.e(TAG, "Error setting up button listener: ${e.message}", e)
                showError("Error setting up UI: ${e.message}")
                finish()
                return
            }
            
            try {
                Log.d(TAG, "Ensuring permissions...")
                ensurePermissions()
            } catch (e: Exception) {
                Log.e(TAG, "Error ensuring permissions: ${e.message}", e)
                showError("Error checking permissions: ${e.message}")
                // Don't finish here, let the app continue
            }
            
            Log.d(TAG, "MainActivity setup completed successfully")
        } catch (e: Exception) {
            Log.e(TAG, "Critical error in onCreate: ${e.message}", e)
            try {
                showError("Critical error: ${e.message}")
            } catch (e2: Exception) {
                Log.e(TAG, "Failed to show error dialog: ${e2.message}", e2)
            }
            finish()
        }
    }

    override fun onResume() {
        super.onResume()
        // Check permissions again when the app comes back to foreground
        if (hasAllRequiredPermissions()) {
            checkAndRequestAccessibilityService()
        }
    }

    private fun ensurePermissions() {
        try {
            Log.d(TAG, "Checking permissions")
            if (!hasAllRequiredPermissions()) {
                Log.d(TAG, "Not all permissions granted, requesting...")
                // Check if we should show rationale
                val shouldShowRationale = requiredPermissions.any {
                    shouldShowRequestPermissionRationale(it)
                }
                
                if (shouldShowRationale) {
                    Log.d(TAG, "Showing permission rationale")
                    showPermissionRationale()
                } else {
                    Log.d(TAG, "Requesting permissions directly")
                    requestPermissions()
                }
            } else {
                Log.d(TAG, "All permissions granted, checking accessibility service")
                checkAndRequestAccessibilityService()
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error in ensurePermissions: ${e.message}", e)
            showError("Error checking permissions: ${e.message}")
        }
    }

    private fun hasAllRequiredPermissions(): Boolean {
        return try {
            requiredPermissions.all {
                val granted = ContextCompat.checkSelfPermission(this, it) == PackageManager.PERMISSION_GRANTED
                Log.d(TAG, "Permission $it granted: $granted")
                granted
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error checking permissions: ${e.message}", e)
            false
        }
    }

    private fun requestPermissions() {
        requestPermissions.launch(requiredPermissions)
    }

    private fun showPermissionRationale() {
        AlertDialog.Builder(this)
            .setTitle("Permissions Required")
            .setMessage("This app needs the following permissions to function properly:\n\n" +
                    "• Microphone - To record and analyze call audio\n" +
                    "• Phone - To detect incoming/outgoing calls\n" +
                    "• Call Log - To identify spam numbers")
            .setPositiveButton("Grant Permissions") { _, _ ->
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M && 
                    !shouldShowRequestPermissionRationale(Manifest.permission.READ_PHONE_STATE)) {
                    // User checked 'Don't ask again', take them to settings
                    val intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
                        data = Uri.fromParts("package", packageName, null)
                    }
                    startActivity(intent)
                } else {
                    requestPermissions()
                }
            }
            .setNegativeButton("Cancel") { dialog, _ ->
                dialog.dismiss()
                Toast.makeText(this, "App may not function properly without permissions", 
                    Toast.LENGTH_LONG).show()
            }
            .setCancelable(false)
            .show()
    }

    private fun checkAndRequestAccessibilityService() {
        // Check if accessibility service is enabled
        val enabledServices = Settings.Secure.getString(
            contentResolver,
            Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
        )

        if (enabledServices != null && enabledServices.contains(packageName)) {
            // Accessibility service is enabled
            statusText.text = "Service is running"
        } else {
            // Show dialog to enable accessibility service
            showAccessibilityServiceDialog()
        }
    }

    private fun showAccessibilityServiceDialog() {
        AlertDialog.Builder(this)
            .setTitle("Enable Accessibility Service")
            .setMessage("Please enable the Spam Detector accessibility service to detect calls.")
            .setPositiveButton("Enable") { _, _ ->
                startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
            }
            .setNegativeButton("Later") { dialog, _ ->
                dialog.dismiss()
                Toast.makeText(this, "You can enable it later in Settings", 
                    Toast.LENGTH_SHORT).show()
            }
            .setCancelable(false)
            .show()
    }
    
    private fun saveServerUrl() {
        try {
            val url = serverUrlInput.text.toString()
            prefs.edit().putString("server_url", url).apply()
            Log.d(TAG, "Server URL saved: $url")
        } catch (e: Exception) {
            Log.e(TAG, "Error saving server URL: ${e.message}", e)
            throw e
        }
    }
    
    private fun showError(message: String) {
        runOnUiThread {
            try {
                AlertDialog.Builder(this)
                    .setTitle("Error")
                    .setMessage(message)
                    .setPositiveButton("OK") { dialog, _ -> dialog.dismiss() }
                    .show()
            } catch (e: Exception) {
                // If UI thread is not ready, show toast instead
                Toast.makeText(this, "Error: $message", Toast.LENGTH_LONG).show()
            }
        }
    }
}


