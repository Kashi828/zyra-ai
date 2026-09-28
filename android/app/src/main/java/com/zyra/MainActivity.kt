package com.zyra

import android.app.Activity
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.net.Uri
import android.os.Bundle
import android.text.InputType
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.Space
import android.widget.TextView
import com.zyra.enrollment.DeviceCredentialStorage
import com.zyra.enrollment.DeviceCredentials
import com.zyra.enrollment.PairingHttpTransport
import com.zyra.session.SessionManager
import com.zyra.transport.AuthenticatedTransportSession
import com.zyra.transport.RemoteCommandHttpTransport
import com.zyra.transport.ZyraHttpTransport
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

    private companion object {
        const val PAIRING_ENROLL_PATH = "/v1/devices/pairing/enroll"
    }

    private lateinit var credentialStorage: DeviceCredentialStorage
    private var credentials: DeviceCredentials? = null

    // Set from the Keystore-backed session each time a request is prepared.
    private var pcBaseUrl: String = ""
    private var deviceId: String = ""
    private var sessionId: String = ""

    private lateinit var onlineChip: TextView
    private lateinit var pairCard: LinearLayout
    private lateinit var agentValue: TextView
    private lateinit var accessValue: TextView
    private lateinit var protectionValue: TextView
    private lateinit var resultView: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = Color.rgb(8, 10, 16)
        window.navigationBarColor = Color.rgb(8, 10, 16)
        window.decorView.systemUiVisibility = 0

        credentialStorage = DeviceCredentialStorage(applicationContext)
        credentials = credentialStorage.load()
        credentials?.let {
            pcBaseUrl = it.pcBaseUrl
            deviceId = it.deviceId
        }

        val scroll = ScrollView(this).apply {
            setBackgroundColor(bg)
            clipToPadding = false
            isFillViewport = true
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
        onlineChip = TextView(this).apply {
            text = "●  Not paired"
            textSize = 12f
            setTextColor(muted)
            setPadding(dp(10), dp(7), dp(10), dp(7))
            background = rounded(panel2, 30)
        }
        top.addView(onlineChip)
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

        // --- Pairing (shown until this phone is paired with a PC) ---
        root.addView(space(22))
        pairCard = card()
        pairCard.addView(label("PAIR WITH YOUR PC", 12f, accent))
        val addressInput = field("PC address, e.g. http://192.168.1.20:8000", InputType.TYPE_TEXT_VARIATION_URI)
        val offerInput = field("Offer ID shown on your PC", InputType.TYPE_CLASS_TEXT)
        val codeInput = field("6-digit code", InputType.TYPE_CLASS_NUMBER)
        pairCard.addView(addressInput, fieldParams())
        pairCard.addView(offerInput, fieldParams())
        pairCard.addView(codeInput, fieldParams())
        val pairButton = Button(this).apply {
            text = "Pair this phone"
            textSize = 14f
            setTextColor(Color.WHITE)
            background = rounded(accent, 16)
            isAllCaps = false
            setOnClickListener {
                pair(
                    addressInput.text.toString().trim(),
                    offerInput.text.toString().trim(),
                    codeInput.text.toString().trim()
                )
            }
        }
        pairCard.addView(pairButton, LinearLayout.LayoutParams(-1, dp(52)).apply { topMargin = dp(10) })
        root.addView(pairCard)

        // --- Command surface ---
        root.addView(space(14))
        val taskCard = card()
        taskCard.addView(label("ASK ZYRA", 12f, accent))
        val input = field("App name, folder path or https:// link", InputType.TYPE_CLASS_TEXT)
        taskCard.addView(input, fieldParams())
        val run = Button(this).apply {
            text = "Run with ZYRA"
            textSize = 14f
            setTextColor(Color.WHITE)
            background = rounded(accent, 16)
            isAllCaps = false
            setOnClickListener { runOnPc(input.text.toString().trim()) }
        }
        taskCard.addView(run, LinearLayout.LayoutParams(-1, dp(52)).apply { topMargin = dp(10) })
        resultView = label("", 13f, muted)
        taskCard.addView(resultView, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(10) })
        root.addView(taskCard)

        root.addView(space(14))
        val status = card()
        val statusHeader = TextView(this).apply {
            text = "PC STATUS"
            textSize = 12f
            setTextColor(muted)
        }
        status.addView(statusHeader)
        agentValue = label("", 14f, muted)
        accessValue = label("", 14f, muted)
        protectionValue = label("", 14f, muted)
        status.addView(row("Agent", agentValue))
        status.addView(row("Remote access", accessValue))
        status.addView(row("Protection", protectionValue))
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
        actions.addView(action("Check PC") { checkPc() }, weightParams())
        actions.addView(action("Devices") { listSessions() }, weightParams().apply { marginStart = dp(8) })
        actions.addView(action("Unpair") { unpair() }, weightParams().apply { marginStart = dp(8) })
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
        renderPairingState()
    }

    // --- Pairing state ---------------------------------------------------------

    private fun renderPairingState() {
        val paired = credentials != null
        pairCard.visibility = if (paired) View.GONE else View.VISIBLE
        if (paired) {
            onlineChip.text = "●  Paired"
            onlineChip.setTextColor(success)
            agentValue.text = "Not checked"
            agentValue.setTextColor(muted)
            accessValue.text = "Session-based"
            accessValue.setTextColor(success)
            protectionValue.text = "Active"
            protectionValue.setTextColor(success)
        } else {
            onlineChip.text = "●  Not paired"
            onlineChip.setTextColor(muted)
            agentValue.text = "Unavailable"
            agentValue.setTextColor(muted)
            accessValue.text = "Off until paired"
            accessValue.setTextColor(muted)
            protectionValue.text = "Active"
            protectionValue.setTextColor(success)
        }
    }

    private fun showResult(message: String, ok: Boolean) {
        runOnUiThread {
            resultView.text = message
            resultView.setTextColor(if (ok) success else danger)
        }
    }

    private fun pair(address: String, offerId: String, code: String) {
        if (!isPrivateLanEndpoint(address)) {
            showResult("Use your PC's local network address (for example http://192.168.1.20:8000).", false)
            return
        }
        if (offerId.isEmpty() || code.length != 6) {
            showResult("Enter the offer ID and 6-digit code shown on your PC.", false)
            return
        }
        showResult("Pairing…", true)
        thread {
            try {
                val result = PairingHttpTransport(address, enrollPath = PAIRING_ENROLL_PATH)
                    .enroll(offerId, code, requestedPairingCapabilities().toList())
                val saved = DeviceCredentials(
                    pcBaseUrl = address.trimEnd('/'),
                    deviceId = result.deviceId,
                    deviceSecret = result.deviceSecret,
                    capabilities = result.capabilities
                )
                credentialStorage.save(saved)
                credentials = saved
                pcBaseUrl = saved.pcBaseUrl
                deviceId = saved.deviceId
                runOnUiThread { renderPairingState() }
                showResult("Paired. This phone can now send commands to your PC.", true)
            } catch (e: Exception) {
                showResult(e.message ?: "Pairing failed.", false)
            }
        }
    }

    private fun unpair() {
        thread {
            sessionManagerOrNull()?.let { runCatching { it.logout() }; it.clearLocalSession() }
            credentialStorage.clear()
            credentials = null
            pcBaseUrl = ""
            deviceId = ""
            sessionId = ""
            runOnUiThread { renderPairingState() }
            showResult("This phone is no longer paired.", true)
        }
    }

    // --- PC networking -----------------------------------------------------------
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
     * user-visible, reviewable set of PC permissions. PairingHttpTransport
     * maps these to the PC agent's grant names. */
    private fun requestedPairingCapabilities(): JSONArray {
        return JSONArray()
            .put("windows.apps")
            .put("windows.files.read")
            .put("windows.browser")
    }

    private fun JSONArray.toList(): List<String> = (0 until length()).map { getString(it) }

    private fun sessionManagerOrNull(): SessionManager? {
        val creds = credentials ?: return null
        if (!isPrivateLanEndpoint(creds.pcBaseUrl)) return null
        return SessionManager(
            applicationContext,
            ZyraHttpTransport(creds.pcBaseUrl, deviceSecret = { creds.deviceSecret })
        )
    }

    /** Returns an active, Keystore-persisted session, refreshing or creating one as needed. */
    private fun activeSession(): AuthenticatedTransportSession? {
        val creds = credentials ?: return null
        val manager = sessionManagerOrNull() ?: return null
        val session = AuthenticatedTransportSession.from(manager.ensureActive(creds.deviceId)) ?: return null
        deviceId = session.deviceId
        sessionId = session.sessionId
        return session
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

    private fun runOnPc(request: String) {
        if (credentials == null) {
            showResult("Pair this phone with your PC first.", false)
            return
        }
        if (request.isEmpty()) {
            showResult("Type an app name, folder path or link first.", false)
            return
        }
        val (action, payload) = when {
            request.startsWith("http://") || request.startsWith("https://") ->
                "open_url" to JSONObject().put("url", request)
            request.contains("\\") || Regex("^[A-Za-z]:").containsMatchIn(request) ->
                "open_folder" to JSONObject().put("path", request)
            else -> "open_app" to JSONObject().put("name", request)
        }
        showResult("Sending to your PC…", true)
        thread {
            try {
                val session = activeSession() ?: return@thread showResult("Could not start a secure session.", false)
                val response = RemoteCommandHttpTransport(pcBaseUrl).execute(session, action, payload)
                showResult(
                    if (response.accepted) "Done: ${response.message.ifBlank { response.status }}"
                    else "PC refused: ${response.message.ifBlank { response.status }}",
                    response.accepted
                )
            } catch (e: Exception) {
                showResult(e.message ?: "PC unreachable.", false)
            }
        }
    }

    private fun checkPc() {
        if (credentials == null) {
            showResult("Pair this phone with your PC first.", false)
            return
        }
        thread {
            val ok = try {
                val connection = URL(pcBaseUrl.trimEnd('/') + "/health").openConnection() as HttpURLConnection
                connection.connectTimeout = 4000
                connection.readTimeout = 4000
                val good = connection.responseCode == 200
                connection.disconnect()
                good
            } catch (_: Exception) {
                false
            }
            runOnUiThread {
                onlineChip.text = if (ok) "●  PC online" else "●  PC unreachable"
                onlineChip.setTextColor(if (ok) success else danger)
                agentValue.text = if (ok) "Ready" else "Unreachable"
                agentValue.setTextColor(if (ok) success else danger)
            }
        }
    }

    private fun listSessions() {
        if (credentials == null) {
            showResult("Pair this phone with your PC first.", false)
            return
        }
        thread {
            try {
                activeSession() ?: return@thread showResult("Could not start a secure session.", false)
                val json = postJson("/v1/session/list", buildAuthenticatedPayload())
                val summary = json?.optJSONObject("summary")
                showResult(
                    if (summary == null) "Could not read sessions."
                    else "${summary.optInt("active")} active session(s) for this phone.",
                    summary != null
                )
            } catch (e: Exception) {
                showResult(e.message ?: "PC unreachable.", false)
            }
        }
    }

    // --- UI helpers ----------------------------------------------------------------

    private fun card(): LinearLayout = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        setPadding(dp(16), dp(16), dp(16), dp(16))
        background = rounded(panel, 20)
        elevation = dp(1).toFloat()
    }

    private fun field(hint: String, type: Int) = EditText(this).apply {
        this.hint = hint
        inputType = type
        textSize = 15f
        setTextColor(primaryText)
        setHintTextColor(muted)
        setSingleLine(true)
        setPadding(dp(16), dp(14), dp(16), dp(14))
        background = rounded(Color.rgb(29, 33, 46), 16)
    }

    private fun fieldParams() = LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(10) }

    private fun row(title: String, value: TextView): View {
        val r = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(0, dp(9), 0, dp(2))
        }
        r.addView(label(title, 14f, muted), LinearLayout.LayoutParams(0, -2, 1f))
        r.addView(value)
        return r
    }

    private fun action(title: String, onClick: () -> Unit): Button = Button(this).apply {
        text = title
        textSize = 12f
        setTextColor(primaryText)
        isAllCaps = false
        background = rounded(panel2, 14)
        setOnClickListener { onClick() }
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
