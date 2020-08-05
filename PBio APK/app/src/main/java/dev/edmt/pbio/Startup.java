package dev.edmt.pbio;

import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;

import androidx.appcompat.app.AppCompatActivity;

import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

public class Startup extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_startup);

        final Handler handler = new Handler();
        handler.postDelayed(new Runnable() {
            @Override
            public void run() {
                //Do something after 100ms
                python_warmup();
                Intent i=new Intent(Startup.this, LoginSelection.class);
                startActivity(i);
                finish();
            }
        }, 100);

    }

//    A startup function to load python library.
    private void python_warmup() {
        if (!Python.isStarted())
            Python.start(new AndroidPlatform(getApplicationContext()));
        Python py = Python.getInstance();
        PyObject pyf = py.getModule("python");
        PyObject obj = pyf.callAttr("warm_up", "0");
    }
}