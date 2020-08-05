import cv2
from PIL import Image
import io
from PBio import *
import requests

# A global variable
# To make it dynamic, you may put it as a reference for functions that needed this
SubName = "X-Bank"

# A start-up function to let android load python library
def warm_up(option):
    return "Python Code is working...."

# Encoder function to map float number to int
# As GSHADE supports max 255, we should convert the float number to maximum 255
def scale_encode(v, s=12):
    t = np.rint( (v + 8)*s )
    return np.asarray(t, dtype=np.int)

# Decoder function to map int back to float
def scale_decode(d, s=12):
    return d/(s*s)

# A function that extract face features
# Encrypt the feature using user key
def prepare(name, byte,key):
    dim = 128

    # Start extraction
    extract_time = time.time()
    byte = bytearray.fromhex(byte)
    image = np.array(Image.open(io.BytesIO(byte)))
    compress_img = cv2.resize(image, (0, 0), fx=0.25, fy=0.25)
    try:
        encode = face_recognition.face_encodings(compress_img)
    except Exception as e:
        print("Error in recognition", e)
    extract_time = time.time() - extract_time
    # End extraction

    # Start Encryption
    enc_time = time.time()
    UserKey = key
    encode = Enc( UserKey, name, encode[0], dim)
    v1, v2 = np.split(encode[0], 2)
    ev2 = ReEnc( UserKey, SubName, v2, len(v1))[0]
    enc_time = time.time() - enc_time
    # Enc encryption

    # Encode float number to int
    v1 = scale_encode(v1)
    ev2 = scale_encode(ev2)

    return [v1.tolist(), ev2.tolist(), extract_time, enc_time]

# A function to check the similarity of partial distance from subscriber
# It will generate encrypted threshold as well
def ver_sub_distance(id, usk, sub_distance):
    # Decode int distance back to float
    decode_sub_distance = scale_decode(sub_distance)
    # Encrypt tolerance/threshold
    tolerance = Enc_t(usk, id, 0.6)
    tolerance = Enc_t(usk, SubName, tolerance)
    tolerance = tolerance * tolerance
    # Check the similarity
    partial_auth_result = decode_sub_distance <= tolerance
    return partial_auth_result, tolerance, decode_sub_distance

# A function to combine and check the full distance
def ver_cloud_distance(usk, decode_sub_distance, cloud_distance, tolerance):
    # Decode int distance back to float
    decode_cloud_distance = scale_decode(cloud_distance)
    # Regenerate scale product
    w = Output_w_Enc_t(usk, SubName)
    # Compute full distance
    full_distance = decode_sub_distance + (decode_cloud_distance * w * w)
    # Check the similarity
    full_auth_result = full_distance <= tolerance
    return full_auth_result

# An acknowledge request to subscriber
# To ask for prepare GSHADE
# Exception returns if user ID doesnt exist
def sub_auth(id, ipaddr):
    url = "http://"+ipaddr+":5001/sub_auth"
    data = {'id': id}
    try:
        response = requests.post(url, json=data, timeout=2)
        try:
            status = response.json()['status']
            if status == '200':
                return '200'
            else:
                return '401'
        except:
            return '401'
    except Exception as e:
        return '404'

# An acknowledge request to cloud
# To ask for prepare GSHADE
# Exception returns if user ID doesnt exist
def cloud_auth(id, ipaddr):
    url = "http://"+ipaddr+":5001/cloud_auth"
    data = {'id': id}
    try:
        response = requests.post(url, json=data, timeout=2)
        try:
            status = response.json()['status']
            if status == '200':
                return '200'
            else:
                return '401'
        except:
            return '401'
    except Exception as e:
        return '404'

# Fpr experiment purpose
# We forward the result back to the server
# By right, one should forward 1/0 to indicate authentication success or failure
def forward_auth_result(id, ipaddr, auth_final_result, enc_time, extract_time, sub_ver_time, cloud_ver_time=0):
    url = "http://" + ipaddr + ":5001/exp_result_collector"
    data = {"id": id, "date":time.time(), "auth_result": auth_final_result, "enc_time": enc_time, "extract_time":extract_time,
            "ver_time":sub_ver_time+cloud_ver_time, "sub_ver_time":sub_ver_time, "cloud_ver_time":cloud_ver_time}
    try:
        response = requests.post(url, json=data, timeout=2)
        try:
            status = response.json()['status']
        except Exception as e:
            print("Something goes wrong", str(e))
    except Exception as e:
        print("Connection error\n"+str(e))

# A function to request OTP
# We need this as 2FA
def request_otp(id, ipaddr):
    url = "http://"+ipaddr+":5001/requestOTP"
    data = {'id': id}
    try:
        response = requests.post(url, json=data, timeout=2)
        try:
            otp = response.json()['OTP']
            return otp
        except:
            return '401'
    except Exception as e:
        return '404'
    except:
        return '404'

# Request a user key
def request_key(id, ipaddr, otp):
    url = "http://" + ipaddr + ":5001/temp"
    data = {'id': id, 'otp':otp}
    try:
        response = requests.post(url, json=data, timeout=2)
        try:
            key = response.json()['key']
            return key
        except Exception as e:
            return "401"
    except Exception as e:
        return "404"

