# This is a _very simple_ example of a web service that recognizes faces in uploaded images.
# Upload an image file and it will check if the image contains a picture of Barack Obama.
# The result is returned as json. For example:
#
# $ curl -XPOST -F "file=@obama2.jpg" http://127.0.0.1:5001
#
# Returns:
#
# {
#  "face_found_in_image": true,
#  "is_picture_of_obama": true
# }
#
# This example is based on the Flask file upload example: http://flask.pocoo.org/docs/0.12/patterns/fileuploads/

# NOTE: This example requires flask to be installed! You can install it with pip:
# $ pip3 install flask
import base64
import json
import math
import os
import pickle
import random
import sys
import time

from flask import Flask,flash, jsonify, request, redirect, render_template, url_for, Response, send_from_directory
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
import pathlib
from DataOwner import KeyGen, Enc, ReEnc, save_userkey


import numpy as np

import ctypes
from numpy.ctypeslib import ndpointer
import threading
import multiprocessing
import subprocess
import re
from string import Template
import csv
import face_recognition

cert_key = 'Cert/apache-selfsigned.key'
cert_cert = 'Cert/apache-selfsigned.crt'
context = (cert_cert, cert_key)  # certificate and key files

# You can change this to any folder on your system
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif','PNG','JPG','JPEG'}
UPLOAD_FOLDER = 'user_img'


# camera = Camera()
# camera.run()


UserKey_Path = 'Original/UserKeys.npy'
data_name = "Train_data_namelist.txt"
government_path_name = 'Government/Government_'
sub_share_path = "Subscriber/Subscriber_.npy"
cloud_share_path = "Cloud/Cloud_1.npy"

app = Flask(__name__, template_folder='pages')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# app.config['SECRET_KEY'] = 'secret!'
# socketio = SocketIO(app, logger=True, engineio_logger=True, async_handlers=True)
socketio = SocketIO(app, async_mode='threading', async_handlers=False)

connected_users = {}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        name = request.form.get('name')
        email = request.form.get('email')
        u_id = random.choice("SG")+gen_OTP(7)+random.choice("ABCDEFGHIJK")
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            path = os.path.join( app.config['UPLOAD_FOLDER'], u_id)
            os.mkdir(path)
            img_path = os.path.join(path, email+'_'+name+'_'+filename)
            file.save(img_path)
            status, user_feature = extract_feature(img_path, u_id)
            if status == 0:
               return '''
                   <!doctype html>
                    <title>Upload new File</title>
                    <h1>Upload Failure</h1>
                    <p>Unable to detect facial landmark.<br>Please ensure to upload a passport photo or a front-facing selfie.</p>
               ''' 
            else:
                ckey = load_key(government_path_name + "_key.txt")
                SubName = "DBS Bank"
                usk = KeyGen(ckey, u_id)

                sub_shares, user_dict = load(sub_share_path)
                cloud_shares, user_dict = load(cloud_share_path)
                userkey_dict, namelist = load(UserKey_Path)

                c = Enc(usk, u_id, user_feature, len(user_feature))
                c1,c2 = np.split(c[0],2)
                cp = ReEnc(usk, SubName, c2, len(c2))

                cloud_shares[u_id]=[c1]
                sub_shares[u_id]=[cp]
                userkey_dict[u_id]=usk

                np.save(cloud_share_path, cloud_shares)
                np.save(sub_share_path, sub_shares)
                save_userkey(userkey_dict, UserKey_Path)

                append_new_user(app.config['UPLOAD_FOLDER'], name, filename, u_id)
                return Template('''
                    <!doctype html>
                    <title>Upload new File</title>
                    <h1>Upload Success</h1>
                    <p>Please download and install the PBio app to your android device using this
                    <a href="https://drive.google.com/file/d/1imIaSOJDGjESvmXysfGXLShEUc-UQFVK/view?usp=sharing"> link</a> </p>
                    <p> or scan the QR code to download.</p>
                    <img src="static/PBio_QR.png" />
                    <p>Your user ID: <strong> ${uid} </strong> </p>
                    <p> Please find this
                    <a href="https://www.talkandroid.com/guides/beginner/install-apk-files-on-android/"> link</a> for the guideline to manually install .apk on your device.</p>
                    ''').substitute(uid=u_id)
    return '''
    <!doctype html>
    <title>Upload new Photo</title>
    <h1>Upload new Photo</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file> <br>
      <input type=text name=name placeholder="Please enter your name"> <br>
      <input type=text name=email placeholder="Please enter your email address">
      <input type=submit value=Upload>
    </form>
    <p>Caution: Please <strong>DO NOT</strong> upload using mobile device. </p>
    '''

