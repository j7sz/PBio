from flask import Flask, request
from numpy.ctypeslib import ndpointer
import numpy as np
import ctypes
import multiprocessing

# The directory that stored the encrypted partial templates
cloud_share_path_name = 'Cloud/'

# Define flask variable
app = Flask(__name__, template_folder='pages')

# Encoder function to map float number to int
# As GSHADE supports max 255, we should convert the float number to maximum 255
# Note: Please ensure value s in the encode and decode function is same.
# Note: Please ensure value s is the same for cloud and subscriber
def scale_encode(v, s=12):
    t = np.rint((v + 8) * s)
    return np.asarray(t, dtype=np.int32)

# Note: Please ensure you have the shared library "dst.so" and utility folder "/util"
# This function call GSHADE function
# On input the vectors, it runs GSHADE with role server 0 on the assigned IP and port number
def start_gshade(full_shares):
    print("Running GSHADE")
    lib = ctypes.cdll.LoadLibrary('./dst.so')
    test = lib.t
    test.restype = ctypes.c_int
    test.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ndpointer(ctypes.c_int, flags="C_CONTIGUOUS"),
                     ctypes.c_size_t]

    role = 0 # Please do not change the role. Server Role = 0
    port = 7766 # You may change the port number if necessary
    ipaddr = "0.0.0.0".encode()  # Usually this is the default broadcast address
    a = test(port, role, ctypes.c_char_p(ipaddr), full_shares, full_shares.size)

    # The following calls the function to retrieve computation overhead
    t2 = lib.get_comp_time
    t2.restype = ctypes.c_double
    b = t2()
    return "done"

# A function to acknowledge for GSHADE
# On receive request from user, it checks whether user exists and returns a ready flag for GSHADE protocol
# TODO: we should do a time-out timer here. In case, if user unable to proceed GSHADE with cloud, it can stop the process
# TODO: randomly assign a port number for GSHADE function. The existing method doesn't work if two users request at the same time
# Please also ensure the url path is consistent to the one in client
@app.route("/cloud_auth", methods=['Get', 'POST'])
def cloud_auth():
    data = request.json
    id = data['id']
    cloud_share_path = "Cloud/EncryptedPartial_I.npy"

    shares, data_namelist = load(cloud_share_path)
    try:
        full_shares = shares[id]
        full_shares = scale_encode(full_shares[0])
        t = multiprocessing.Process(target=start_gshade, args=(full_shares,))
        t.start()
        return {'status': '200'}
    except:
        return {'status': '401'}

# A function to load user encrypted templates
def load(dict_file):
    try:
        temp = np.load(dict_file, allow_pickle=True)
        d_dict = temp.item()
        namelist = list(d_dict.keys())
    except:
        d_dict={}
        namelist=[]
    return d_dict, namelist

# A main function to start cloud (flask) service
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002, debug=True)
