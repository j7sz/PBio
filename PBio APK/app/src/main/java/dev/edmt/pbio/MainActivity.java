package dev.edmt.pbio;

import android.Manifest;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.graphics.ImageFormat;
import android.graphics.Matrix;
import android.graphics.SurfaceTexture;
import android.hardware.camera2.CameraAccessException;
import android.hardware.camera2.CameraCaptureSession;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CameraDevice;
import android.hardware.camera2.CameraManager;
import android.hardware.camera2.CameraMetadata;
import android.hardware.camera2.CaptureRequest;
import android.hardware.camera2.TotalCaptureResult;
import android.hardware.camera2.params.StreamConfigurationMap;
import android.media.Image;
import android.media.ImageReader;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.HandlerThread;
import android.util.Base64;
import android.util.Size;
import android.util.SparseIntArray;
import android.view.Surface;
import android.view.TextureView;
import android.view.View;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;
import androidx.core.app.ActivityCompat;

import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.security.KeyStore;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Date;
import java.util.List;

import javax.crypto.Cipher;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

public class MainActivity extends AppCompatActivity {

//    Camera preview variables
    String mCurrentPhotoPath;
    Bitmap bitmap;
    static final int REQUEST_TAKE_PHOTO = 1;
    private TextureView textureView;
    private static final SparseIntArray ORIENTATIONS = new SparseIntArray();

    private String cameraId;
    private CameraDevice cameraDevice;
    private CameraCaptureSession cameraCaptureSessions;
    private CaptureRequest.Builder captureRequestBuilder;
    private Size imageDimension;

    private File file;
    private static final int REQUEST_CAMERA_PERMISSION = 200;
    private Handler mBackgroundHandler;
    private HandlerThread mBackgroundThread;

//    Page Variables
    Button btnCamera;
    TextView txt_status;
    int service;
    ImageView logo;

//      Cache variables
    SharedPreferences sharedPref;
    public static final String MyPREFERENCES = "myprefs";
    SharedPreferences.Editor editor;

    // Used to load the 'native-lib' library on application startup.
//    Load for GSHADE library
    static {
        System.loadLibrary("ndktest");
    }
//    Declare GSHADE functions
//    role() initiates gshade with role either client or server
    public native int role(int role, String ipaddr, int[] vec);
//    get_comp_time() retrieve computation time
    public native double get_comp_time();

//    Initialize camera preview declarations
    CameraDevice.StateCallback stateCallback = new CameraDevice.StateCallback() {
        @Override
        public void onOpened(@NonNull CameraDevice camera) {
            cameraDevice = camera;
            createCameraPreview();
        }

        @Override
        public void onDisconnected(@NonNull CameraDevice cameraDevice) {
            cameraDevice.close();
        }

        @Override
        public void onError(@NonNull CameraDevice cameraDevice, int i) {
            cameraDevice.close();
            cameraDevice = null;
        }
    };

    //    A startup function
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

//        Get the reference value from the previous intent, LoginSelection intent
        Intent intent = getIntent();
        service = intent.getIntExtra("service",0);

//        Initialize toolbar, declare onclick function
        Toolbar toolbar = findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);
        Button setting = (Button) findViewById(R.id.btnSettings);
        setting.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                go_to_setting();
            }
        });

//        Set interface variable references
        btnCamera = (Button)findViewById(R.id.btnCamera);
        textureView = (TextureView) findViewById(R.id.textureView1);
        assert textureView != null;
        textureView.setSurfaceTextureListener(textureListener);
        logo = (ImageView)findViewById(R.id.imgViewLogo);
        logo.setImageResource(service);
        txt_status = (TextView)findViewById(R.id.textView);

//        Initialize cache object
        sharedPref = getSharedPreferences(MyPREFERENCES, Context.MODE_PRIVATE);
        editor = sharedPref.edit();
//      Check if there is exists user ID in cache
        String name = sharedPref.getString("etxt_id", "");
        if (name.equals("")) {
            txt_status.setText("Please go to settings to setup PBio");
            btnCamera.setVisibility(View.GONE);
            go_to_setting();
        }else{
            txt_status.setText("Please capture your face to authenticate");
            btnCamera.setVisibility(View.VISIBLE);
        }

