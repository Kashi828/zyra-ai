package com.zyra

import android.app.Activity
import android.content.Intent
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.net.Uri
import android.os.Bundle
import android.provider.Settings
import android.view.Gravity
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.Space
import android.widget.TextView
import okhttp3.Call
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import org.json.JSONObject
import java.io.IOException
import java.net.URI
import java.util.concurrent.TimeUnit

class MainActivity : Activity() {
    private val bg = Color.rgb(7, 9, 15)
    private val panel = Color.rgb(17, 20, 30)
    private val panel2 = Color.rgb(25, 29, 42)
    private val inputBg = Color.rgb(28, 32, 45)
    private val primaryText = Color.rgb(246, 247, 251)
    private val muted = Color.rgb(151, 159, 179)
    private val accent = Color.rgb(139, 92, 246)
    private val accentSoft = Color.rgb(49, 38, 79)
    private val success = Color.rgb(72, 211, 137)
    private val warning = Color.rgb(245, 190, 80)
    private val prefs by lazy { getSharedPreferences("zyra_phone", MODE_PRIVATE) }
    private val http = OkHttpClient.Builder()
        .connectTimeout(5, TimeUnit.SECONDS)
        .readTimeout(5, TimeUnit.SECONDS)
        .build()
    private val jsonType = "application/json; charset=utf-8".toMediaType()

    private lateinit var modeLabel: TextView
    private lateinit var pcState: TextView
    private lateinit var activityLog: TextView
    private lateinit var taskInput: EditText
    private lateinit var pcUrlInput: EditText
    private lateinit var offerIdInput: EditText
    private lateinit var pairCodeInput: EditText
    private var runOnPc = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = bg
        window.navigationBarColor = bg
        window.decorView.systemUiVisibility = 0

