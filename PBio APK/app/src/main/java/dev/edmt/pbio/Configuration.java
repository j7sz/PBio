package dev.edmt.pbio;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.security.keystore.KeyProperties;
import android.security.keystore.KeyProtection;
import android.text.TextUtils;
import android.util.Base64;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.Toast;

import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

import java.security.KeyStore;
import java.security.NoSuchAlgorithmException;

import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;

public class Configuration extends Activity {

//  Declaration for  cache storage
    SharedPreferences sharedPref;
    public static final String MyPREFERENCES = "myprefs";
    SharedPreferences.Editor editor;

//    Declaration for interface object variables
    EditText etID;
    EditText etOTP;     // OTP is hidden, you may set its visibility in the layout
    EditText etIP;
    Button btnSave;
    Button btnReqOTP;
    Button btnCancel;

    String user_id;
    LinearLayout ipaddrLayout;
    String ipaddr ;

//  Declaration for secure keystore variable
    KeyGenerator keyGenerator;  // Java Key generator used to import the android keystore
    SecretKey secretKey;        // Java AES Key
    byte[] secretKeyen;
    String strSecretKey;
    byte[] IV = new byte[16];


    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_configuration);

//        Initiate cache storage
        sharedPref = getSharedPreferences(MyPREFERENCES, Context.MODE_PRIVATE);
        editor = sharedPref.edit();

//        Set interface object references
        etID = (EditText)findViewById(R.id.etID);
        etIP = (EditText)findViewById(R.id.etIPaddr) ;
        btnSave = (Button)findViewById(R.id.saveBtn);
        btnReqOTP = (Button)findViewById(R.id.btn_OTP);
        btnCancel = (Button)findViewById(R.id.cancelBtn);

//        Set IP field. By right it's hidden, but for debugging purpose, we may show its visibility for the very first time
        ipaddrLayout = (LinearLayout)findViewById(R.id.ipaddrLayout);
        ipaddr = sharedPref.getString("cloud_ipaddr", "");
        if(ipaddr.equals("")){
            ipaddr = getResources().getString(R.string.cloudipaddr);
            ipaddrLayout.setVisibility(View.VISIBLE);
        }
        etIP.setText(ipaddr);

        user_id = sharedPref.getString("etxt_id", "");
        etID.setText(user_id);

//        This button is disabled as it's done automatically in Save. One may show it to manually request OTP
/*
        btnReqOTP.setOnClickListener(new View.OnClickListener(){
            @Override
            public void onClick(View view){
                ipaddr = String.valueOf(etIP.getText());
                try {
                    RequestOTP();
                } catch (Exception e){
                    new AlertDialog.Builder(Configuration.this)
                            .setTitle("Connection Error")
                            .setMessage("Please ensure IP Addr is correct").show();
                    ipaddrLayout.setVisibility(View.VISIBLE);
                }
            }
        });
 */

