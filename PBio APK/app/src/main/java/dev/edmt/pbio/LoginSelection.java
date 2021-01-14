package dev.edmt.pbio;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;

public class LoginSelection extends AppCompatActivity implements View.OnClickListener {

//    Preferences object, act as an android cache file
//    to check whether there user ID exists
    SharedPreferences sharedPref;
    public static final String MyPREFERENCES = "myprefs";
    SharedPreferences.Editor editor;

//    A startup function
    @Override
    protected void onCreate(Bundle savedInstanceState) {
//        Declare and link toolbar and buttons
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_login_selection);
        Toolbar toolbar = findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);

        Button setting = (Button) findViewById(R.id.btnSettings);
        setting.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                go_to_setting();
            }
        });

//        Link the preference object.
//        Check whether user ID exists
//        If no user ID exists, redirect user to setting page by calling
//        go_to_setting() function
        sharedPref = getSharedPreferences(MyPREFERENCES, Context.MODE_PRIVATE);
        String name = sharedPref.getString("etxt_id", "");
        if (name.equals("")) {
            go_to_setting();
            this.finish();
        }


//        Declare and link the list of subscirbers
        LinearLayout ll1 = (LinearLayout) findViewById(R.id.list_item1);
        LinearLayout ll2 = (LinearLayout) findViewById(R.id.list_item2);
        LinearLayout ll3 = (LinearLayout) findViewById(R.id.list_item3);
        LinearLayout ll4 = (LinearLayout) findViewById(R.id.list_item4);
        LinearLayout ll5 = (LinearLayout) findViewById(R.id.list_item5);
        LinearLayout ll6 = (LinearLayout) findViewById(R.id.list_item6);
        LinearLayout ll7 = (LinearLayout) findViewById(R.id.list_item7);
        LinearLayout ll8 = (LinearLayout) findViewById(R.id.list_item8);

        ll1.setOnClickListener(this);
        ll2.setOnClickListener(this);
        ll3.setOnClickListener(this);
        ll4.setOnClickListener(this);
        ll5.setOnClickListener(this);
        ll6.setOnClickListener(this);
        ll7.setOnClickListener(this);
        ll8.setOnClickListener(this);

    }

//    An onclick listener that learn which services that the user select
//    Pass the selected service to the next activity
//    TODO: In practice, one should pass the service IP address to the next activity
    @Override
    public void onClick(View v) {
        int service;
        switch (v.getId()){
            case R.id.list_item1:
                service = R.drawable.undefine;
                break;
            case R.id.list_item2:
                service = R.drawable.undefine;
                break;
            case R.id.list_item3:
                service = R.drawable.undefine;
                break;
            case R.id.list_item4:
                service = R.drawable.undefine;
                break;
            case R.id.list_item5:
                service = R.drawable.undefine;
                break;
            case R.id.list_item6:
                service = R.drawable.undefine;
                break;
            case R.id.list_item7:
                service = R.drawable.undefine;
                break;
            case R.id.list_item8:
                service = R.drawable.undefine;
                break;
            default:
                throw new IllegalStateException("Unexpected value: " + v.getId());
        }

//        Check whether user ID exists
//        navigate user to setting page if there is no user ID exists
//        otherwise, it navigate to user to authentication page
//        intent putExtra() allows one to pass which selected service to the next activity
//        TODO: One should also include the selected ip address to the next activity
        String name = sharedPref.getString("etxt_id", "");
        if (name.equals("")) {
            Toast.makeText(LoginSelection.this,"Please ensure you have setup your ID.", Toast.LENGTH_SHORT).show();
            go_to_setting();
        }else{
            Intent i=new Intent(LoginSelection.this, MainActivity.class);
            i.putExtra("service", service);
            startActivity(i);
        }

    }

//    A function to navigate to setting page
    public void go_to_setting(){
        Intent i=new Intent(LoginSelection.this, Configuration.class);
        startActivity(i);
    }


}