        val scroll = ScrollView(this).apply {
            setBackgroundColor(bg)
            clipToPadding = false
            isFillViewport = true
        }
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(16), dp(20), dp(30))
        }
        scroll.addView(root)

        val top = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        val brand = TextView(this).apply {
            text = "✦  ZYRA"
            textSize = 24f
            setTextColor(primaryText)
            typeface = Typeface.DEFAULT_BOLD
            letterSpacing = .02f
        }
        top.addView(brand, LinearLayout.LayoutParams(0, -2, 1f))
        modeLabel = pill("●  Phone active", success)
        top.addView(modeLabel)
        root.addView(top)

        root.addView(space(28))
        val greeting = TextView(this).apply {
            text = "Your agent.\nOn your phone."
            textSize = 32f
            setTextColor(primaryText)
            typeface = Typeface.DEFAULT_BOLD
            setLineSpacing(0f, 1.02f)
        }
        root.addView(greeting)
        root.addView(label("Safe phone actions plus an authenticated Windows agent connection.", 14f, muted),
            LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(9) })

        root.addView(space(22))
        val taskCard = card()
        taskCard.addView(label("ASK ZYRA", 11f, accent))
        taskInput = EditText(this).apply {
            hint = "Try: open camera · open settings · open https://example.com"
            textSize = 16f
            setTextColor(primaryText)
            setHintTextColor(muted)
            setPadding(dp(16), dp(14), dp(16), dp(14))
            minLines = 3
            maxLines = 5
            gravity = Gravity.TOP
            background = rounded(inputBg, 16)
        }
        taskCard.addView(taskInput, LinearLayout.LayoutParams(-1, dp(104)).apply { topMargin = dp(11) })

        val modeRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        val phoneButton = actionButton("On phone", true)
        val pcButton = actionButton("On PC", false)
        phoneButton.setOnClickListener { runOnPc = false; updateModeButtons(phoneButton, modeRow) }
        pcButton.setOnClickListener { runOnPc = true; updateModeButtons(phoneButton, modeRow) }
        modeRow.addView(phoneButton, LinearLayout.LayoutParams(0, dp(46), 1f))
        modeRow.addView(pcButton, LinearLayout.LayoutParams(0, dp(46), 1f).apply { marginStart = dp(8) })
        taskCard.addView(modeRow, LinearLayout.LayoutParams(-1, dp(46)).apply { topMargin = dp(11) })

        val run = primaryButton("Run with ZYRA")
        run.setOnClickListener { executeTask() }
        taskCard.addView(run, LinearLayout.LayoutParams(-1, dp(54)).apply { topMargin = dp(11) })
        root.addView(taskCard)

        root.addView(space(14))
        val status = card()
        status.addView(label("ECOSYSTEM", 11f, muted))
        status.addView(row("Phone agent", "Ready", success))
        pcState = label(if (prefs.getString("device_id", null) != null) "Paired" else "Not paired", 14f,
            if (prefs.getString("device_id", null) != null) success else muted)
        val pcRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(0, dp(9), 0, dp(2))
        }
        pcRow.addView(label("Windows agent", 14f, muted), LinearLayout.LayoutParams(0, -2, 1f))
        pcRow.addView(pcState)
        status.addView(pcRow)
        status.addView(row("Protection", "Active", success))
        status.addView(row("Network", "Private LAN only", warning))
        root.addView(status)

        root.addView(space(14))
        val connect = card()
        connect.addView(label("WINDOWS CONNECTION", 11f, muted))
        connect.addView(label("1. Generate a pairing code on Windows. 2. Enter the code here. 3. Run tasks on PC.", 12f, muted),
            LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(5) })
        pcUrlInput = EditText(this).apply {
            hint = "http://192.168.x.x:8000"
            setText(prefs.getString("pc_url", "") ?: "")
            textSize = 14f
            setTextColor(primaryText)
            setHintTextColor(muted)
            setSingleLine(true)
            setPadding(dp(14), dp(12), dp(14), dp(12))
            background = rounded(inputBg, 14)
        }
        connect.addView(pcUrlInput, LinearLayout.LayoutParams(-1, dp(50)).apply { topMargin = dp(10) })
        val checkButton = secondaryButton("Check Windows agent")
        checkButton.setOnClickListener { connectToPc() }
        connect.addView(checkButton, LinearLayout.LayoutParams(-1, dp(46)).apply { topMargin = dp(8) })

        offerIdInput = EditText(this).apply {
            hint = "Pairing offer ID"
            textSize = 14f
            setTextColor(primaryText)
            setHintTextColor(muted)
            setSingleLine(true)
            setPadding(dp(14), dp(12), dp(14), dp(12))
            background = rounded(inputBg, 14)
        }
        connect.addView(offerIdInput, LinearLayout.LayoutParams(-1, dp(50)).apply { topMargin = dp(8) })
        pairCodeInput = EditText(this).apply {
            hint = "Pairing code"
            textSize = 14f
            setTextColor(primaryText)
            setHintTextColor(muted)
            setSingleLine(true)
            setPadding(dp(14), dp(12), dp(14), dp(12))
            background = rounded(inputBg, 14)
        }
        connect.addView(pairCodeInput, LinearLayout.LayoutParams(-1, dp(50)).apply { topMargin = dp(8) })
        val pairButton = secondaryButton("Pair this phone")
        pairButton.setOnClickListener { pairWithWindows() }
        connect.addView(pairButton, LinearLayout.LayoutParams(-1, dp(46)).apply { topMargin = dp(8) })
        root.addView(connect)

        root.addView(space(14))
        val logCard = card()
        logCard.addView(label("ACTIVITY", 11f, muted))
        activityLog = label("Ready · authenticated local-first agent.", 13f, primaryText)
        activityLog.setLineSpacing(0f, 1.15f)
        logCard.addView(activityLog, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(10) })
        root.addView(logCard)

        root.addView(space(26))
        val footer = TextView(this).apply {
            text = "ZYRA AI  •  Phone + Windows ecosystem  •  beta.4"
            textSize = 11f
            setTextColor(Color.rgb(100, 108, 126))
            gravity = Gravity.CENTER
        }
        root.addView(footer)
        setContentView(scroll)
    }

    private fun executeTask() {
        val task = taskInput.text.toString().trim()
        if (task.isEmpty()) {
            activityLog.text = "Enter a task first."
            taskInput.requestFocus()
            return
        }
        if (!runOnPc) {
            executePhoneTask(task)
            return
        }
        sendPcTask(task)
    }

    private fun executePhoneTask(task: String) {
        val lowered = task.lowercase()
        try {
            when {
                lowered.contains("settings") -> startActivity(Intent(Settings.ACTION_SETTINGS))
                lowered.contains("wifi") -> startActivity(Intent(Settings.ACTION_WIFI_SETTINGS))
                lowered.contains("bluetooth") -> startActivity(Intent(Settings.ACTION_BLUETOOTH_SETTINGS))
                lowered.contains("camera") -> startActivity(Intent("android.media.action.IMAGE_CAPTURE"))
                lowered.contains("browser") || lowered.contains("web") -> startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("https://www.google.com")))
                Regex("https?://\\S+").containsMatchIn(task) -> {
                    val url = Regex("https?://\\S+").find(task)!!.value.trimEnd('.', ',', ')')
                    startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
                }
                lowered.startsWith("share ") -> {
                    val text = task.substringAfter(' ', "").trim()
                    val intent = Intent(Intent.ACTION_SEND).apply {
                        type = "text/plain"
                        putExtra(Intent.EXTRA_TEXT, text)
                    }
                    startActivity(Intent.createChooser(intent, "Share with"))
                }
                else -> {
                    activityLog.text = "Phone action not mapped yet. Try settings, Wi‑Fi, Bluetooth, camera, browser, URL, or share."
                    return
                }
            }
            activityLog.text = "Phone action completed."
        } catch (e: Exception) {
            activityLog.text = "Phone action failed: ${e.message ?: "unknown error"}"
        }
    }

    private fun sendPcTask(task: String) {
        val base = pcUrlInput.text.toString().trim().trimEnd('/')
        if (!isAllowedPcUrl(base)) {
            activityLog.text = "Use a local/LAN Windows address first."
            return
        }
        activityLog.text = "Refreshing authenticated Windows session…"
        ensurePcSession({ deviceId, sessionId ->
            activityLog.text = "Sending task to Windows…"
            val body = JSONObject()
                .put("goal", task)
                .put("device_id", deviceId)
                .put("session_id", sessionId)
                .put("confirmed", true)
                .put("context", JSONObject().put("source", "android"))
                .toString().toRequestBody(jsonType)
            val request = Request.Builder().url("$base/v1/runtime/tasks").post(body).build()
            http.newCall(request).enqueue(object : okhttp3.Callback {
                override fun onFailure(call: Call, e: IOException) {
                    runOnUiThread { activityLog.text = "PC task failed: ${e.message ?: "connection failed"}" }
                }
                override fun onResponse(call: Call, response: Response) {
                    response.use {
                        val text = response.body?.string().orEmpty()
                        runOnUiThread {
                            if (response.isSuccessful) {
                                pcState.text = "Connected"
                                pcState.setTextColor(success)
                                val json = try { JSONObject(text) } catch (_: Exception) { JSONObject() }
                                activityLog.text = "Windows task ${json.optString("status", "done")}: ${json.optString("detail", "done")}"
                            } else {
                                activityLog.text = "Windows agent rejected the task (${response.code})."
                            }
                        }
                    }
                }
            })
        }, { message -> runOnUiThread { activityLog.text = message } })
    }

    private fun ensurePcSession(onReady: (String, String) -> Unit, onError: (String) -> Unit) {
        val device = prefs.getString("device_id", null)
        val secret = prefs.getString("device_secret", null)
        val refresh = prefs.getString("refresh_token", null)
        if (device.isNullOrBlank() || secret.isNullOrBlank()) {
            onError("Pair this phone with Windows first.")
            return
        }
        if (!refresh.isNullOrBlank()) {
            postJson("http://$${pcUrlInput.text.toString().trim().trimEnd('/')}/v1/session/refresh", JSONObject().put("device_id", device).put("refresh_token", refresh)) { ok, text ->
                if (ok) {
                    try {
                        val json = JSONObject(text)
                        saveSession(device, secret, json)
                        onReady(device, json.getString("session_id"))
                    } catch (_: Exception) {
                        createSession(device, secret, onReady, onError)
                    }
                } else createSession(device, secret, onReady, onError)
            }
        } else createSession(device, secret, onReady, onError)
    }

    private fun createSession(device: String, secret: String, onReady: (String, String) -> Unit, onError: (String) -> Unit) {
        val base = pcUrlInput.text.toString().trim().trimEnd('/')
        postJson("$base/v1/session/create", JSONObject().put("device_id", device).put("device_secret", secret), absolute = true) { ok, text ->
            if (!ok) { onError("Windows session creation failed."); return@postJson }
            try {
                val json = JSONObject(text)
                saveSession(device, secret, json)
                onReady(device, json.getString("session_id"))
            } catch (_: Exception) { onError("Windows session response was invalid.") }
        }
    }

    private fun saveSession(device: String, secret: String, json: JSONObject) {
        prefs.edit().putString("device_id", device).putString("device_secret", secret)
            .putString("session_id", json.optString("session_id"))
            .putString("refresh_token", json.optString("refresh_token"))
            .putLong("expires_at", json.optLong("expires_at", 0L)).apply()
    }

    private fun pairWithWindows() {
        val base = pcUrlInput.text.toString().trim().trimEnd('/')
        val offer = offerIdInput.text.toString().trim()
        val code = pairCodeInput.text.toString().trim()
        if (!isAllowedPcUrl(base)) { activityLog.text = "Enter the Windows LAN address first."; return }
        if (offer.isBlank() || code.isBlank()) { activityLog.text = "Enter the Windows pairing offer ID and code."; return }
        activityLog.text = "Enrolling this phone…"
        val body = JSONObject().put("offer_id", offer).put("pairing_code", code)
            .put("capabilities", org.json.JSONArray().apply {
                put("windows.apps"); put("windows.files.read"); put("windows.browser")
            })
        postJson("$base/v1/devices/pairing/enroll", body, absolute = true) { ok, text ->
            if (!ok) { runOnUiThread { activityLog.text = "Pairing rejected." }; return@postJson }
            try {
                val json = JSONObject(text)
                val device = json.getString("device_id")
                val secret = json.getString("device_secret")
                prefs.edit().putString("pc_url", base).putString("device_id", device).putString("device_secret", secret).apply()
                createSession(device, secret, { _, _ ->
                    runOnUiThread { pcState.text = "Paired"; pcState.setTextColor(success); activityLog.text = "Phone paired securely with Windows." }
                }, { message -> runOnUiThread { activityLog.text = message } })
            } catch (_: Exception) { runOnUiThread { activityLog.text = "Pairing response was invalid." } }
        }
    }

    private fun postJson(path: String, body: JSONObject, absolute: Boolean = false, callback: (Boolean, String) -> Unit) {
        val request = Request.Builder().url(if (absolute) path else "http://127.0.0.1:8000$path")
            .post(body.toString().toRequestBody(jsonType)).build()
        http.newCall(request).enqueue(object : okhttp3.Callback {
            override fun onFailure(call: Call, e: IOException) = callback(false, e.message ?: "connection failed")
            override fun onResponse(call: Call, response: Response) { response.use { callback(response.isSuccessful, response.body?.string().orEmpty()) } }
        })
    }

    private fun connectToPc() {
        val base = pcUrlInput.text.toString().trim().trimEnd('/')
        if (!isAllowedPcUrl(base)) { activityLog.text = "Enter a local/LAN Windows address first."; return }
        activityLog.text = "Checking Windows agent…"
        val request = Request.Builder().url("$base/health").get().build()
        http.newCall(request).enqueue(object : okhttp3.Callback {
            override fun onFailure(call: Call, e: IOException) { runOnUiThread { pcState.text = "Offline"; pcState.setTextColor(warning); activityLog.text = "Windows agent unavailable: ${e.message ?: "connection failed"}" } }
            override fun onResponse(call: Call, response: Response) { response.use { runOnUiThread { if (response.isSuccessful) { prefs.edit().putString("pc_url", base).apply(); pcState.text = if (prefs.getString("device_id", null) != null) "Paired" else "Reachable"; pcState.setTextColor(success); activityLog.text = "Windows agent is reachable." } else { pcState.text = "Error"; pcState.setTextColor(warning); activityLog.text = "Windows agent returned HTTP ${response.code}." } } } }
        })
    }

    private fun isAllowedPcUrl(value: String): Boolean = try {
        val uri = URI(value)
        val host = uri.host ?: return false
        val schemeOk = uri.scheme == "http" || uri.scheme == "https"
        val localHost = host == "localhost" || host == "127.0.0.1" || host.endsWith(".local")
        val privateIp = host.matches(Regex("^10\\..*")) || host.matches(Regex("^192\\.168\\..*")) || host.matches(Regex("^172\\.(1[6-9]|2[0-9]|3[0-1])\\..*"))
        schemeOk && (localHost || privateIp)
    } catch (_: Exception) { false }

    private fun updateModeButtons(phoneButton: Button, modeRow: LinearLayout) {
        val pc = modeRow.getChildAt(1) as? Button ?: return
        phoneButton.background = rounded(if (!runOnPc) accent else panel2, 14)
        pc.background = rounded(if (runOnPc) accent else panel2, 14)
        phoneButton.setTextColor(if (!runOnPc) Color.WHITE else primaryText)
        pc.setTextColor(if (runOnPc) Color.WHITE else primaryText)
        modeLabel.text = if (runOnPc) "●  PC selected" else "●  Phone active"
        modeLabel.setTextColor(if (runOnPc) warning else success)
    }

    private fun card() = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(dp(16), dp(16), dp(16), dp(16)); background = rounded(panel, 20) }
    private fun actionButton(textValue: String, selected: Boolean) = Button(this).apply { text = textValue; textSize = 13f; setTextColor(if (selected) Color.WHITE else primaryText); isAllCaps = false; minHeight = 0; stateListAnimator = null; background = rounded(if (selected) accent else panel2, 14) }
    private fun primaryButton(textValue: String) = Button(this).apply { text = textValue; textSize = 14f; setTextColor(Color.WHITE); isAllCaps = false; minHeight = 0; stateListAnimator = null; background = rounded(accent, 16) }
    private fun secondaryButton(textValue: String) = Button(this).apply { text = textValue; textSize = 13f; setTextColor(primaryText); isAllCaps = false; minHeight = 0; stateListAnimator = null; background = rounded(panel2, 14) }
    private fun pill(textValue: String, color: Int) = TextView(this).apply { text = textValue; textSize = 12f; setTextColor(color); setPadding(dp(11), dp(7), dp(11), dp(7)); background = rounded(accentSoft, 30) }
    private fun label(textValue: String, size: Float, color: Int) = TextView(this).apply { text = textValue; textSize = size; setTextColor(color) }
    private fun row(name: String, value: String, color: Int) = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL; setPadding(0, dp(10), 0, dp(2)); addView(label(name, 14f, muted), LinearLayout.LayoutParams(0, -2, 1f)); addView(label(value, 14f, color)) }
    private fun space(height: Int) = Space(this).apply { layoutParams = LinearLayout.LayoutParams(1, dp(height)) }
    private fun rounded(color: Int, radius: Int) = GradientDrawable().apply { setColor(color); cornerRadius = dp(radius).toFloat() }
    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()
}
