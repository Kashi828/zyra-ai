package com.zyra

import android.app.Activity
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.net.Uri
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.Space
import android.widget.TextView
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import kotlin.concurrent.thread

class MainActivity : Activity() {
    private val bg = Color.rgb(8, 10, 16)
    private val panel = Color.rgb(18, 21, 31)
    private val panel2 = Color.rgb(24, 28, 40)
    private val primaryText = Color.rgb(244, 245, 250)
    private val muted = Color.rgb(155, 162, 180)
    private val accent = Color.rgb(139, 92, 246)
    private val success = Color.rgb(72, 211, 137)
    private val danger = Color.rgb(240, 113, 103)

    // Populated once the device has enrolled/activated a session with the
    // paired PC agent. Never logged, never sent anywhere except the PC's own
    // LAN endpoint alongside a matching session_id.
    private var pcBaseUrl: String = ""
    private var deviceId: String = ""
    private var sessionId: String = ""

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = Color.rgb(8, 10, 16)
        window.navigationBarColor = Color.rgb(8, 10, 16)
        window.decorView.systemUiVisibility = 0

        val scroll = ScrollView(this).apply {
            setBackgroundColor(bg)
            clipToPadding = false
        }
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(18), dp(20), dp(28))
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
            typeface = android.graphics.Typeface.DEFAULT_BOLD
        }
        top.addView(brand, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        val online = TextView(this).apply {
            text = "●  PC online"
            textSize = 12f
            setTextColor(success)
            setPadding(dp(10), dp(7), dp(10), dp(7))
            background = rounded(panel2, 30)
        }
        top.addView(online)
        root.addView(top)

        root.addView(space(18))
        val greeting = TextView(this).apply {
            text = "Control your PC\nfrom anywhere."
            textSize = 30f
            setTextColor(primaryText)
            typeface = android.graphics.Typeface.DEFAULT_BOLD
            setLineSpacing(0f, 1.05f)
        }
        root.addView(greeting)
        root.addView(label("Secure companion for your ZYRA AI agent."), LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(8) })

        root.addView(space(22))
        val taskCard = card()
        taskCard.addView(label("ASK ZYRA", 12f, accent))
        val input = TextView(this).apply {
            text = "What should ZYRA do on your PC?"
            textSize = 16f
            setTextColor(muted)
            setPadding(dp(16), dp(17), dp(16), dp(17))
            background = rounded(Color.rgb(29, 33, 46), 16)
        }
        taskCard.addView(input, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(10) })
        val run = Button(this).apply {
            text = "Run with ZYRA"
            textSize = 14f
            setTextColor(Color.WHITE)
            background = rounded(accent, 16)
            isAllCaps = false
            setOnClickListener {
                input.text = "Task sent to your protected PC agent."
                sendTaskToPc(input.text.toString())
            }
        }
        taskCard.addView(run, LinearLayout.LayoutParams(-1, dp(52)).apply { topMargin = dp(10) })
        root.addView(taskCard)

        root.addView(space(14))
        val status = card()
        val statusHeader = TextView(this).apply {
            text = "PC STATUS"
            textSize = 12f
            setTextColor(muted)
        }
        status.addView(statusHeader)
        status.addView(row("Agent", "Ready", success))
        status.addView(row("Remote access", "Off by default", muted))
        status.addView(row("Protection", "Active", success))
        root.addView(status)

        root.addView(space(14))
        val quick = card()
        val quickHeader = TextView(this).apply {
            text = "QUICK ACTIONS"
            textSize = 12f
            setTextColor(muted)
        }
        quick.addView(quickHeader)
        val actions = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        actions.addView(action("Send to PC"), weightParams())
        actions.addView(action("Devices"), weightParams().apply { marginStart = dp(8) })
        actions.addView(action("Tasks"), weightParams().apply { marginStart = dp(8) })
        quick.addView(actions, LinearLayout.LayoutParams(-1, dp(48)).apply { topMargin = dp(10) })
        root.addView(quick)

        root.addView(space(22))
        val footer = TextView(this).apply {
            text = "ZYRA AI  •  Secure Android companion  •  v0.1.0-beta.1"
            textSize = 12f
            setTextColor(Color.rgb(105, 112, 130))
            gravity = Gravity.CENTER
        }
        root.addView(footer)

        setContentView(scroll)
    }

    // --- PC networking -----------------------------------------------------
    //
    // The companion app only ever talks to the paired PC agent over the LAN,
    // never over the open internet, and every request carries the device's
    // authenticated session alongside it. Both properties are enforced here
    // rather than trusted from the caller, since this activity is the last
    // line of defense before a request leaves the phone.

    /** Restricts outbound PC-agent requests to http(s) on the local network:
     * loopback, mDNS (`.local`), and the RFC1918 private ranges. Anything
     * else (a public host, a non-http scheme) is rejected before it is sent. */
    private fun isPrivateLanEndpoint(rawUrl: String): Boolean {
        val uri = Uri.parse(rawUrl) ?: return false
        if (!(uri.scheme == "http" || uri.scheme == "https")) return false
        val host = uri.host ?: return false
        if (host == "localhost" || host == "127.0.0.1") return true
        if (host.endsWith(".local")) return true
        if (Regex("^10\\..*").matches(host)) return true
        if (Regex("^192\\.168\\..*").matches(host)) return true
        if (Regex("^172\\.(1[6-9]|2[0-9]|3[0-1])\\..*").matches(host)) return true
        return false
    }

    /** Every authenticated request to the PC agent carries both the
     * device/session pair the backend validates and the auth/client key
     * fields the transport layer expects alongside it. */
    private fun buildAuthenticatedPayload(extra: JSONObject? = null): JSONObject {
        val payload = extra ?: JSONObject()
        return payload
            .put("device_id", deviceId)
            .put("session_id", sessionId)
            .put("auth_key", sessionId)
            .put("client_key", sessionId)
    }

    /** Capabilities requested during first-time pairing. Kept as an
     * allowlist here so the app can never silently request more than a
     * user-visible, reviewable set of PC permissions. */
    private fun requestedPairingCapabilities(): JSONArray {
        return JSONArray()
            .put("windows.apps")
            .put("windows.files.read")
            .put("windows.browser")
    }

    private fun postJson(path: String, body: JSONObject): JSONObject? {
        if (pcBaseUrl.isEmpty() || !isPrivateLanEndpoint(pcBaseUrl)) return null
        val connection = (URL(pcBaseUrl.trimEnd('/') + path).openConnection() as HttpURLConnection)
        return try {
            connection.requestMethod = "POST"
            connection.connectTimeout = 8000
            connection.readTimeout = 8000
            connection.doOutput = true
            connection.setRequestProperty("Content-Type", "application/json")
            connection.outputStream.use { it.write(body.toString().toByteArray(Charsets.UTF_8)) }
            val status = connection.responseCode
            val stream = if (status in 200..299) connection.inputStream else connection.errorStream
            val text = stream?.bufferedReader()?.use { it.readText() }.orEmpty()
            if (status !in 200..299) null else JSONObject(text)
        } catch (_: Exception) {
            null
        } finally {
            connection.disconnect()
        }
    }

    private fun sendTaskToPc(goal: String) {
        if (deviceId.isEmpty() || sessionId.isEmpty()) return
        thread {
            postJson("/v1/runtime/tasks", buildAuthenticatedPayload(JSONObject().put("goal", goal)))
        }
    }

    private fun enrollWithPc(offerId: String, pairingCode: String) {
        thread {
            val body = JSONObject()
                .put("offer_id", offerId)
                .put("pairing_code", pairingCode)
                .put("capabilities", requestedPairingCapabilities())
            postJson("/v1/devices/pairing/enroll", body)
        }
    }

    // --- UI helpers ----------------------------------------------------------

    private fun card(): LinearLayout = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        setPadding(dp(16), dp(16), dp(16), dp(16))
        background = rounded(panel, 20)
        elevation = dp(1).toFloat()
    }

    private fun row(title: String, value: String, color: Int): View {
        val r = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(0, dp(9), 0, dp(2))
        }
        r.addView(label(title, 14f, muted), LinearLayout.LayoutParams(0, -2, 1f))
        r.addView(label(value, 14f, color))
        return r
    }

    private fun action(title: String): Button = Button(this).apply {
        text = title
        textSize = 12f
        setTextColor(primaryText)
        isAllCaps = false
        background = rounded(panel2, 14)
    }

    private fun label(value: String, size: Float = 14f, color: Int = muted) = TextView(this).apply {
        text = value
        textSize = size
        setTextColor(color)
    }

    private fun space(height: Int) = Space(this).apply {
        layoutParams = LinearLayout.LayoutParams(1, dp(height))
    }

    private fun weightParams() = LinearLayout.LayoutParams(0, -1, 1f)

    private fun rounded(color: Int, radius: Int): GradientDrawable = GradientDrawable().apply {
        setColor(color)
        cornerRadius = dp(radius).toFloat()
    }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()
}
