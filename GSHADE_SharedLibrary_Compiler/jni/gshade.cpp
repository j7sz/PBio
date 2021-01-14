#include <iostream>
#include <jni.h>
#include <distance_framework.h>
#include <string>
#include <android/log.h>
#include <syslog.h>
using namespace std;

extern "C" JNIEXPORT jstring JNICALL
Java_com_example_ndk_1build_MainActivity_role0(JNIEnv* env,jobject /* this */) {
	
    syslog(LOG_CRIT, "hello syslog");
    std::string hello = "Role 0 finish";
    return env->NewStringUTF(hello.c_str());
}

extern "C" JNIEXPORT jstring JNICALL
Java_com_example_ndk_1build_MainActivity_role1(JNIEnv* env,jobject /* this */) {

    test(1);
    std::string hello = "Role 1 finish";
    return env->NewStringUTF(hello.c_str());
}