def extract_feature(img_path, u_id, verbose=False):
    try:
        image = face_recognition.load_image_file(img_path)
        face_bounding_boxes = face_recognition.face_locations(image)

        if len(face_bounding_boxes) != 1:
            # If there are no people (or too many people) in a training image, skip the image.
            if verbose:
                print("Image {} not suitable for training: {}".format(img_path, "Didn't find a face" if len(
                    face_bounding_boxes) < 1 else "Found more than one face"))
                return 0, []
            return 0, []
        else:
            # Add face encoding for current image to the training set
            v = face_recognition.face_encodings(image, known_face_locations=face_bounding_boxes)[0]
            print(v)
            return 1, v
    except:
        return 0,[]


def append_new_user(path, name, filename, u_id):
    dict = {name:{'uid':u_id,'filename':filename}}
    filename = "user_list.txt"
    filedict = pathlib.Path(os.path.join(path,filename))
    if filedict.exists():
        print("File exist")
        w = csv.writer(open(filedict, "a"))
        for n,u in dict.items():
            w.writerow([n,u])
    else:
        print("File not exist")
        w = csv.writer(open(filedict, "w"))
        for n,u in dict.items():
            w.writerow([n,u])


def scale_encode(v, s=12):
    print("==== Scaler encode===")
    t = np.rint((v + 8) * s)
    print(t)
    return np.asarray(t, dtype=np.int32)


def secure_distance_verifier(c, x):
    alpha = x * c
    sum_alpha = np.sum(alpha) + np.sum(np.square(x))
    sum_b2 = np.sum(x)

    return sum_alpha, sum_b2


@socketio.on('connect')
def on_connect(**kwargs):
    print("Client connected %s" % request.sid)


@socketio.on('auth_result')
def on_auth_result(*args):
    print("auth result", args[0])
    socketio.emit("disconnect", args[0])


@socketio.on('disconnect')
def on_disconnect():
    print("Client disconnected %s" % request.sid)


@socketio.on("ping")
def on_ping(a):
    print("Received Ping from client", a)
    socketio.emit("pong", time.time() - a)


@socketio.on('auth_sub')
def auth_sub(data):
    # print('hello !', pickle.loads(data))
    data = pickle.loads(data)
    id = data[0]
    client_share = data[1]

    sub_share_path = "Subscriber/Subscriber_.npy"

    shares, data_namelist = load(sub_share_path)

    try:
        full_shares = shares[id]
        print("encoding.")
        print(full_shares)
        full_shares = scale_encode(full_shares[0])
        print("encoded....")
        sum_alpha, sum_b2 = secure_distance_verifier(client_share, full_shares)
        emit('auth_sub', pickle.dumps(np.array([sum_alpha, sum_b2])))
    except:
        print("Name not found")
        emit('auth_sub', pickle.dumps(np.array(['Error'])))
    pass


@socketio.on('auth_cloud')
def auth_cloud(data):
    # print('hello !', pickle.loads(data))
    data = pickle.loads(data)
    id = data[0]
    client_share = data[1]


    shares, data_namelist = load(cloud_share_path)

    try:
        full_shares = shares[id]
        print(full_shares)
        full_shares = scale_encode(full_shares[0])
        sum_alpha, sum_b2 = secure_distance_verifier(client_share, full_shares)
        emit('auth_cloud', pickle.dumps(np.array([sum_alpha, sum_b2])))
    except:
        print("Name not found")
        emit('auth_cloud', pickle.dumps(np.array(['Error'])))
    pass


@socketio.on_error_default
def error_handler(e):
    print("socket error: %s, %s" % (e, str(request.event)))


def gen_OTP(size=6, random_str=""):
    digits = [i for i in range(0, 10)]
    for i in range(size):
        index = math.floor(random.random() * 10)
        random_str += str(digits[index])
    return random_str


def start_gshade(full_shares):
    print("Running GSHADE")
    lib = ctypes.cdll.LoadLibrary('./dst.so')
    test = lib.t
    test.restype = ctypes.c_int
    test.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ndpointer(ctypes.c_int, flags="C_CONTIGUOUS"),
                     ctypes.c_size_t]
    a = test(7766, 0, ctypes.c_char_p("0.0.0.0".encode()), full_shares, full_shares.size)

    t2 = lib.get_comp_time
    t2.restype = ctypes.c_double
    b = t2()
    print("Comp time:", b)
    return "done"


