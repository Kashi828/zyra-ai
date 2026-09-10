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
import android.view.View
import android.view.inputmethod.InputMethodManager
import android.content.Context
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.ScrollView
import android.widget.Space
import android.widget.TextView
import okhttp3.Call
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import org.json.JSONArray
import org.json.JSONObject
import java.io.IOException
import java.net.URI
import java.util.concurrent.TimeUnit

class MainActivity : Activity() {
    private val bg = Color.rgb(7, 9, 15)
    private val panel = Color.rgb(16, 20, 29)
    private val panel2 = Color.rgb(22, 27, 39)
    private val inputBg = Color.rgb(12, 16, 24)
    private val primaryText = Color.rgb(247, 248, 252)
    private val muted = Color.rgb(151, 160, 181)
    private val accent = Color.rgb(139, 92, 246)
    private val accentSoft = Color.rgb(52, 39, 84)
    private val success = Color.rgb(78, 214, 141)
    private val warning = Color.rgb(244, 191, 84)
    private val danger = Color.rgb(255, 112, 127)
    private val line = Color.rgb(40, 48, 63)
    private val prefs by lazy { getSharedPreferences("zyra_phone", MODE_PRIVATE) }
    private val http = OkHttpClient.Builder().connectTimeout(15, TimeUnit.SECONDS).readTimeout(15, TimeUnit.SECONDS).writeTimeout(15, TimeUnit.SECONDS).build()
    private val jsonType = "application/json; charset=utf-8".toMediaType()

