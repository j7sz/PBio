JNI_PATH := $(call my-dir)
GMP_WITH_CPLUSPLUS := yes
include $(JNI_PATH)/gmp/Android.mk
LOCAL_PATH := $(JNI_PATH)
FILE_LIST := $(wildcard $(LOCAL_PATH)/gshade/util/Miracl/mr/*.c)

include $(CLEAR_VARS)
LOCAL_MODULE := crypto_static
LOCAL_SRC_FILES := libs/$(TARGET_ARCH_ABI)/libcrypto.a
include $(PREBUILT_STATIC_LIBRARY)

include $(CLEAR_VARS)
LOCAL_MODULE := ssl_static
LOCAL_SRC_FILES := libs/$(TARGET_ARCH_ABI)/libssl.a
include $(PREBUILT_STATIC_LIBRARY)

include $(CLEAR_VARS)
LOCAL_MODULE := ndktest
LOCAL_SRC_FILES :=  $(LOCAL_PATH)/gshade/mains/distance_framework.cpp $(LOCAL_PATH)/gshade/util/cbitvector.cpp $(LOCAL_PATH)/gshade/ot/brick.cpp $(LOCAL_PATH)/gshade/ot/naor-pinkas.cpp $(LOCAL_PATH)/gshade/util/crypto.cpp $(LOCAL_PATH)/gshade/util/brick.cpp $(LOCAL_PATH)/gshade/util/Miracl/ec2.cpp $(LOCAL_PATH)/gshade/util/Miracl/ecn.cpp $(LOCAL_PATH)/gshade/util/Miracl/poly.cpp $(LOCAL_PATH)/gshade/util/Miracl/polymod.cpp $(LOCAL_PATH)/gshade/util/Miracl/zzn.cpp $(LOCAL_PATH)/gshade/ot/ot-extension.cpp $(LOCAL_PATH)/gshade/util/Miracl/big.cpp $(LOCAL_PATH)/gshade/util/Miracl/mr/$(TARGET_ARCH_ABI)/mrmuldv.c $(FILE_LIST)

LOCAL_LDLIBS += -llog 
LOCAL_LDFLAGS := -llog

LOCAL_C_INCLUDES := $(LOCAL_PATH)/gshade/mains $(LOCAL_PATH)/gshade/ot $(LOCAL_PATH)/gshade/util $(LOCAL_PATH)/gshade/util/Miracl $(LOCAL_PATH)/include/$(TARGET_ARCH_ABI)

LOCAL_STATIC_LIBRARIES := ssl_static crypto_static
LOCAL_SHARED_LIBRARIES := gmp liblog crystax

LOCAL_CPP_FEATURES := exceptions
include $(BUILD_SHARED_LIBRARY)
