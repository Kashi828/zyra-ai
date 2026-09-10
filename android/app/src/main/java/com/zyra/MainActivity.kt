package com.zyra

import android.app.Activity
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
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
        .connectTimeout(4, TimeUnit.SECONDS)
        .readTimeout(4, TimeUnit.SECONDS)
        .build()
    private val jsonType = "application/json; charset=utf-8".toMediaType()

    private lateinit var modeLabel: TextView
    private lateinit var pcState: TextView
    private lateinit var activityLog: TextView
    private lateinit var taskInput: EditText
    private lateinit var pcUrlInput: EditText
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
        root.addView(label("A calm command center for your phone and trusted Windows PC.", 14f, muted),
            LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(9) })

        root.addView(space(22))
        val taskCard = card()
        taskCard.addView(label("ASK ZYRA", 11f, accent))
        taskInput = EditText(this).apply {
            hint = "What should ZYRA do?"
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
        status.addView(row("Phone agent", "Active", success))
        pcState = label("Not connected", 14f, muted)
        val pcRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(0, dp(9), 0, dp(2))
        }
        pcRow.addView(label("Windows agent", 14f, muted), LinearLayout.LayoutParams(0, -2, 1f))
        pcRow.addView(pcState)
        status.addView(pcRow)
        status.addView(row("Protection", "Active", success))
        status.addView(row("Remote access", "LAN / local only", warning))
        root.addView(status)

        root.addView(space(14))
        val connect = card()
        connect.addView(label("CONNECT WINDOWS PC", 11f, muted))
        connect.addView(label("Use a private-network address. ZYRA blocks public hosts here.", 12f, muted),
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
        val connectButton = secondaryButton("Connect & check")
        connectButton.setOnClickListener { connectToPc() }
        connect.addView(connectButton, LinearLayout.LayoutParams(-1, dp(46)).apply { topMargin = dp(8) })
        root.addView(connect)

        root.addView(space(14))
        val logCard = card()
        logCard.addView(label("ACTIVITY", 11f, muted))
        activityLog = label("Ready · phone agent is local-first.", 13f, primaryText)
        activityLog.setLineSpacing(0f, 1.15f)
        logCard.addView(activityLog, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(10) })
        root.addView(logCard)

        root.addView(space(26))
        val footer = TextView(this).apply {
            text = "ZYRA AI  •  Phone + Windows ecosystem  •  beta.2"
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
            activityLog.text = "Phone agent received the task."
            return
        }
        val base = pcUrlInput.text.toString().trim().trimEnd('/')
        if (!isAllowedPcUrl(base)) {
            activityLog.text = "Use a local/LAN Windows address (127.0.0.1, 10.x, 172.16–31.x, 192.168.x, or .local)."
            return
        }
        activityLog.text = "Sending to trusted Windows agent…"
        val body = JSONObject()
            .put("goal", task)
            .put("context", JSONObject().put("source", "android"))
            .toString().toRequestBody(jsonType)
        val request = Request.Builder().url("$base/v1/runtime/tasks").post(body).build()
        http.newCall(request).enqueue(object : okhttp3.Callback {
            override fun onFailure(call: Call, e: IOException) {
                runOnUiThread { activityLog.text = "PC connection failed: ${e.message ?: "unknown error"}" }
            }
            override fun onResponse(call: Call, response: Response) {
                response.use {
                    runOnUiThread {
                        if (response.isSuccessful) {
                            prefs.edit().putString("pc_url", base).apply()
                            pcState.text = "Connected"
                            pcState.setTextColor(success)
                            activityLog.text = "Task handed to the Windows agent."
                        } else activityLog.text = "Windows agent rejected the task (${response.code})."
                    }
                }
            }
        })
    }

    private fun connectToPc() {
        val base = pcUrlInput.text.toString().trim().trimEnd('/')
        if (!isAllowedPcUrl(base)) {
            activityLog.text = "Enter a local/LAN Windows address first."
            return
        }
        activityLog.text = "Checking Windows agent…"
        val request = Request.Builder().url("$base/health").get().build()
        http.newCall(request).enqueue(object : okhttp3.Callback {
            override fun onFailure(call: Call, e: IOException) {
                runOnUiThread {
                    pcState.text = "Offline"
                    pcState.setTextColor(warning)
                    activityLog.text = "Windows agent unavailable: ${e.message ?: "connection failed"}"
                }
            }
            override fun onResponse(call: Call, response: Response) {
                response.use {
                    runOnUiThread {
                        if (response.isSuccessful) {
                            prefs.edit().putString("pc_url", base).apply()
                            pcState.text = "Connected"
                            pcState.setTextColor(success)
                            activityLog.text = "Windows agent connected."
                        } else {
                            pcState.text = "Error"
                            pcState.setTextColor(warning)
                            activityLog.text = "Windows agent returned HTTP ${response.code}."
                        }
                    }
                }
            }
        })
    }

    private fun isAllowedPcUrl(value: String): Boolean = try {
        val uri = URI(value)
        val host = uri.host ?: return false
        val schemeOk = uri.scheme == "http" || uri.scheme == "https"
        val localHost = host == "localhost" || host == "127.0.0.1" || host.endsWith(".local")
        val privateIp = host.matches(Regex("^10\\..*")) || host.matches(Regex("^192\\.168\\..*")) ||
            host.matches(Regex("^172\\.(1[6-9]|2[0-9]|3[0-1])\\..*"))
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

    private fun card() = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        setPadding(dp(16), dp(16), dp(16), dp(16))
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
    }

    private fun secondaryButton(textValue: String) = Button(this).apply {
        text = textValue
        textSize = 13f
        setTextColor(primaryText)
        isAllCaps = false
        minHeight = 0
        stateListAnimator = null
        background = rounded(panel2, 14)
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
        setPadding(0, dp(10), 0, dp(2))
        addView(label(name, 14f, muted), LinearLayout.LayoutParams(0, -2, 1f))
        addView(label(value, 14f, color))
    }

    private fun space(height: Int) = Space(this).apply { layoutParams = LinearLayout.LayoutParams(1, dp(height)) }

    private fun rounded(color: Int, radius: Int) = GradientDrawable().apply {
        setColor(color)
        cornerRadius = dp(radius).toFloat()
    }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()
}
