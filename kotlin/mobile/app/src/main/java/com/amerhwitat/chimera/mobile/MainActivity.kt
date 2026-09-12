package com.amerhwitat.chimera.mobile
import android.app.Activity
import android.os.Bundle
import android.view.Gravity
import android.widget.*
class MainActivity:Activity(){override fun onCreate(savedInstanceState:Bundle?){super.onCreate(savedInstanceState);val r=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL;gravity=Gravity.CENTER;setPadding(32,32,32,32)};val t=TextView(this).apply{text="Chimera II OS — Kotlin Mobile";textSize=24f;gravity=Gravity.CENTER};val s=TextView(this).apply{text="Mobile Microkernel boundary: ready\nKoronos mobile services: ready\n128D state: ready\nTrusted P2P: opt-in only";textSize=16f;gravity=Gravity.CENTER;setPadding(0,24,0,24)};val b=Button(this).apply{text="Start mobile runtime";setOnClickListener{s.text="Spit Fire mobile gate: ready\nKoronos services: active\n128D state: active\nTrusted P2P: awaiting peer"}};r.addView(t);r.addView(s);r.addView(b);setContentView(r)}}
