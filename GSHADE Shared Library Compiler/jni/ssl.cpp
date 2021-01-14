#include <iostream>
#include <iomanip>
#include <sstream>
#include <string>
#include <openssl/sha.h>
#include <jni.h>
#include <string>
using namespace std;

string sha256(const string str)
{
    unsigned char hash[SHA256_DIGEST_LENGTH];
    SHA256_CTX sha256;
    SHA256_Init(&sha256);
    SHA256_Update(&sha256, str.c_str(), str.size());
    SHA256_Final(hash, &sha256);
    stringstream ss;
    for(int i = 0; i < SHA256_DIGEST_LENGTH; i++)
    {
        ss << hex << setw(2) << setfill('0') << (int)hash[i];
    }
    return ss.str();
}

extern "C" JNIEXPORT jstring JNICALL
Java_com_example_ndk_1build_MainActivity_stringFromJNI(JNIEnv* env,jobject /* this */) {

        
    cout << sha256("1234567890_1") << endl;
    cout << sha256("1234567890_2") << endl;
    cout << sha256("1234567890_3") << endl;
    cout << sha256("1234567890_4") << endl;
    std::string hello = "Hello from C++";
    return env->NewStringUTF(hello.c_str());
}
