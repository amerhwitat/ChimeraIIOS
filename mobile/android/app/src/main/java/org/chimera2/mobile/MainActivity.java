package org.chimera2.mobile;
import android.app.Activity; import android.os.Bundle; import android.widget.TextView;
public final class MainActivity extends Activity { @Override public void onCreate(Bundle state) { super.onCreate(state); TextView v=new TextView(this); v.setText("Chimera II OS Mobile\nKoronos • RegisterN • Aurora"); v.setTextSize(20); v.setPadding(32,48,32,48); setContentView(v); } }