@app.route("/cloud_auth", methods=['Get', 'POST'])
def cloud_auth():
    data = request.json
    id = data['id']
    cloud_share_path = "Cloud/Cloud_1.npy"

    shares, data_namelist = load(cloud_share_path)
    try:
        full_shares = shares[id]
        print(full_shares)
        full_shares = scale_encode(full_shares[0])
        print("Ready GShade")
        # t = threading.Thread(target=start_gshade, args=(full_shares,))
        t = multiprocessing.Process(target=start_gshade, args=(full_shares,))
        t.start()

        return {'status': '200'}
    except:
        print("Name not found")
        return {'status': '401'}


@app.route("/sub_auth", methods=['Get', 'POST'])
def sub_auth():
    data = request.json
    id = data['id']
    shares, data_namelist = load(sub_share_path)
    try:
        # full_shares = np.append( shares[id], shares[id] )
        full_shares = shares[id]
        print(full_shares)
        full_shares = scale_encode(full_shares[0])
        print("Ready GShade")
        # t = threading.Thread(target=start_gshade, args=(full_shares,))
        t = multiprocessing.Process(target=start_gshade, args=(full_shares,))
        t.start()

        return {'status': '200'}
    except:
        print("Name not found")
        return {'status': '401'}


@app.route("/requestOTP", methods=['GET', 'POST'])
def request_OTP():
    print("Requesting OTP")
    data = request.json
    id = data['id']
    userkey_dict, namelist = load("Original/UserKeys.npy")

    try:
        if (id in namelist):
            print('haha')
            otp = gen_OTP(6)
            print("Generated OTP", otp)
            timestamp = time.time()

            try:
                otp_dict[id] = [timestamp, otp]
                print("Replaced repeated")
            except KeyError:
                print("New OTP requested")
                otp_dict[id] = [timestamp, otp]

            print(otp_dict)
            return {'OTP': otp}
        else:
            return {'error': '401'}
    except Exception as e:
        print("Error ", e)
        return {'error': '404'}


@app.route("/exp_result_collector", methods=['GET', 'POST'])
def exp_result_collector():
    exp_filepath = "Experiment Result/exp_result.npy"
    data = request.json
    print(data)

    id = data["id"]
    date = data["date"]
    auth_result = data["auth_result"]
    enc_time = data["enc_time"]
    extract_time = data["extract_time"]
    ver_time = data["ver_time"]
    sub_ver_time = data["sub_ver_time"]
    cloud_ver_time = data["cloud_ver_time"]
    result = {"date": date, "auth_result": auth_result, "enc_time": enc_time, "extract_time": extract_time, "ver_time": ver_time,
              "sub_ver_time":sub_ver_time, "cloud_ver_time": cloud_ver_time}

    try:
        dict, name = load(exp_filepath)
        if id in dict:
            print("ID exists...., append result")
            dict[id].append(result)
            # for i in dict[id]:
            #     print(i)
        else:
            dict[id] = [result]
            print("Saving new result")
        np.save(exp_filepath, dict)
    except Exception as e:
        print("error,", str(e))
        print("File not found, creating a new one")
        dict = {}
        # dict["temp"] = [
        #     {"date": time.time(), "auth_result": "true", "enc_time": 0.52437, "ver_time": 1.12, "extract_time": 0.7}]
        dict[id] = [result]
        np.save(exp_filepath, dict)
        print("New file saved")

    # print(dict)
    return {'status': '200'}


@app.route("/temp", methods=['GET', 'POST'])
def temp():
    # TODO: create an API that allow user to request a user secret key
    data = request.json
    id = data['id']
    req_otp = data['otp']
    # print(id, req_otp)

    userkey_dict, namelist = load("Original/UserKeys.npy")

    req_time = time.time()

    try:
        otp_time = otp_dict[id][0]
        otp_code = otp_dict[id][1]
        if (req_time - otp_time) > 30:
            return {'error': "otp expired"}
        else:
            if otp_code == req_otp:
                try:
                    print(userkey_dict[id])
                    return {'key': userkey_dict[id]}
                except Exception as e:
                    return {'error': '401'}
            else:
                return {'error': "401"}
    except Exception as e:
        print("id not found")
        return {'error': '404'}


def load(dict_file):
    try:
        temp = np.load(dict_file, allow_pickle=True)
        d_dict = temp.item()
        namelist = list(d_dict.keys())
    except:
        d_dict={}
        namelist=[]
    return d_dict, namelist


def load_key(filename):
    file = open(filename, 'rb')
    # sk = PM.deserialize(file.read())
    sk = file.read().decode()
    file.close()
    return sk

if __name__ == "__main__":
    # app.run(host='0.0.0.0', port=5001, debug=True)
    global otp_dict
    otp_dict = {}
    #socketio.run(app, host='0.0.0.0', port=5001, debug=True, ssl_context=context)
    socketio.run(app, host='0.0.0.0', port=5001, debug=False)