//      Define btnCamera functions.
//        It first capture image takePicture()
//        Wait for 500ms for processing image, such as store and read as same device couldn't read it directly
//        proceed to python_auth() to run GSHADE, a secure distance computation
//        Lastly, refresh camera preview
        btnCamera.setOnClickListener(new View.OnClickListener() {


            @Override
            public void onClick(View view) {
                txt_status.setTextColor(Color.BLACK);
                txt_status.setText("Authenticating......");

                Toast.makeText(MainActivity.this,"Authenticating......", Toast.LENGTH_LONG).show();

                final Handler handler = new Handler();
                handler.postDelayed(new Runnable() {
                    @Override
                    public void run() {
                        try {
                            txt_status.setText("Capturing image...");
                            takePicture();
                            txt_status.setText("Image Captured");
                            // Wait for 500ms to process image
                            Thread.sleep(500);
                            python_auth();
                            createCameraPreview();
                        } catch (Exception e){
                            txt_status.setTextColor(getResources().getColor(R.color.orange));
                            txt_status.setText("Warning: Unable to detect face");
                            createCameraPreview();
                        }
                    }
                }, 100);
            }
        });

    }

//     Navigate to setting page
    public void go_to_setting(){
        Intent i=new Intent(MainActivity.this, Configuration.class);
        startActivity(i);
    }

//  A function to capture the preview photo
//    For some device, we must store the photo to a storage and read back
//    Otherwise, the device uses the thumbnail instead of full image
    private void takePicture() {
        if (cameraDevice == null)
            return;

        CameraManager manager = (CameraManager) getSystemService(Context.CAMERA_SERVICE);
        try {
            CameraCharacteristics characteristics = manager.getCameraCharacteristics(cameraDevice.getId());
            Size[] jpegSizes = null;
            if (characteristics != null)
                jpegSizes = characteristics.get(CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP)
                        .getOutputSizes(ImageFormat.JPEG);

            //Capture image with custom size
            int width = 300;
            int height = 400;
            if (jpegSizes != null && jpegSizes.length > 0) {
                width = jpegSizes[0].getWidth();
                height = jpegSizes[0].getHeight();
            }
            final ImageReader reader = ImageReader.newInstance(width, height, ImageFormat.JPEG, 1);
            List<Surface> outputSurface = new ArrayList<>(2);
            outputSurface.add(reader.getSurface());
            outputSurface.add(new Surface(textureView.getSurfaceTexture()));

            final CaptureRequest.Builder captureBuilder = cameraDevice.createCaptureRequest(CameraDevice.TEMPLATE_STILL_CAPTURE);
            captureBuilder.addTarget(reader.getSurface());
            captureBuilder.set(CaptureRequest.CONTROL_MODE, CameraMetadata.CONTROL_MODE_AUTO);

            //Check orientation base on device
            int rotation = getWindowManager().getDefaultDisplay().getRotation();
            captureBuilder.set(CaptureRequest.JPEG_ORIENTATION, ORIENTATIONS.get(rotation));

//            Set the file location
            try {
                file = createImageFile();
                // Save a file: path for use with ACTION_VIEW intents
                mCurrentPhotoPath = file.getAbsolutePath();
            } catch (IOException e) {
                e.printStackTrace();
            }

//          Convert the preview image to bytes and save via save() function
            ImageReader.OnImageAvailableListener readerListener = new ImageReader.OnImageAvailableListener() {
                @Override
                public void onImageAvailable(ImageReader imageReader) {
                    Image image = null;
                    try {
                    image = reader.acquireLatestImage();
                    ByteBuffer buffer = image.getPlanes()[0].getBuffer();
                    byte[] bytes = new byte[buffer.capacity()];
                    buffer.get(bytes);
//                    str_bytes = convert_img_to_byte(bytes);
                        save(bytes);

                    } catch (FileNotFoundException e) {
                        e.printStackTrace();
                    } catch (IOException e) {
                        e.printStackTrace();
                    } finally {
                        {
                            if (image != null)
                                image.close();
                        }
                    }
                }

//                We must save the image to storage and read it back
//                Otherwise, the capture image is a thumbnail, which resolution is too very low.
//                While reading back from the storage, we can retrieve the full image.
                private void save(byte[] bytes) throws IOException {
                    OutputStream outputStream = null;
                    try {
                        outputStream = new FileOutputStream(file);
                        outputStream.write(bytes);
                        access_bitmap(1);
                    } finally {
                        if (outputStream != null)
                            outputStream.close();
                    }
                }
            };

            reader.setOnImageAvailableListener(readerListener, mBackgroundHandler);
            final CameraCaptureSession.CaptureCallback captureListener = new CameraCaptureSession.CaptureCallback() {
                @Override
                public void onCaptureCompleted(@NonNull CameraCaptureSession session, @NonNull CaptureRequest request, @NonNull TotalCaptureResult result) {
                    super.onCaptureCompleted(session, request, result);
                    //to restart camera preview
                    //createCameraPreview();
                }
            };

            cameraDevice.createCaptureSession(outputSurface, new CameraCaptureSession.StateCallback() {
                @Override
                public void onConfigured(@NonNull CameraCaptureSession cameraCaptureSession) {
                    try {
                        cameraCaptureSession.capture(captureBuilder.build(), captureListener, mBackgroundHandler);
                    } catch (CameraAccessException e) {
                        e.printStackTrace();
                    }
                }

                @Override
                public void onConfigureFailed(@NonNull CameraCaptureSession cameraCaptureSession) {

                }
            }, mBackgroundHandler);


        } catch (CameraAccessException e) {
            e.printStackTrace();
        }
    }

