from PBio import *
import os
from face_recognition.face_recognition_cli import image_files_in_folder
from flask import Flask,flash, jsonify, request, redirect, render_template, url_for, Response, send_from_directory
import random, pathlib, csv, math
from string import Template
from werkzeug.utils import secure_filename

# Declare some default path to store data
# Image_path is a directory that contains of user face images. Please note that their folder name indicate their user ID respectively
image_path = "images/"


# A path named as DataOwner
# It creates userkey file and extracted vectors dataset
dataowner_path_name = 'DataOwner/'
UserKey_Path = 'DataOwner/UserKeys.npy'
extracted_data = 'DataOwner/Extracted_data.npy'

# A path named Cloud
# It creates two encrypted partial datasets
cloud_share_path_name = 'Cloud/'

# A path named Subscriber
# It create subscriber template dataset
subscriber_share_path_name = 'Subscriber/'


# Configuration of Flask server
# The allowed extensions enable users to upload for only the listed format
# UPLOAD_FOLDER is the submitted image directory
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif','PNG','JPG','JPEG'}
UPLOAD_FOLDER = 'user_img'
app = Flask(__name__, template_folder='pages')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# A function to check the allowed file format
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# A flask route to store the submitted images
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

# A default flask route to show the index page
# A page to enable users to enroll their face images
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
        # A random function to generate random ID
        u_id = random.choice("SG")+gen_OTP(7)+random.choice("ABCDEFGHIJK")
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            # The following codes store the submitted image
            # It then extract the feature vectors
            filename = secure_filename(file.filename)
            path = os.path.join( app.config['UPLOAD_FOLDER'], u_id)
            os.mkdir(path)
            img_path = os.path.join(path, email+'_'+name+'_'+filename)
            file.save(img_path)
            status, user_feature = extract_feature(img_path, u_id)
            # If the image doesn't pass the extract_feature function, returns an error page to ask users to try again
            if status == 0:
                return '''
                   <!doctype html>
                    <title>Upload new File</title>
                    <h1>Upload Failure</h1>
                    <p>Unable to detect facial landmark.<br>Please ensure to upload a passport photo or a front-facing selfie.</p>
               '''
            # Otherwise, it loads the master secret key
            # Generate the encrypted templates for cloud and subscribers
            # In our case, we assume there is only a subscriber, namely X-Bank
            else:
                msk = load_key(dataowner_path_name + "masterkey.txt")
                SubName = "X-Bank"
                usk = KeyGen(msk, u_id)

                sub_share_path = "Subscriber/SubscriberTemplate.npy"
                cloud_share_path = "Cloud/EncryptedPartial_I.npy"
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
                save_userkey(UserKey_Path, userkey_dict)

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


# A flask route to enable user from requesting OTP
# This OTP is used for 2FA during key distribution
# A global variable, otp_dict, is required for verification purpose
# A timestamp is included for expiration purpose
@app.route("/requestOTP", methods=['GET', 'POST'])
def request_OTP():
    data = request.json
    id = data['id']
    userkey_dict, namelist = load("DataOwner/UserKeys.npy")

    try:
        if (id in namelist):
            otp = gen_OTP(6)
            timestamp = time.time()
            try:
                otp_dict[id] = [timestamp, otp]
            except KeyError:
                otp_dict[id] = [timestamp, otp]

            return {'OTP': otp}
        else:
            return {'error': '401'}
    except Exception as e:
        return {'error': '404'}

# A flask route for experiment results collection
# It saves the collected results following the user ID
@app.route("/exp_result_collector", methods=['GET', 'POST'])
def exp_result_collector():
    exp_filepath = "Experiment Result/exp_result.npy"
    data = request.json

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
            dict[id].append(result)
        else:
            dict[id] = [result]
        np.save(exp_filepath, dict)
    except Exception as e:
        dict = {}
        dict[id] = [result]
        np.save(exp_filepath, dict)
    return {'status': '200'}


# A flask route to allow user for requesting his user key
# Please note that an OTP is required for 2FA
@app.route("/keyrequest", methods=['GET', 'POST'])
def keyrequest():
    data = request.json
    id = data['id']
    req_otp = data['otp']
    userkey_dict, namelist = load("DataOwner/UserKeys.npy")
    req_time = time.time()
    try:
        otp_time = otp_dict[id][0]
        otp_code = otp_dict[id][1]
        if (req_time - otp_time) > 30:
            return {'error': "otp expired"}
        else:
            if otp_code == req_otp:
                try:
                    return {'key': userkey_dict[id]}
                except Exception as e:
                    return {'error': '401'}
            else:
                return {'error': "401"}
    except Exception as e:
        return {'error': '404'}

# A function to extract feature vectors from the submitted face image
# Note that it returns 2 parameters, status 1 or 0 and feature vectors
# Status 1 or 0 indicate the success or failure of the extraction
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
            return 1, v
    except:
        return 0,[]

# A function to append new users to a list
# The list contains the enrollment information, e.g. user name, email, and etc
def append_new_user(path, name, filename, u_id):
    dict = {name:{'uid':u_id,'filename':filename}}
    filename = "user_list.txt"
    filedict = pathlib.Path(os.path.join(path,filename))
    if filedict.exists():
        w = csv.writer(open(filedict, "a"))
        for n,u in dict.items():
            w.writerow([n,u])
    else:
        w = csv.writer(open(filedict, "w"))
        for n,u in dict.items():
            w.writerow([n,u])

# A function to generate OTP
def gen_OTP(size=6, random_str=""):
    digits = [i for i in range(0, 10)]
    for i in range(size):
        index = math.floor(random.random() * 10)
        random_str += str(digits[index])
    return random_str

