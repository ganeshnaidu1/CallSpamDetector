package com.callscam.detector

import android.Manifest
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.SharedPreferences
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.telephony.TelephonyManager
import android.util.Log
import android.view.View
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import com.callscam.detector.audio.WhisperHelper
import com.callscam.detector.service.CallAccessibilityService
import com.callscam.detector.service.CallRecordingService
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class MainActivity : AppCompatActivity() {
    private val TAG = "SpamDetector"

    private val requiredPermissions = arrayOf(
        Manifest.permission.RECORD_AUDIO,
        Manifest.permission.READ_PHONE_STATE,
        Manifest.permission.READ_CALL_LOG,
        Manifest.permission.FOREGROUND_SERVICE,
        Manifest.permission.POST_NOTIFICATIONS
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

    private lateinit var statusText: TextView
    private lateinit var prefs: SharedPreferences
    // SpamDetector is now managed by CallAccessibilityService
    private val coroutineScope = CoroutineScope(Dispatchers.Main)

    private lateinit var startButton: Button
    private lateinit var statusText: TextView
    private lateinit var prefs: SharedPreferences
    private var isServiceRunning = false
    private val coroutineScope = CoroutineScope(Dispatchers.Main)
    private lateinit var whisperHelper: WhisperHelper

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        Log.d(TAG, "onCreate: Starting MainActivity")
        
        try {
            Log.d(TAG, "Setting content view...")
            setContentView(R.layout.activity_main)
            Log.d(TAG, "Content view set successfully")
            
            // Initialize WhisperHelper
            whisperHelper = WhisperHelper(this)
            
            Log.d(TAG, "Initializing SharedPreferences...")
            prefs = getSharedPreferences("SpamDetector", MODE_PRIVATE)
            Log.d(TAG, "SharedPreferences initialized")
            
            try {
                Log.d(TAG, "Finding views...")
                statusText = findViewById(R.id.status_text)
                startButton = findViewById(R.id.start_button)
                
                startButton.setOnClickListener {
                    if (!hasAllRequiredPermissions()) {
                        requestPermissions()
                    } else if (!isAccessibilityServiceEnabled()) {
                        checkAndRequestAccessibilityService()
                    } else {
                        toggleService()
                    }
                }
                
                updateUI()
                Log.d(TAG, "All views found and initialized successfully")
            } catch (e: Exception) {
                Log.e(TAG, "Error finding views: ${e.message}", e)
                showError("Error initializing UI: ${e.message}")
                finish()
                return
            }
            
            
                // Check and request permissions
            if (!hasAllRequiredPermissions()) {
                requestPermissions()
            } else if (!isAccessibilityServiceEnabled()) {
                checkAndRequestAccessibilityService()
            } else {
                startCallMonitoring()
            }
                
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
                val intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
                startActivity(intent)
            }
            .setNegativeButton("Cancel") { dialog, _ ->
                dialog.dismiss()
            }
            .setCancelable(false)
            .show()
    }
    
    private fun isAccessibilityServiceEnabled(): Boolean {
        val expectedComponentName = ComponentName(this, CallAccessibilityService::class.java)
        val enabledServices = Settings.Secure.getString(
            contentResolver,
            Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
        ) ?: return false
        
        return enabledServices.contains(expectedComponentName.flattenToString())
    }
    
    private fun startCallMonitoring() {
        // Start the foreground service
        val serviceIntent = Intent(this, CallRecordingService::class.java)
        ContextCompat.startForegroundService(this, serviceIntent)
        isServiceRunning = true
        updateUI()
    }

    
    private fun showError(message: String) {
        runOnUiThread {
            try {
                AlertDialog.Builder(this@MainActivity)
                    .setTitle("Error")
                    .setMessage(message)
                    .setPositiveButton("OK", null)
                    .show()
            } catch (e: Exception) {
                Log.e(TAG, "Error showing error dialog: ${e.message}")
                Toast.makeText(this@MainActivity, "Error: $message", Toast.LENGTH_LONG).show()
            }
        }
    }
    
    private fun testSpamDetection(text: String) {
        coroutineScope.launch {
            try {
                val spamDetector = CallAccessibilityService.getSpamDetector(this@MainActivity)
                val result = withContext(Dispatchers.IO) {
                    spamDetector.analyzeConversation(text)
                }
                
                val status = if (result.isSuspicious) {
                    "⚠️ SUSPICIOUS (${(result.confidence * 100).toInt()}%)"
                } else {
                    "✅ Not suspicious (${(result.confidence * 100).toInt()}%)"
                }
                
                statusText.text = """
                    Analysis Result:
                    Status: $status
                    
                    Reasoning:
                    ${result.reasoning}
                    
                    Timestamp: ${result.timestamp}
                """.trimIndent()
                
            } catch (e: Exception) {
                Log.e(TAG, "Error analyzing text: ${e.message}", e)
                showError("Error analyzing text: ${e.message}")
            }
        }
    }