//    An authentication function
//    It first read the user key from secure keystore
//    Extract the feature vectors from image
//    Performance encryption
//    Run GSHADE with subscriber server, reject and abort if this result is false
//    Run with cloud if and only if the preview result is true
    private void python_auth() {
        txt_status.setText("Authenticating image...");

//        Initialize python object, to run python function later
        if (!Python.isStarted())
            Python.start(new AndroidPlatform(getApplicationContext()));
        Python py = Python.getInstance();

//        Initialize default variables from cache, we assume cache is publicly known, hence it's nt
//        store in secure keystore
        String cloud_ipaddr = sharedPref.getString("cloud_ipaddr", getResources().getString(R.string.cloudipaddr));
        String name = sharedPref.getString("etxt_id", "");
        String encodedBytes2 = sharedPref.getString("cipher", "");
        String IV = sharedPref.getString("IV", "");
        String key = "";


        if (name.equals("") ){
            txt_status.setText("Please ensure you have configured you ID");
            return ;
        }

//      Read the user key from secure keystore
        SecretKey keyStoreKey=null;
        try {
            String password = "someString";
            char[] charArray = password.toCharArray();

            KeyStore keyStore = KeyStore.getInstance("AndroidKeyStore");
            keyStore.load(null);
            keyStoreKey = (SecretKey) keyStore.getKey("key2", charArray);
            // when the app run on the phone 1st time generate the key2 in the keystore
            if(keyStoreKey==null) {
                txt_status.setText("Please ensure you have configured your user ID.");
            }else{

                // Key imported, obtain a reference to it.
                Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
                cipher.init(Cipher.ENCRYPT_MODE, keyStoreKey);

                // decrypted
                Cipher dcipher = Cipher.getInstance("AES/GCM/NoPadding");

                byte[] bytesIV = Base64.decode(IV, Base64.DEFAULT);
                final GCMParameterSpec spec = new GCMParameterSpec(128, bytesIV);
                dcipher.init(Cipher.DECRYPT_MODE, ((KeyStore.SecretKeyEntry) keyStore.getEntry("key2", null)).getSecretKey(), spec);
                byte[] bytes = Base64.decode(encodedBytes2, Base64.DEFAULT);
                byte[] encodedBytes3 = dcipher.doFinal(bytes);
                // Set the java aes encrypt key:
                key = new  String(encodedBytes3, "UTF-8");
            }

        } catch (Exception e){
            txt_status.setText("Unable to retrieve user key.");
            e.printStackTrace();
        }


//        Compress the captured image
        ByteArrayOutputStream stream = new ByteArrayOutputStream();
        bitmap.compress(Bitmap.CompressFormat.JPEG, 90, stream);
        byte[] byteArray = stream.toByteArray();

//        Call python function, prepare() to compute encrypted vectors
        PyObject pyf = py.getModule("python");
        PyObject user_vec = pyf.callAttr("prepare",name, convert_img_to_byte(byteArray),key);
        List<PyObject> user_vec_list = user_vec.asList();
        int[] user_sub_vec = user_vec_list.get(1).toJava(int[].class);
        int[] user_cloud_vec = user_vec_list.get(0).toJava(int[].class);
//        For experiment purpose, we retrieve the computation time required
        double extract_time = user_vec_list.get(2).toJava(double.class);
        double enc_time = user_vec_list.get(3).toJava(double.class);

//        Call python function, sub_auth() to run acknowledge for GSHADE protocol.
//        Note that GSHADE is run with jni function, sub_auth() only ask server to listen a port
//        One should change cloud_ipaddr to sub_ipaddr, if there is subscriber server
//        For experiment purpose, we let subscriber server and cloud as the same party
        PyObject sub_auth = pyf.callAttr("sub_auth", name, cloud_ipaddr);
        if (String.valueOf(sub_auth).equals("200")){
//            This starts GSHADE with role() function via native library
//            For experiment purpose, we retrieve the computation time required
            txt_status.setText(String.valueOf("Authenticating..."));
            int sub_distance = role(1, cloud_ipaddr,user_sub_vec);
            double sub_ver_time = get_comp_time();

//            Call the python function, ver_sub_distance to verify the partial result
            PyObject sub_partial_result = pyf.callAttr("ver_sub_distance", name, key, sub_distance);
            List<PyObject> sub_partial_result_list = sub_partial_result.asList();
            boolean sub_result = sub_partial_result_list.get(0).toJava(boolean.class);
            double tolerance = sub_partial_result_list.get(1).toJava(double.class);
            double decode_sub_distance = sub_partial_result_list.get(2).toJava(double.class);

//          Check if the partial result (sub_result) is true
            if(sub_result==true){
                txt_status.setText(String.valueOf("Partial Success"));
//                Similar as previous, cloud_auth() from python to acknowledge for GHSADE
                PyObject cloud_auth = pyf.callAttr("cloud_auth", name, cloud_ipaddr);
                if (String.valueOf(cloud_auth).equals("200")){
    //            This starts GSHADE with role() function via native library
        //        One should carefully assign their cloud_ipaddr to sub_ipaddr
//              For experiment purpose, we let subscriber server and cloud as the same party
                    int cloud_distance = role(1, cloud_ipaddr,user_cloud_vec);
                    double cloud_ver_time = get_comp_time();

                    PyObject full_auth_result = pyf.callAttr("ver_cloud_distance", key, decode_sub_distance, cloud_distance, tolerance);
                    boolean final_result = full_auth_result.toJava(boolean.class);
                    if(final_result==true){
                        txt_status.setTextColor(Color.GREEN);
                        txt_status.setText(String.valueOf("Authentication Success"));
                        PyObject forwardAuthResult = pyf.callAttr("forward_auth_result", name, cloud_ipaddr, final_result, enc_time, extract_time, sub_ver_time, cloud_ver_time);
                    }
                    else{
                        txt_status.setTextColor(Color.RED);
                        txt_status.setText(String.valueOf("Authentication Failure"));
                        PyObject forwardAuthResult = pyf.callAttr("forward_auth_result", name, cloud_ipaddr, final_result, enc_time, extract_time, sub_ver_time, cloud_ver_time);
                    }
                }
            }else{
                txt_status.setTextColor(Color.RED);
                txt_status.setText(String.valueOf("Authentication Failure"));
                PyObject forwardAuthResult = pyf.callAttr("forward_auth_result", name, cloud_ipaddr, sub_result, enc_time, extract_time, sub_ver_time);
            }
        }
    }

