package com.zyra

import android.app.Activity
import android.os.Bundle
import android.widget.LinearLayout
import android.widget.TextView

class MainActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(48, 48, 48, 48)
        }
        root.addView(TextView(this).apply {
            text = "ZYRA AI"
            textSize = 30f
        })
        root.addView(TextView(this).apply {
            text = "Android Beta • Secure companion"
            textSize = 18f
        })
        root.addView(TextView(this).apply {
            text = "Session, device pairing, realtime transport and transfer modules are bundled in this beta build."
            textSize = 16f
            setPadding(0, 32, 0, 0)
        })
        setContentView(root)
    }
}
