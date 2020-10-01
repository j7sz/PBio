from PBio import *
import os
from face_recognition.face_recognition_cli import image_files_in_folder

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
    main(True)