//      This button is disabled. One may show it to show user for cancelling the changes
/*
        btnCancel.setOnClickListener(new View.OnClickListener(){
            @Override
            public void onClick(View view){
                finish();
            }
        });
*/


        btnSave.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                if (TextUtils.isEmpty(etID.getText()) ) {
                    Toast.makeText(Configuration.this, "Please fill up your ID.", Toast.LENGTH_SHORT).show();
                }
                else{

                ipaddr = String.valueOf(etIP.getText());
//                Call RequestOTP() function to retrieve OTP from server
//                    This serves a 2FA with the server
                try {
                    RequestOTP();
                } catch (Exception e){
                    new AlertDialog.Builder(Configuration.this)
                            .setTitle("Connection Error")
                            .setMessage("Please ensure IP Addr is correct").show();
                    ipaddrLayout.setVisibility(View.VISIBLE);
                }


//                Request user key from server
//                 Note that one must request a valid OTP from server
//                    OTP will expire without in 1minute
                String otp = btnReqOTP.getText().toString();
                final String key = Get_key(etID.getText().toString(), ipaddr, otp);

//              This error shows that user ID doesn't exists
                if(key.equals("401")){
                    new AlertDialog.Builder(Configuration.this)
                            .setTitle("Unable to retrieve key")
                            .setMessage("Please ensure the ID exists.").show();

                }else if(key.equals("404")){
//                    This error shows that there is connection error
//                    One may either server problem or device connection problem. e.g. incorrect ip addr
                    new AlertDialog.Builder(Configuration.this)
                            .setTitle("Unable to retrieve key")
                            .setMessage("Please ensure the server is online.").show();
                    ipaddrLayout.setVisibility(View.VISIBLE);

                }
                else{
                    new AlertDialog.Builder(Configuration.this)
                            .setTitle("Save")
                            .setMessage("Are you sure you want to save this entry?")
                            // Specifying a listener allows you to take an action before dismissing the dialog.
                            // The dialog is automatically dismissed when a dialog button is clicked.
                            .setPositiveButton(android.R.string.yes, new DialogInterface.OnClickListener() {
                                public void onClick(DialogInterface dialog, int which) {
                                    // Continue with delete operation
                                    try {
                                        keyGenerator = KeyGenerator.getInstance("AES");
                                    } catch (NoSuchAlgorithmException e) {
                                        e.printStackTrace();
                                    }
                                    // The hard code key String we are going to use :
                                    String hardcodekey = key;

                                    // Key generation
                                    keyGenerator.init(256);
                                    secretKey = keyGenerator.generateKey();
                                    secretKeyen=secretKey.getEncoded();
                                    strSecretKey = encoderfun(secretKeyen);


                                    // Use password to load key in the android key store with name "key2"
                                    String password = "someString";
                                    char[] charArray = password.toCharArray();

                                    SecretKey keyStoreKey=null;
                                    try {
                                        KeyStore keyStore = KeyStore.getInstance("AndroidKeyStore");
                                        keyStore.load(null);
                                        keyStoreKey = (SecretKey) keyStore.getKey("key2", charArray);
                                        // when the app run on the phone 1st time generate the key2 in the keystore
                                        if(keyStoreKey==null) {
                                            keyStore.setEntry(
                                                    "key2",
                                                    new KeyStore.SecretKeyEntry(secretKey),
                                                    new KeyProtection.Builder(KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                                                            .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                                                            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                                                            .build());
                                            keyStoreKey = (SecretKey) keyStore.getKey("key2", charArray);
                                        }

                                        // Key imported, obtain a reference to it.
                                        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
                                        cipher.init(Cipher.ENCRYPT_MODE, keyStoreKey);
                                        IV = cipher.getIV();
                                        byte[] encodedBytes = cipher.doFinal(new String(hardcodekey).getBytes("UTF-8"));

                                        editor.putString("etxt_id", String.valueOf(etID.getText()));
                                        editor.putString("cipher", encoderfun(encodedBytes));
                                        editor.putString("IV", encoderfun(IV));
                                        editor.putString("cloud_ipaddr", String.valueOf(etIP.getText()));

                                        editor.commit();
                                        go_to_menu();
                                        finish();
                                    } catch (Exception e){
                                        e.printStackTrace();
                                        Toast.makeText(Configuration.this, "Error occurs while generating new user key", Toast.LENGTH_LONG).show();
                                    }
                                }
                            })

                            // A null listener allows the button to dismiss the dialog and take no further action.
                            .setNegativeButton(android.R.string.no, null)
                            .show();
                }

                }

            }
        });
    }

//    Go back to login selection page
    public void go_to_menu(){
        Intent i=new Intent(Configuration.this, LoginSelection.class);
        startActivity(i);
    }


//    A request OTP function that serves as 2FA with the server
//    This call Get_otp() function to request a key. This also servers a function to check the availability
    public void RequestOTP(){
        if (TextUtils.isEmpty(etID.getText()) ){
            Toast.makeText(Configuration.this, "Please fill up your ID.", Toast.LENGTH_SHORT).show();
        }else{
            final String otp = Get_otp(etID.getText().toString(), ipaddr);
            if (otp.equals("404")){
                Toast.makeText(Configuration.this, "Connection not found. Please check the IP Addr", Toast.LENGTH_SHORT).show();
            }else if(otp.equals("401")){
                Toast.makeText(Configuration.this, "Incorrect ID", Toast.LENGTH_SHORT).show();
            }
            else{
                btnReqOTP.setText(otp);
            }
        }
    }

//    On request OTP, return OTP from server by calling python function
    public String Get_otp(String id, String ipaddr) {
        if (!Python.isStarted())
            Python.start(new AndroidPlatform(getApplicationContext()));
        Python py = Python.getInstance();
        PyObject pyf = py.getModule("python");
        PyObject obj = pyf.callAttr("request_otp", id, ipaddr);

        return obj.toString();
    }

//    Call a python function to request user key
//    an OTP requires to serve as 2FA
    public String Get_key(String id, String ipaddr, String OTP){
        if (!Python.isStarted())
            Python.start(new AndroidPlatform(getApplicationContext()));
        Python py = Python.getInstance();
        PyObject pyf = py.getModule("python");
        PyObject obj = pyf.callAttr("request_key", id, ipaddr, OTP);

        return obj.toString();
    }

    public static String encoderfun(byte[] decval) {
        String conVal= Base64.encodeToString(decval,Base64.DEFAULT);
        return conVal;
    }

}