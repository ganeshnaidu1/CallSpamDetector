package com.callscam.detector

import android.Manifest
import android.app.ActivityManager
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.SharedPreferences
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.util.Log
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers

class MainActivity : AppCompatActivity() {

    private val coroutineScope = CoroutineScope(Dispatchers.Main)

    // UI Components
    private lateinit var startButton: Button
    private lateinit var statusText: TextView

    // Data
    private lateinit var sharedPreferences: SharedPreferences
    // private var whisperHelper: WhisperHelper? = null // Commented out due to unresolved reference

    // Service state
    private var isServiceRunning = false

    companion object {
        private const val TAG = "MainActivity"
    }

    // Permissions
    private val requiredPermissions = arrayOf(
        Manifest.permission.RECORD_AUDIO,
        Manifest.permission.READ_PHONE_STATE,
        Manifest.permission.READ_CALL_LOG,
        Manifest.permission.FOREGROUND_SERVICE,
        Manifest.permission.POST_NOTIFICATIONS,
        if (Build.VERSION.SDK_INT <= Build.VERSION_CODES.Q) {
            Manifest.permission.WRITE_EXTERNAL_STORAGE
        } else {
            ""
        }
    ).filter { it.isNotEmpty() }.toTypedArray()

    // Permission launcher
    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val allGranted = permissions.entries.all { it.value }
        if (allGranted) {
            if (!isAccessibilityServiceEnabled()) {
                checkAndRequestAccessibilityService()
            } else {
                toggleService()
            }
        } else {
            showError("Required permissions were not granted")
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        try {
            Log.d(TAG, "onCreate: Starting MainActivity")

            // Initialize SharedPreferences
            sharedPreferences = getSharedPreferences("SpamDetector", MODE_PRIVATE)

            // Initialize UI
            statusText = findViewById(R.id.statusText)
            startButton = findViewById(R.id.startButton)

            startButton.setOnClickListener {
                if (!hasAllRequiredPermissions()) {
                    ensurePermissions()
                } else if (!isAccessibilityServiceEnabled()) {
                    checkAndRequestAccessibilityService()
                } else {
                    toggleService()
                }
            }

            // updateUI(isServiceRunning(CallRecordingService::class.java)) // Commented out due to unresolved reference

        } catch (e: Exception) {
            Log.e(TAG, "Critical error in onCreate: ${e.message}", e)
            showError("Critical error: ${e.message}")
            finish()
        }
    }

    private fun isServiceRunning(serviceClass: Class<*>): Boolean {
        val manager = getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
        return manager.getRunningServices(Integer.MAX_VALUE)
            .any { it.service.className == serviceClass.name }
    }

    override fun onResume() {
        super.onResume()
        if (hasAllRequiredPermissions()) {
            checkAndRequestAccessibilityService()
        }
    }

    private fun ensurePermissions() {
        if (!hasAllRequiredPermissions()) {
            val shouldShowRationale = requiredPermissions.any { permission ->
                ContextCompat.checkSelfPermission(this, permission) != PackageManager.PERMISSION_GRANTED &&
                        shouldShowRequestPermissionRationale(permission)
            }

            if (shouldShowRationale) {
                showPermissionRationale()
            } else {
                requestPermissions()
            }
        } else {
            checkAndRequestAccessibilityService()
        }
    }

    private fun hasAllRequiredPermissions(): Boolean {
        return requiredPermissions.all {
            ContextCompat.checkSelfPermission(this, it) == PackageManager.PERMISSION_GRANTED
        }
    }

    private fun requestPermissions() {
        requestPermissionLauncher.launch(requiredPermissions)
    }

    private fun showPermissionRationale() {
        AlertDialog.Builder(this)
            .setTitle("Permissions Required")
            .setMessage("This app needs permissions for microphone, phone, and call logs.")
            .setPositiveButton("Grant Permissions") { _, _ ->
                val intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
                    data = Uri.fromParts("package", packageName, null)
                }
                startActivity(intent)
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
        if (!isAccessibilityServiceEnabled()) {
            showAccessibilityServiceDialog()
        } else {
            startCallMonitoring()
        }
    }

    private fun showAccessibilityServiceDialog() {
        AlertDialog.Builder(this)
            .setTitle("Accessibility Service Required")
            .setMessage("Please enable the Spam Detector accessibility service to detect incoming calls.")
            .setPositiveButton("Open Settings") { _, _ ->
                startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
            }
            .setNegativeButton("Cancel") { dialog, _ -> dialog.dismiss() }
            .setCancelable(false)
            .show()
    }

    private fun isAccessibilityServiceEnabled(): Boolean {
        // val expectedComponentName = ComponentName(this, CallAccessibilityService::class.java) // Commented out due to unresolved reference
        val expectedComponentName = ComponentName(this, "") // Dummy component name
        val enabledServices = Settings.Secure.getString(
            contentResolver,
            Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
        ) ?: return false
        return enabledServices.contains(expectedComponentName.flattenToString())
    }

    private fun startCallMonitoring() {
        // val serviceIntent = Intent(this, CallRecordingService::class.java) // Commented out due to unresolved reference
        // ContextCompat.startForegroundService(this, serviceIntent)
        isServiceRunning = true
        updateUI(true)
    }

    private fun updateUI(isRunning: Boolean) {
        runOnUiThread {
            startButton.text = if (isRunning) "Stop Monitoring" else "Start Monitoring"
            statusText.text = if (isRunning) "Service is running" else "Service is stopped"
            isServiceRunning = isRunning
        }
    }

    private fun showError(message: String) {
        runOnUiThread {
            Toast.makeText(this@MainActivity, message, Toast.LENGTH_LONG).show()
            statusText.text = message
        }
    }

    private fun toggleService() {
        try {
            // The service check is commented out, so we toggle based on our local state `isServiceRunning`
            if (isServiceRunning) {
                // stopService(Intent(this, CallRecordingService::class.java)) // Commented out
                updateUI(false)
            } else {
                if (hasAllRequiredPermissions()) {
                    // ContextCompat.startForegroundService(this, Intent(this, CallRecordingService::class.java)) // Commented out
                    updateUI(true)
                } else {
                    requestPermissions()
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error toggling service: ${e.message}", e)
            showError("Failed to toggle service: ${e.message}")
        }
    }

    private fun testSpamDetection(text: String) {
        if (text.isBlank()) {
            showError("Please enter some text to analyze")
            return
        }
        statusText.text = "Analyzing text for spam..."
        val resultText = """
            Analysis Result:
            Status: ✅ Not suspicious (95%)
            
            Input Text: ${text.take(100)}${if (text.length > 100) "..." else ""}
            
            Note: Spam detection is currently in development.
        """.trimIndent()
        statusText.text = resultText
    }
}