def main(setup=True):
    # Check if setup flag is set to True.
    # Otherwise, it load master secret key
    if setup == True:
        # Empty all folders
        empty_folder("Subscriber")
        empty_folder("Cloud")
        empty_folder("DataOwner")

        # Create a master secret key.
        msk = MKGen()
        # Save master secret key
        save_key(msk, dataowner_path_name+"masterkey.txt")
    else:
        # Load master secret key
        msk = load_key(dataowner_path_name+"masterkey.txt")

    # Assume there is a subscriber, namely X-Bank
    SubName = "X-Bank"

    # Call extract function to extract user images to feature vectors
    # Extracted feature vectors are saved in path extracted_data
    print("=====Extracting Training Set====")
    extract(image_path, extracted_data)

    # A function to load the extracted_data
    # Feature vectors are stored in dict
    # A list of username as namelist
    print("=====Load Full=====")
    Dict, namelist = load(extracted_data)

    # Call the encrypt then split function
    # On input master secret key, both path name, and dict of feature vectors
    # It generates both partial encrypted templates and a list of user key
    print("========Encrypt_then_Split and Save=======")
    C1,C2, UserKey_Dict = enc_then_split(msk, cloud_share_path_name+"EncryptedPartial_I",cloud_share_path_name+"EncryptedPartial_II" , Dict)

    # Save user secret key
    save_userkey(UserKey_Path, UserKey_Dict)

    # Call ReEnc function to generate subscriber template
    # User key and SubName are used for HMAC to generate subscriber key
    print("=====ReEncrypt and Save =======")
    Cp2 = Full_ReEnc(UserKey_Dict, subscriber_share_path_name+"SubscriberTemplate", SubName, C2)

# A function to save user key
# On input path to save and dict of user key
def save_userkey(UserKey_Path, UserKey_Dict):
    print("======= Saving user keys=======")
    np.save(UserKey_Path, UserKey_Dict)


# A function to extract a directory of face images
# It then save the extracted feature vectors into a file
def extract(images_dir, dict_file ,verbose=False):
    temp = {}

    # Loop through each person in the images directory
    for class_dir in os.listdir(images_dir):
        if not os.path.isdir(os.path.join(images_dir, class_dir)):
            continue

        # Loop through each training image for the current person
        # Note that the name of folder is the user identity
        for img_path in image_files_in_folder(os.path.join(images_dir, class_dir)):
            image = face_recognition.load_image_file(img_path)
            face_bounding_boxes = face_recognition.face_locations(image)

            if len(face_bounding_boxes) != 1:
                # If there are no people (or too many people) in a training image, skip the image.
                if verbose:
                    print("Image {} not suitable for training: {}".format(img_path, "Didn't find a face" if len(face_bounding_boxes) < 1 else "Found more than one face"))
            else:
                # Add face encoding for current image to the training set
                # It is also known as feature vectors v
                v = face_recognition.face_encodings(image, known_face_locations=face_bounding_boxes)[0]
                try:
                    temp[class_dir].append(v)
                except KeyError:
                    temp[class_dir] = [v]

    # Save all the extracted feature vectors into a file
    np.save(dict_file, temp)

# A function to load a dict of vectors
# It returns a dict of vectors and its corresponding list of users
def load(dict_file):
    temp = np.load(dict_file, allow_pickle=True)
    d_dict = temp.item()
    namelist = list(d_dict.keys())
    return d_dict, namelist

# A function to encrypt then split a set of templates
# On input master secret key, 2 paths to be saved, and a dict of feature vectors (templates)
# It generates user key for every user identity, then it encrypt_then_split the feature vectors into encrypted partial template I and II
def enc_then_split(msk, encsplit_part1_filename, encsplit_part2_filename, Dict):
    Enc_DictA = {}
    Enc_DictB = {}
    UserKey_Dict = {}
    for i in Dict:
        user_key = KeyGen(msk,i)

        for j in Dict[i]:
            v = Enc( user_key, i, j, len(j))
            v1, v2 = np.split(v[0], 2)
            try:
                Enc_DictA[i].append(v1)
                Enc_DictB[i].append(v2)
                UserKey_Dict[i].append(user_key)
            except KeyError:
                Enc_DictA[i] = [v1]
                Enc_DictB[i] = [v2]
                UserKey_Dict[i] = user_key
    np.save(encsplit_part1_filename, Enc_DictA)
    np.save(encsplit_part2_filename, Enc_DictB)
    return Enc_DictA, Enc_DictB, UserKey_Dict

# A function to reencrypt the encrypted partial templates
# On input list of userkey, path to store, subscriber identity, and the encrypted partial templates
# It call ReEnc function to generate subscriber template
def Full_ReEnc(UserKey_Dict, enc_file_path, SubName, Dict):
    Enc_Dict = {}
    for i in Dict:
        sk = UserKey_Dict[i]
        for j in Dict[i]:
            v = ReEnc( sk, SubName, j, len(j))
            try:
                Enc_Dict[i].append(v)
            except KeyError:
                Enc_Dict[i] = [v]
    np.save(enc_file_path, Enc_Dict)

# A function to empty/create a folder
def empty_folder(path):
    try:
        for file in os.listdir(path):
            f = os.path.join(path, file)
            try:
                if os.path.isfile(f):
                    os.unlink(f)
            except Exception as e:
                print(e)
    except:
        os.mkdir(path)

if __name__ == '__main__':
    # main(True)
    global otp_dict
    otp_dict = {}
    app.run(host='0.0.0.0', port=5001, debug=True)