    private lateinit var modeLabel: TextView
    private lateinit var pcState: TextView
    private lateinit var activityLog: TextView
    private lateinit var taskInput: EditText
    private lateinit var pcUrlInput: EditText
    private lateinit var offerIdInput: EditText
    private lateinit var pairCodeInput: EditText
    private lateinit var runButton: Button
    private var runOnPc = false
    private var taskBusy = false

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
            setPadding(dp(18), dp(14), dp(18), dp(30))
        }
        scroll.addView(root)

        val top = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL }
        top.addView(TextView(this).apply {
            text = "✦  ZYRA"
            textSize = 24f
            setTextColor(primaryText)
            typeface = Typeface.DEFAULT_BOLD
            letterSpacing = .02f
        }, LinearLayout.LayoutParams(0, -2, 1f))
        modeLabel = pill("●  Phone ready", success)
        top.addView(modeLabel)
        root.addView(top)

        root.addView(space(26))
        root.addView(TextView(this).apply {
            text = "Your agent.\nOn every device."
            textSize = 31f
            setTextColor(primaryText)
            typeface = Typeface.DEFAULT_BOLD
            setLineSpacing(0f, 1.01f)
        })
        root.addView(label("Run safe actions on your phone or send an authenticated task to your Windows agent.", 14f, muted), LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(9) })

        root.addView(space(20))
        val taskCard = card()
        taskCard.addView(label("COMMAND", 11f, accent))
        taskInput = EditText(this).apply {
            hint = "What should ZYRA do?\nTry: open camera, open settings, or open https://example.com"
            textSize = 16f
            setTextColor(primaryText)
            setHintTextColor(muted)
            setPadding(dp(16), dp(15), dp(16), dp(15))
            minLines = 4
            maxLines = 6
            gravity = Gravity.TOP
            background = rounded(inputBg, 17)
            isSingleLine = false
        }
        taskCard.addView(taskInput, LinearLayout.LayoutParams(-1, dp(128)).apply { topMargin = dp(11) })

        taskCard.addView(label("RUN TARGET", 10f, muted), LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(13) })
        val modeRow = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL }
        val phoneButton = actionButton("On phone", true)
        val pcButton = actionButton("On Windows", false)
        phoneButton.setOnClickListener { runOnPc = false; updateModeButtons(phoneButton, pcButton) }
        pcButton.setOnClickListener { runOnPc = true; updateModeButtons(phoneButton, pcButton) }
        modeRow.addView(phoneButton, LinearLayout.LayoutParams(0, dp(48), 1f))
        modeRow.addView(pcButton, LinearLayout.LayoutParams(0, dp(48), 1f).apply { marginStart = dp(8) })
        taskCard.addView(modeRow, LinearLayout.LayoutParams(-1, dp(48)).apply { topMargin = dp(7) })

        runButton = primaryButton("Run with ZYRA")
        runButton.setOnClickListener { executeTask() }
        taskCard.addView(runButton, LinearLayout.LayoutParams(-1, dp(56)).apply { topMargin = dp(11) })
        val progress = ProgressBar(this).apply { visibility = View.GONE }
        taskCard.addView(progress, LinearLayout.LayoutParams(-2, dp(24)).apply { gravity = Gravity.CENTER_HORIZONTAL; topMargin = dp(8) })
        root.addView(taskCard)

        root.addView(space(12))
        val statusCard = card()
        statusCard.addView(label("ECOSYSTEM", 10f, muted))
        statusCard.addView(row("Phone agent", "READY", success))
        pcState = label(if (hasPcCredentials()) "PAIRED" else "NOT PAIRED", 13f, if (hasPcCredentials()) success else muted)
        val pcRow = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL; setPadding(0, dp(10), 0, dp(2)) }
        pcRow.addView(label("Windows agent", 14f, muted), LinearLayout.LayoutParams(0, -2, 1f))
        pcRow.addView(pcState)
        statusCard.addView(pcRow)
        statusCard.addView(row("Protection", "ACTIVE", success))
        statusCard.addView(row("Transport", "PRIVATE LAN", warning))
        root.addView(statusCard)

        root.addView(space(12))
        val connectCard = card()
        connectCard.addView(label("CONNECT WINDOWS", 10f, muted))
        connectCard.addView(label("1. Enter the Windows LAN address.\n2. Generate a pairing offer on Windows.\n3. Enter the Offer ID and one-time code below.", 12f, muted), LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(6) })
        pcUrlInput = field("http://192.168.x.x:8000", prefs.getString("pc_url", "") ?: "")
        connectCard.addView(pcUrlInput, LinearLayout.LayoutParams(-1, dp(52)).apply { topMargin = dp(11) })
        val check = secondaryButton("Check Windows connection")
        check.setOnClickListener { connectToPc() }
        connectCard.addView(check, LinearLayout.LayoutParams(-1, dp(47)).apply { topMargin = dp(8) })
        offerIdInput = field("Pairing Offer ID", "")
        connectCard.addView(offerIdInput, LinearLayout.LayoutParams(-1, dp(52)).apply { topMargin = dp(8) })
        pairCodeInput = field("One-time pairing code", "")
        connectCard.addView(pairCodeInput, LinearLayout.LayoutParams(-1, dp(52)).apply { topMargin = dp(8) })
        val pair = secondaryButton("Pair this phone securely")
        pair.setOnClickListener { pairWithWindows() }
        connectCard.addView(pair, LinearLayout.LayoutParams(-1, dp(47)).apply { topMargin = dp(8) })
        root.addView(connectCard)

        root.addView(space(12))
        val activityCard = card()
        activityCard.addView(label("ACTIVITY", 10f, muted))
        activityLog = label("Ready. Choose a target and run your first command.", 13f, primaryText)
        activityLog.setLineSpacing(0f, 1.16f)
        activityCard.addView(activityLog, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(9) })
        root.addView(activityCard)

        root.addView(space(24))
        root.addView(TextView(this).apply {
            text = "ZYRA AI  •  Phone + Windows ecosystem  •  beta.4"
            textSize = 11f
            setTextColor(Color.rgb(95, 103, 121))
            gravity = Gravity.CENTER
        })
        setContentView(scroll)
    }

    private fun executeTask() {
        if (taskBusy) return
        val task = taskInput.text.toString().trim()
        if (task.isEmpty()) {
            activityLog.text = "Enter a task first."
            taskInput.requestFocus()
            return
        }
        hideKeyboard()
        taskBusy = true
        runButton.isEnabled = false
        runButton.text = "Working…"
        activityLog.text = if (runOnPc) "Connecting to Windows and submitting task…" else "Running phone action…"
        if (runOnPc) sendPcTask(task) else executePhoneTask(task)
    }

    private fun finishTaskUi() {
        runOnUiThread {
            taskBusy = false
            runButton.isEnabled = true
            runButton.text = "Run with ZYRA"
        }
    }

    private fun executePhoneTask(task: String) {
        val lowered = task.lowercase()
        try {
            when {
                lowered.contains("settings") -> startActivity(Intent(Settings.ACTION_SETTINGS))
                lowered.contains("wifi") -> startActivity(Intent(Settings.ACTION_WIFI_SETTINGS))
                lowered.contains("bluetooth") -> startActivity(Intent(Settings.ACTION_BLUETOOTH_SETTINGS))
                lowered.contains("camera") -> startActivity(Intent("android.media.action.IMAGE_CAPTURE"))
                Regex("https?://\\S+").containsMatchIn(task) -> {
                    val url = Regex("https?://\\S+").find(task)?.value?.trimEnd('.', ',', ')')
                    startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
                }
                lowered.contains("browser") || lowered.contains("web") -> startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("https://www.google.com")))
                lowered.startsWith("share ") -> {
                    val text = task.substringAfter(' ', "").trim()
                    startActivity(Intent.createChooser(Intent(Intent.ACTION_SEND).apply {
                        type = "text/plain"
                        putExtra(Intent.EXTRA_TEXT, text)
                    }, "Share with"))
                }
                else -> {
                    activityLog.text = "Phone action not mapped. Try settings, Wi‑Fi, Bluetooth, camera, browser, URL, or share."
                    finishTaskUi()
                    return
                }
            }
            activityLog.text = "Phone action launched successfully."
        } catch (e: Exception) {
            activityLog.text = "Phone action failed: ${e.message ?: "unknown error"}"
        } finally {
            finishTaskUi()
        }
    }

    private fun sendPcTask(task: String) {
        val base = pcUrlInput.text.toString().trim().trimEnd('/')
        if (!isAllowedPcUrl(base)) {
            activityLog.text = "Enter a private LAN Windows address, for example http://192.168.1.20:8000."
            finishTaskUi()
            return
        }
        ensurePcSession(base, { deviceId, sessionId ->
            val body = JSONObject()
                .put("goal", task)
                .put("device_id", deviceId)
                .put("session_id", sessionId)
                .put("auth_key", sessionId)
                .put("client_key", sessionId)
                .put("confirmed", true)
                .put("context", JSONObject().put("source", "android"))
            val request = Request.Builder()
                .url("$base/v1/runtime/tasks")
                .post(body.toString().toRequestBody(jsonType))
                .build()
            http.newCall(request).enqueue(object : okhttp3.Callback {
                override fun onFailure(call: Call, e: IOException) {
                    runOnUiThread { activityLog.text = "Windows task failed: ${e.message ?: "connection failed"}" }
                    finishTaskUi()
                }
                override fun onResponse(call: Call, response: Response) {
                    response.use {
                        val text = response.body?.string().orEmpty()
                        runOnUiThread {
                            if (response.isSuccessful) {
                                pcState.text = "CONNECTED"
                                pcState.setTextColor(success)
                                val json = try { JSONObject(text) } catch (_: Exception) { JSONObject() }
                                activityLog.text = "Windows task ${json.optString("status", "submitted")}: ${json.optString("detail", "accepted")}" 
                            } else {
                                val detail = try { JSONObject(text).optString("detail", text) } catch (_: Exception) { text }
                                activityLog.text = "Windows rejected the task (${response.code}): ${detail.ifBlank { "request rejected" }}"
                            }
                        }
                        finishTaskUi()
                    }
                }
            })
        }, { message ->
            runOnUiThread { activityLog.text = message }
            finishTaskUi()
        })
    }

    private fun ensurePcSession(base: String, onReady: (String, String) -> Unit, onError: (String) -> Unit) {
        val device = prefs.getString("device_id", null)
        val secret = prefs.getString("device_secret", null)
        val refresh = prefs.getString("refresh_token", null)
        if (device.isNullOrBlank() || secret.isNullOrBlank()) {
            onError("Pair this phone with Windows first. Generate the Offer ID and code on Windows.")
            return
        }
        if (!refresh.isNullOrBlank()) {
            postJson("$base/v1/session/refresh", JSONObject().put("device_id", device).put("refresh_token", refresh)) { ok, text ->
                if (ok) {
                    try {
                        val json = JSONObject(text)
                        saveSession(device, secret, json)
                        onReady(device, json.getString("session_id"))
                    } catch (_: Exception) {
                        createSession(base, device, secret, onReady, onError)
                    }
                } else {
                    createSession(base, device, secret, onReady, onError)
                }
            }
        } else createSession(base, device, secret, onReady, onError)
    }

    private fun createSession(base: String, device: String, secret: String, onReady: (String, String) -> Unit, onError: (String) -> Unit) {
        postJson("$base/v1/session/create", JSONObject().put("device_id", device).put("device_secret", secret)) { ok, text ->
            if (!ok) {
                val detail = try { JSONObject(text).optString("detail", "Windows session creation failed.") } catch (_: Exception) { "Windows session creation failed." }
                onError(detail)
                return@postJson
            }
            try {
                val json = JSONObject(text)
                saveSession(device, secret, json)
                onReady(device, json.getString("session_id"))
            } catch (_: Exception) {
                onError("Windows session response was invalid.")
            }
        }
    }

    private fun saveSession(device: String, secret: String, json: JSONObject) {
        val existingRefresh = prefs.getString("refresh_token", null)
        val refresh = json.optString("refresh_token").ifBlank { existingRefresh.orEmpty() }
        val currentExpires = prefs.getLong("expires_at", 0L)
        val expires = if (json.has("expires_at")) json.optLong("expires_at", currentExpires) else currentExpires
        prefs.edit()
            .putString("device_id", device)
            .putString("device_secret", secret)
            .putString("session_id", json.optString("session_id"))
            .putString("refresh_token", refresh)
            .putLong("expires_at", expires)
            .apply()
    }

    private fun pairWithWindows() {
        val base = pcUrlInput.text.toString().trim().trimEnd('/')
        val offer = offerIdInput.text.toString().trim()
        val code = pairCodeInput.text.toString().trim()
        if (!isAllowedPcUrl(base)) { activityLog.text = "Enter the Windows LAN address first."; return }
        if (offer.isBlank() || code.isBlank()) { activityLog.text = "Enter both the Offer ID and one-time pairing code from Windows."; return }
        hideKeyboard()
        activityLog.text = "Securely enrolling this phone…"
        val capabilities = JSONArray().apply {
            put("windows.apps")
            put("windows.files.read")
            put("windows.browser")
        }
        val body = JSONObject()
            .put("offer_id", offer)
            .put("pairing_code", code)
            .put("capabilities", capabilities)
        postJson("$base/v1/devices/pairing/enroll", body) { ok, text ->
            if (!ok) {
                val detail = try { JSONObject(text).optString("detail", "Pairing rejected.") } catch (_: Exception) { "Pairing rejected." }
                runOnUiThread { activityLog.text = detail }
                return@postJson
            }
            try {
                val json = JSONObject(text)
                val device = json.getString("device_id")
                val secret = json.getString("device_secret")
                prefs.edit().putString("pc_url", base).putString("device_id", device).putString("device_secret", secret).apply()
                createSession(base, device, secret, { _, _ ->
                    runOnUiThread {
                        pcState.text = "PAIRED"
                        pcState.setTextColor(success)
                        activityLog.text = "Phone paired with Windows. You can now select On Windows and run a task."
                    }
                }, { message -> runOnUiThread { activityLog.text = message } })
            } catch (_: Exception) {
                runOnUiThread { activityLog.text = "Pairing response was invalid." }
            }
        }
    }

    private fun postJson(url: String, body: JSONObject, callback: (Boolean, String) -> Unit) {
        val request = try {
            Request.Builder().url(url).post(body.toString().toRequestBody(jsonType)).build()
        } catch (e: Exception) {
            callback(false, e.message ?: "invalid URL")
            return
        }
        http.newCall(request).enqueue(object : okhttp3.Callback {
            override fun onFailure(call: Call, e: IOException) = callback(false, e.message ?: "connection failed")
            override fun onResponse(call: Call, response: Response) {
                response.use { callback(response.isSuccessful, response.body?.string().orEmpty()) }
            }
        })
    }

    private fun connectToPc() {
        val base = pcUrlInput.text.toString().trim().trimEnd('/')
        if (!isAllowedPcUrl(base)) {
            activityLog.text = "Use a private LAN Windows address, for example http://192.168.1.20:8000."
            return
        }
        activityLog.text = "Checking Windows agent…"
        http.newCall(Request.Builder().url("$base/health").get().build()).enqueue(object : okhttp3.Callback {
            override fun onFailure(call: Call, e: IOException) {
                runOnUiThread {
                    pcState.text = "OFFLINE"
                    pcState.setTextColor(danger)
                    activityLog.text = "Windows agent unavailable: ${e.message ?: "connection failed"}"
                }
            }
            override fun onResponse(call: Call, response: Response) {
                response.use {
                    runOnUiThread {
                        if (response.isSuccessful) {
                            prefs.edit().putString("pc_url", base).apply()
                            pcState.text = if (hasPcCredentials()) "PAIRED" else "REACHABLE"
                            pcState.setTextColor(success)
                            activityLog.text = "Windows agent is reachable on the private LAN."
                        } else {
                            pcState.text = "ERROR"
                            pcState.setTextColor(warning)
                            activityLog.text = "Windows agent returned HTTP ${response.code}."
                        }
                    }
                }
            }
        })
    }

    private fun hasPcCredentials(): Boolean = !prefs.getString("device_id", null).isNullOrBlank() && !prefs.getString("device_secret", null).isNullOrBlank()

    private fun isAllowedPcUrl(value: String): Boolean = try {
        val uri = URI(value)
        val host = uri.host ?: return false
        val schemeOk = uri.scheme == "http" || uri.scheme == "https"
        val localHost = host == "localhost" || host == "127.0.0.1" || host == "::1" || host.endsWith(".local")
        val privateIp = host.matches(Regex("^10\\..*")) || host.matches(Regex("^192\\.168\\..*")) || host.matches(Regex("^172\\.(1[6-9]|2[0-9]|3[0-1])\\..*"))
        schemeOk && (localHost || privateIp)
    } catch (_: Exception) { false }

    private fun updateModeButtons(phoneButton: Button, pcButton: Button) {
        phoneButton.background = rounded(if (!runOnPc) accent else panel2, 14)
        pcButton.background = rounded(if (runOnPc) accent else panel2, 14)
        phoneButton.setTextColor(if (!runOnPc) Color.WHITE else primaryText)
        pcButton.setTextColor(if (runOnPc) Color.WHITE else primaryText)
        modeLabel.text = if (runOnPc) "●  Windows selected" else "●  Phone selected"
        modeLabel.setTextColor(if (runOnPc) warning else success)
    }

    private fun field(hintValue: String, value: String) = EditText(this).apply {
        hint = hintValue
        setText(value)
        textSize = 14f
        setTextColor(primaryText)
        setHintTextColor(muted)
        setSingleLine(true)
        setPadding(dp(14), dp(12), dp(14), dp(12))
        background = rounded(inputBg, 14)
    }

    private fun card() = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        setPadding(dp(17), dp(17), dp(17), dp(17))
        background = rounded(panel, 20)
    }

    private fun actionButton(textValue: String, selected: Boolean) = Button(this).apply {
        text = textValue
        textSize = 13f
        setTextColor(if (selected) Color.WHITE else primaryText)
        isAllCaps = false
        minHeight = 0
        stateListAnimator = null
        background = rounded(if (selected) accent else panel2, 14)
    }

    private fun primaryButton(textValue: String) = Button(this).apply {
        text = textValue
        textSize = 14f
        setTextColor(Color.WHITE)
        isAllCaps = false
        minHeight = 0
        stateListAnimator = null
        background = rounded(accent, 16)
        typeface = Typeface.DEFAULT_BOLD
    }

    private fun secondaryButton(textValue: String) = Button(this).apply {
        text = textValue
        textSize = 13f
        setTextColor(primaryText)
        isAllCaps = false
        minHeight = 0
        stateListAnimator = null
        background = GradientDrawable().apply {
            setColor(panel2)
            cornerRadius = dp(14).toFloat()
            setStroke(dp(1), line)
        }
    }

    private fun pill(textValue: String, color: Int) = TextView(this).apply {
        text = textValue
        textSize = 12f
        setTextColor(color)
        setPadding(dp(11), dp(7), dp(11), dp(7))
        background = rounded(accentSoft, 30)
    }

    private fun label(textValue: String, size: Float, color: Int) = TextView(this).apply {
        text = textValue
        textSize = size
        setTextColor(color)
    }

    private fun row(name: String, value: String, color: Int) = LinearLayout(this).apply {
        orientation = LinearLayout.HORIZONTAL
        gravity = Gravity.CENTER_VERTICAL
        setPadding(0, dp(9), 0, dp(2))
        addView(label(name, 14f, muted), LinearLayout.LayoutParams(0, -2, 1f))
        addView(label(value, 13f, color))
    }

    private fun space(height: Int) = Space(this).apply { layoutParams = LinearLayout.LayoutParams(1, dp(height)) }

    private fun rounded(color: Int, radius: Int) = GradientDrawable().apply {
        setColor(color)
        cornerRadius = dp(radius).toFloat()
    }

    private fun hideKeyboard() {
        val imm = getSystemService(Context.INPUT_METHOD_SERVICE) as? InputMethodManager
        imm?.hideSoftInputFromWindow(currentFocus?.windowToken, 0)
        currentFocus?.clearFocus()
    }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()
}
