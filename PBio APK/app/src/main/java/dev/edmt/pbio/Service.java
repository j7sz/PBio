package dev.edmt.pbio;

import android.content.Intent;
import android.os.Bundle;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;

public class Service extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_service);
        Intent intent = getIntent();
        String service = intent.getStringExtra("service");

        TextView tv = (TextView) findViewById(R.id.txt_service);
//        tv.setText(tv.getText()+service);
    }
}