import hashlib
import hmac
import secrets
import numpy as np
import face_recognition
import time

#Function to save a key as file
def save_key(sk, filename):
    file = open(filename, 'wb')
    file.write(sk.encode())
    file.close()

#Function to load key from a file
def load_key(filename):
    file = open(filename, 'rb')
    sk = file.read().decode()
    file.close()
    return sk

#Function to count the number of bits
def countSetBits(n):
    # base case
    if (n == 0):
        return 0
    else:
        return (n & 1) + countSetBits(n >> 1)

#Function to split an int into array
def split_int(i, n):
    h = []
    while countSetBits(i) != 0:
        h.append(i % 2147483648)
        i = i >> n
    return h

#A function to generate master secret key
#By default, it is 256bits key length
def MKGen(bit=256):
    sec_param = int(bit/8)
    msk = secrets.token_hex(sec_param)
    return msk

#A function to derive user key
#It calls HMAC_SHA256 with input of master secret and user identity
def KeyGen(msk, u_id):
    sk_id = HMAC_SHA256(msk,u_id)
    return sk_id

# A psedorandom key function
# On input userkey and ID, it generates a subscriber key
def PRKey(sk_i, id):
    if isinstance(id, int) == True:
        id = str(id)
    k = SHA256_string(str(sk_i)+id)
    k_id = split_int(k, 32)
    return k_id

# generate random matrix
def rand_matrix(dim=3, rand_seed = 0):
    np.random.seed(rand_seed)
    return np.random.randint(low=0, high=255, size=(dim,dim) )


# A psedorandom matrix function
def rand_orth_matrix(dim=3, rand_seed = 0):
    rand_m = rand_matrix(dim, rand_seed)
    q, _ = np.linalg.qr(rand_m)
    return q

# A psedorandom vector function
def rand_vector(size=3, rand_seed = 0):
    np.random.seed(rand_seed)
    t =  np.random.uniform(low=-1, high=1, size=(1, size))
    return t

# A psedorandom permutation function
def rand_permute(v, rand_seed=0):
    v = np.random.RandomState(seed=rand_seed).permutation(v)
    return v

# Generate random scalar
def rand_w(rand_seed = 0):
    np.random.seed(rand_seed)
    return np.random.uniform(low=1, high=2)

# PBio threshold encryption function
def Enc_t( sk_i, id, t):
    k_id = PRKey(sk_i,id)
    w = rand_w(k_id)
    return t*w

# A function to return scalar product
def Output_w_Enc_t(sk_i,id):
    k_id = PRKey(sk_i,id)
    w = rand_w(k_id)
    return w

# A hmac function
def HMAC_SHA256(sk,msg):
    signature = hmac.new(
        sk.encode(),
        msg=msg.encode(),
        digestmod=hashlib.sha256
    ).hexdigest().upper()
    return signature

# SHA256 function
def SHA256_string(hash_string):
    sha_signature = \
        int(hashlib.sha256(hash_string.encode()).hexdigest(), base=16)
    return sha_signature

# PBio encryption algorithm
def Enc( sk_i, id, x, dim):
    k_id = PRKey(sk_i,id)
    M = rand_orth_matrix(dim, k_id)
    v = rand_vector(dim, k_id)
    w = rand_w(k_id)
    x_p = rand_permute(x, k_id)
    c_id = ((x_p + v).dot(M)).dot(w)
    return c_id

# PBio ReEnc function
def ReEnc(sk_j, id, c, dim):
    k_id = PRKey(sk_j,id)
    M = rand_orth_matrix(dim, k_id)
    v = rand_vector(dim, k_id)
    w = rand_w(k_id)
    cc_id = ((c + v).dot(M)).dot(w)
    return cc_id

