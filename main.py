import os,sys
import platform
#import tkinter
from .HCNetSDK import *
import time,codecs
# 登录的设备信息

from io import BytesIO

#global DATA_SIZE 
#DATA_SIZE = 0
def GetPlatform():
    sysstr = platform.system()
    print('' + sysstr)
    if sysstr != "Windows":
        global WINDOWS_FLAG
        WINDOWS_FLAG = False
    else:
        WINDOWS_FLAG = True
    return WINDOWS_FLAG
def SetSDKInitCfg(Objdll):
    # 设置HCNetSDKCom组件库和SSL库加载路径
    # print(os.getcwd())
    if WINDOWS_FLAG:
        strPath = os.getcwd().encode('gbk')
        sdk_ComPath = NET_DVR_LOCAL_SDK_PATH()
        sdk_ComPath.sPath = strPath
        Objdll.NET_DVR_SetSDKInitCfg(2, byref(sdk_ComPath))
        Objdll.NET_DVR_SetSDKInitCfg(3, create_string_buffer(strPath + b'\libcrypto-1_1-x64.dll'))
        Objdll.NET_DVR_SetSDKInitCfg(4, create_string_buffer(strPath + b'\libssl-1_1-x64.dll'))
    else:
        strPath = os.getcwd().encode('utf-8')
        sdk_ComPath = NET_DVR_LOCAL_SDK_PATH()
        sdk_ComPath.sPath = strPath
        Objdll.NET_DVR_SetSDKInitCfg(2, byref(sdk_ComPath))
        Objdll.NET_DVR_SetSDKInitCfg(3, create_string_buffer(strPath + b'/libcrypto.so.1.1'))
        Objdll.NET_DVR_SetSDKInitCfg(4, create_string_buffer(strPath + b'/libssl.so.1.1'))
    return Objdll
def LoginDev(Objdll,IP):
    # 登录注册设备
    #DEV_IP = create_string_buffer(b'192.168.2.18')
    DEV_IP = bytes(IP,"ascii")
    DEV_PORT = 8000
    DEV_USER_NAME = create_string_buffer(b'admin')
    DEV_PASSWORD = create_string_buffer(b'a123456789')
    device_info = NET_DVR_DEVICEINFO_V30()
    lUserId = Objdll.NET_DVR_Login_V30(DEV_IP, DEV_PORT, DEV_USER_NAME, DEV_PASSWORD, byref(device_info))
    return (lUserId, device_info)
def VoiceMRDataCallBack_V30(lPlayHandle, pRecvDataBuffer, dwBufSize, byAudioFlag, pUser):
    #file = open("../../decode_device.pcm","ab+")
    
    outbuf = BytesIO()
    #dec_frame_info = NET_DVR_AUDIODE mC_PROCESS_PARAM()
    if byAudioFlag==1:
        #deinfo = NET_DVR_AUDIODESC_INFO()
        global Decoder
        Decoder = None
        if Decoder is None:
            Objdll.NET_DVR_InitG722Decoder.restype = c_void_p#G722解码器
            Decoder = Objdll.NET_DVR_InitG722Decoder()
        #G722解码信息结构体
        dec_frame_info = NET_DVR_AUDIODEC_PROCESS_PARAM()
        dec_frame_info.in_buf = cast(pRecvDataBuffer, POINTER(c_ubyte)) # type: ignore
        #dec_frame_info.in_buf = cast(bytes(char_arr), POINTER(c_ubyte))
        #dec_frame_info.in_buf = pRecvDataBuffer
        #dec_frame_info.dec_info = deinfo
        dec_frame_info.in_data_size = dwBufSize 
        #dec_frame_info.in_data_size = 80
        dec_frame_info.out_buf = cast(create_string_buffer(1280), POINTER(c_ubyte))
        Objdll.NET_DVR_DecodeG722Frame.argtypes = (c_void_p, POINTER(NET_DVR_AUDIODEC_PROCESS_PARAM))
        #Objdll.NET_DVR_DecodeG722Frame.argtypes = (c_int, POINTER(NET_DVR_AUDIODEC_PROCESS_PARAM))
        ret = Objdll.NET_DVR_DecodeG722Frame(Decoder,byref(dec_frame_info))
        out_buf = dec_frame_info.out_buf
       # print("zz",ret,type(dec_frame_info.in_buf),type(dec_frame_info.out_buf),bytes(dec_frame_info.out_buf))
        if ret==1:
            
            #print("dec_info:",dec_frame_info.dec_info.nchans,Objdll.NET_DVR_GetLastError())
            CharArr = c_char * 1280
            char_arr = CharArr(*out_buf[:1280])
            # file.write(char_arr.raw)
            outbuf.write(char_arr.raw)
            #print("raw",char_arr.raw)
            time.sleep(0.01)
    # else:
    #     file.close()
        
    if Decoder is not None:
        Objdll.NET_DVR_ReleaseG722Encoder.argtypes = [c_void_p]
        Objdll.NET_DVR_ReleaseG722Encoder(Decoder)
        Decoder = None
    