//  Camera preview function
    private void createCameraPreview() {
        try {
            SurfaceTexture texture = textureView.getSurfaceTexture();
            assert texture != null;
            texture.setDefaultBufferSize(imageDimension.getWidth(), imageDimension.getHeight());
            Surface surface = new Surface(texture);
            captureRequestBuilder = cameraDevice.createCaptureRequest(CameraDevice.TEMPLATE_PREVIEW);
            captureRequestBuilder.addTarget(surface);
            cameraDevice.createCaptureSession(Arrays.asList(surface), new CameraCaptureSession.StateCallback() {
                @Override
                public void onConfigured(@NonNull CameraCaptureSession cameraCaptureSession) {
                    if (cameraDevice == null)
                        return;
                    cameraCaptureSessions = cameraCaptureSession;
                    updatePreview();
                }

                @Override
                public void onConfigureFailed(@NonNull CameraCaptureSession cameraCaptureSession) {
                    Toast.makeText(MainActivity.this, "Changed", Toast.LENGTH_SHORT).show();
                }
            }, null);
        } catch (CameraAccessException e) {
            e.printStackTrace();
        }
    }

//  Camera preview function
    private void updatePreview() {
        if (cameraDevice == null)
            Toast.makeText(this, "Error", Toast.LENGTH_SHORT).show();
        captureRequestBuilder.set(CaptureRequest.CONTROL_MODE, CaptureRequest.CONTROL_MODE_AUTO);
        try {
            cameraCaptureSessions.setRepeatingRequest(captureRequestBuilder.build(), null, mBackgroundHandler);
        } catch (CameraAccessException e) {
            e.printStackTrace();
        }
    }

    //  Camera preview function
    private void openCamera() {
        CameraManager manager = (CameraManager) getSystemService(Context.CAMERA_SERVICE);
        try {
            try{
                cameraId = getFrontFacingCameraId(manager);
            } catch (Exception e) {
                e.printStackTrace();
            }
            if(cameraId == null)
                cameraId = manager.getCameraIdList()[0];
            CameraCharacteristics characteristics = manager.getCameraCharacteristics(cameraId);
            StreamConfigurationMap map = characteristics.get(CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP);
            assert map != null;
            imageDimension = map.getOutputSizes(SurfaceTexture.class)[0];
            //Check realtime permission if run higher API 23
            if (ActivityCompat.checkSelfPermission(this, Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
                ActivityCompat.requestPermissions(this, new String[]{
                        Manifest.permission.CAMERA,
                        Manifest.permission.WRITE_EXTERNAL_STORAGE
                }, REQUEST_CAMERA_PERMISSION);
                return;
            }
            manager.openCamera(cameraId, stateCallback, null);

        } catch (CameraAccessException e) {
            e.printStackTrace();
        }
    }

    //  Camera preview function
    TextureView.SurfaceTextureListener textureListener = new TextureView.SurfaceTextureListener() {
        @Override
        public void onSurfaceTextureAvailable(SurfaceTexture surfaceTexture, int i, int i1) {
            openCamera();
        }

        @Override
        public void onSurfaceTextureSizeChanged(SurfaceTexture surfaceTexture, int i, int i1) {

        }

        @Override
        public boolean onSurfaceTextureDestroyed(SurfaceTexture surfaceTexture) {
            return false;
        }

        @Override
        public void onSurfaceTextureUpdated(SurfaceTexture surfaceTexture) {

        }
    };

    //  Camera preview function
    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        if (requestCode == REQUEST_CAMERA_PERMISSION) {
            if (grantResults[0] != PackageManager.PERMISSION_GRANTED) {
                Toast.makeText(this, "You can't use camera without permission", Toast.LENGTH_SHORT).show();
                finish();
            }
        }
    }

    //  Camera preview function
    @Override
    protected void onResume() {
        super.onResume();

        String name = sharedPref.getString("etxt_id", "");
        if (name.equals("")) {
            txt_status.setText("Please go to setting on top of menu options");
            btnCamera.setVisibility(View.GONE);
            //btnEncode.setVisibility(View.GONE);
        }else{
            txt_status.setText("Please capture your face and authenticate");
            btnCamera.setVisibility(View.VISIBLE);
            //btnEncode.setVisibility(View.VISIBLE);
        }

        startBackgroundThread();
        if (textureView.isAvailable()) {
            openCamera();
        }
        else
            textureView.setSurfaceTextureListener(textureListener);
    }

    //  Camera preview function
    @Override
    protected void onPause() {
        stopBackgroundThread();
        super.onPause();
    }

    //  Camera preview function
    private void stopBackgroundThread() {
        mBackgroundThread.quitSafely();
        try {
            mBackgroundThread.join();
            mBackgroundThread = null;
            mBackgroundHandler = null;
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    //  Camera preview function
    private void startBackgroundThread() {
        mBackgroundThread = new HandlerThread("Camera Background");
        mBackgroundThread.start();
        mBackgroundHandler = new Handler(mBackgroundThread.getLooper());
    }

    //  Camera preview function
    private String getFrontFacingCameraId(CameraManager cManager) {
        try {
            String cameraId;
            int cameraOrientation;
            CameraCharacteristics characteristics;
            for (int i = 0; i < cManager.getCameraIdList().length; i++) {
                cameraId = cManager.getCameraIdList()[i];
                characteristics = cManager.getCameraCharacteristics(cameraId);
                cameraOrientation = characteristics.get(CameraCharacteristics.LENS_FACING);
                if (cameraOrientation == CameraCharacteristics.LENS_FACING_FRONT) {
                    return cameraId;
                }

            }
        } catch (CameraAccessException e) {
            e.printStackTrace();
        }
        return null;
    }

//    Convert image to bytes and string
//    The string allows python function to detect and extract feature vectors
    public static String convert_img_to_byte(byte[] bytes) {
        StringBuilder sb = new StringBuilder();
        for (byte b : bytes) {
            sb.append(String.format("%02X", b));
        }
        return sb.toString();
    }

//  Store the preview image to a directory
//    This is necessary for some device, which doesn't permit us to read the preview image (resulted thumbnail)
    private File createImageFile() throws IOException {
        // Create an image file name
        String timeStamp = new SimpleDateFormat("yyyyMMdd_HHmmss").format(new Date());
        String imageFileName = "JPEG_" + timeStamp + "_";
        File storageDir = getExternalFilesDir(Environment.DIRECTORY_PICTURES);
        File image = File.createTempFile(
                imageFileName,  /* prefix */
                ".jpg",         /* suffix */
                storageDir      /* directory */
        );


        return image;
    }

//    Read the image from stored directory
    private void access_bitmap(int requestCode){
        try{
            if (requestCode == 1) {
                File imgFile = new  File(mCurrentPhotoPath);
                if(imgFile.exists()){
                    Bitmap myBitmap = BitmapFactory.decodeFile(imgFile.getAbsolutePath());
                    Matrix matrix = new Matrix();

//                   We must rotate the image
                    matrix.postRotate(270);

                    Bitmap scaledBitmap = Bitmap.createScaledBitmap(myBitmap, 640, 480, true);

                    Bitmap rotatedBitmap = Bitmap.createBitmap(scaledBitmap, 0, 0, scaledBitmap.getWidth(), scaledBitmap.getHeight(), matrix, true);

                    bitmap = rotatedBitmap;

                    File fdelete = new File(mCurrentPhotoPath);
                    if (fdelete.exists()) {
                        if (fdelete.delete()) {
                            System.out.println("file Deleted :" + mCurrentPhotoPath);
                        } else {
                            System.out.println("file not Deleted :" + mCurrentPhotoPath);
                        }
                    }

                }
            }
        }catch (Exception e){
            txt_status.setText("Please take a photo");
        }
    }


    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        access_bitmap(requestCode);
    }

}
