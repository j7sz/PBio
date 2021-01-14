#include <jni.h>
#include <string>
#include <iostream>
#include <gmpxx.h>
#include <gmp.h>
using namespace std;

extern "C" JNIEXPORT jstring JNICALL
Java_com_example_ndk_1build_MainActivity_stringFromJNI(JNIEnv* env,jobject /* this */) {

        mpz_t a,b,c;
        mpz_inits(a,b,c,NULL);

        mpz_set_str(a, "1234", 10);
        mpz_set_str(b,"-5678", 10); //Decimal base

        mpz_add(c,a,b);

        cout<<"\nThe exact result is:";
        mpz_out_str(stdout, 10, c); //Stream, numerical base, var
        cout<<endl;

        mpz_abs(c, c);
        cout<<"The absolute value result is:";
        mpz_out_str(stdout, 10, c);
        cout<<endl;

        std::string hello = "Hello from C++";
        return env->NewStringUTF(hello.c_str());
}