def RealVioeDataCallBack_V30(lPlayHandle, pRecvDataBuffer, dwBufSize, byAudioFlag, pUser):
    
    
    pass
    
# if __name__ == '__main__':
def run(voicedata,camera_ip):
    btmp_buf = BytesIO()
    btmp_buf.write(voicedata)
    GetPlatform()
    print("winflag:",WINDOWS_FLAG)
    # pwd = os.path.abspath()
    PWD_DIR = os.path.dirname(os.path.abspath(__file__))
    global Objdll
#Objdll = None
    global outbuf
    outbuf = None
    if WINDOWS_FLAG:
        sdk_dir = os.path.join(PWD_DIR,"lib","win")
        # os.chdir(r'./lib/win')
        os.chdir(sdk_dir)
        Objdll = ctypes.WinDLL('./HCNetSDK.dll')  # 加载网络库
        
        # Objdll = ctypes.WinDLL(os.path.join(sdk_dir,"HCNetSDK.dll"))
    else:
        sdk_dir = os.path.join(PWD_DIR,"lib","linux")
        os.chdir(sdk_dir)
        # os.chdir(r'./lib/linux')
        
        Objdll = cdll.LoadLibrary(r'./libhcnetsdk.so')
    Objdll=SetSDKInitCfg(Objdll)  # 设置组件库和SSL库加载路径
    Objdll.NET_DVR_SetLogToFile(3, bytes('./SdkLog_Python/', encoding="utf-8"), False)
    # 初始化DLL
    Objdll.NET_DVR_Init()
    (lUserId, device_info) = LoginDev(Objdll,camera_ip)#登录
    if lUserId < 0:
        err = Objdll.NET_DVR_GetLastError()
        print('Login device fail, error code is: %d' % Objdll.NET_DVR_GetLastError())
        # 释放资源
        Objdll.NET_DVR_Cleanup()
        # exit()
    """
    #实时语音通话
    funcRealVoiceDataCallBack_V30 = REALVOICEDATACALLBACK(RealVioeDataCallBack_V30)
    voice_tag=Objdll.NET_DVR_StartVoiceCom_V30(lUserId,1,funcRealVoiceDataCallBack_V30,None)
    time.sleep(10)
    Objdll.NET_DVR_StopVoiceCom(lUserId)    
    """
    audio_info = NET_DVR_COMPRESSION_AUDIO()#音频编码结构体
    Objdll.NET_DVR_GetCurrentAudioCompress.restype = c_void_p
    audio_handle=Objdll.NET_DVR_GetCurrentAudioCompress(lUserId,byref(audio_info))#获取音频信息
    if audio_handle<0:
        print("获取设备音频编码信息失败")
        print("errors code:",Objdll.NET_DVR_GetLastError())
        Objdll.NET_DVR_Cleanup()
        sys.exit()
    print("device audio encode is:",audio_info.byAudioEncType,audio_info.byAudioSamplingRate,audio_info.byAudioBitRate)#0-G722,1-G711_U,2-G711_A
    funVoiceMRDataCallBack_V30=MRVOICEDATACALLBACK(VoiceMRDataCallBack_V30)
    Objdll.NET_DVR_StartVoiceCom_MR_V30.restype = c_void_p
    voice_handle = 0
    voice_handle=Objdll.NET_DVR_StartVoiceCom_MR_V30(lUserId,1,funVoiceMRDataCallBack_V30,None)
    Encoder = None
    # global Decoder
    # Decoder = None
    # print("语音转发启动失败")
 
    if voice_handle==-1:
        print("语音转发启动失败")
        print("errors code:",Objdll.NET_DVR_GetLastError())
        Objdll.NET_DVR_Cleanup()
        # sys.exit()
    else:
        #file = open('../../AudioFile/send2device.pcm','rb')
       # file = open('../../AudioFile/test.pcm','rb')
        audio_enc_info = NET_DVR_AUDIOENC_INFO()# G722编码机构体
        
        #input_buf = create_string_buffer(80)
        #input_buf = c_ubyte*1280
       # out_buf = create_string_buffer(1280)
        #out_buf = c_ubyte*80  
        Objdll.NET_DVR_InitG722Encoder.restype = c_void_p
        Encoder = Objdll.NET_DVR_InitG722Encoder(byref(audio_enc_info))
        #Encoder = Objdll.NET_DVR_InitG722Encoder()
        btmp_buf.seek(0) #将buffer的游标至为开头
        while True:
            #block = file.read(1280)
           
            block = btmp_buf.read(1280)
            print(len(block))
            if len(block)<1:
                break
            else:
                enc_frame_info = NET_DVR_AUDIOENC_PROCESS_PARAM()#G722编码信息结构体
                enc_frame_info.in_buf = cast(block, POINTER(c_ubyte)) # type: ignore
                enc_frame_info.out_buf = cast(create_string_buffer(80), POINTER(c_ubyte))
                # enc_frame_info.g726enc_reset = 1
                # enc_frame_info.out_frame_size = 320
                # enc_frame_info.g711_type = 1
                # enc_frame_info.enc_mode = 1
                # enc_frame_info.reserved = 0
                
                # input_buf.value = block
                Objdll.NET_DVR_EncodeG722Frame.argtypes = (c_void_p, POINTER(NET_DVR_AUDIOENC_PROCESS_PARAM))
                Objdll.NET_DVR_EncodeG722Frame(Encoder,byref(enc_frame_info))
                #Objdll.NET_DVR_EncodeG722Frame(Encoder,input_buf,out_buf)
                time.sleep(0.01)
                if enc_frame_info.out_buf:
                   # print("encode out_buf:",bytes(enc_frame_info.out_buf))
                    #print("encode in_puf:",bytes(enc_frame_info.in_buf))
                    Objdll.NET_DVR_VoiceComSendData(voice_handle,enc_frame_info.out_buf,80)
                    # print("发送成功",Objdll.NET_DVR_GetLastError())
        # file.close()
        if Encoder is not None:
            Objdll.NET_DVR_ReleaseG722Encoder.argtypes = [c_void_p]
            Objdll.NET_DVR_ReleaseG722Encoder(Encoder)
        time.sleep(5)
        # return voice_handle
        Objdll.NET_DVR_StopVoiceCom.argtypes = [c_void_p]
        m_stopVoiceHandle = Objdll.NET_DVR_StopVoiceCom(voice_handle)
        #if m_stopVoiceHandle is False:
        if m_stopVoiceHandle <0:
            print("停止语音转发失败，错误码为%s" % Objdll.NET_DVR_GetLastError())
            Objdll.NET_DVR_Logout(lUserId)
            Objdll.NET_DVR_Cleanup()
        else:
            Objdll.NET_DVR_Logout(lUserId)
            Objdll.NET_DVR_Cleanup()
            print("程序退出成功")
        print(outbuf)
