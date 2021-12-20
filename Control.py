import json

import paho.mqtt.client as mqttclient
import cv2
import time
import numpy as np
import Pose_Module as htm
import math
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

################################
wCam, hCam = 640, 480
################################

cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)
pTime = 0
detector = htm.handDetector(detectionCon=0.7)

devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(
    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
# volume.GetMute()
# volume.GetMasterVolumeLevel()
volRange = volume.GetVolumeRange()
minVol = volRange [0]
maxVol = volRange [1]
vol = 0
volBar = 400
volPer = 0
t,t1=41,41

# ###################    MQTT Connect  ##################################################
broker_address = "localhost"
port = 1883
user = "mqtt"
password = "test"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("client is connected")
        global connected
        connected = True
    else:
        print("client is error")

def on_message(client, userdata, message):
    print("message recieved = " + str(message.payload.decode("utf-8")))
    print("message topic=", message.topic)

Messagerecieved = False
connected = False
client = mqttclient.Client("MQTT")
client.on_message = on_message
client.username_pw_set(user, password=password)
client.on_connect = on_connect
client.connect(broker_address, port=port)

client.loop_start()
client.subscribe("ebrain/#")

#############################################################################
while True:
    success, img = cap.read()
    img = detector.findHands(img)
    lmList = detector.findPosition(img, draw=False)
    if len(lmList) != 0:
        # print(lmList&#91;4], lmList&#91;8])

        x1, y1 = lmList[4][1], lmList[4][2]
        x2, y2 = lmList[6][1], lmList[6][2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        cv2.circle(img, (x1, y1), 7, (255, 0, 255), cv2.FILLED)
        cv2.circle(img, (x2, y2), 7, (255, 0, 255), cv2.FILLED)
        cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
        cv2.circle(img, (cx, cy), 7, (255, 0, 255), cv2.FILLED)

        length = math.hypot(x2 - x1, y2 - y1)
        print(length)

        # Hand range 50 - 100
        # Volume Range -65 - 0

        vol = np.interp(length, [50, 110], [minVol, maxVol])
        volBar = np.interp(length, [50, 110], [400, 150])
        volPer = np.interp(length,[50, 110],[0, 100])
        print(int(length), vol)
        volume.SetMasterVolumeLevel(vol, None)

        if length <40:
            cv2.circle(img, (cx, cy), 15, (0, 255, 0), cv2.FILLED)
            cv2.putText(img, str("Ihres Daumens an Ihre Hand heran"), (20, 50),
                        cv2.FONT_HERSHEY_PLAIN, 2,
                        (255, 0, 0), 2)
            #cv2.imshow("Image", img)
            f = open('data.json')
            data = json.load(f)
            x = data[0]
            y1 = json.dumps(x)
            if t > 42:
                client.publish("ebrain/DialogEngine1/interaction", y1)
                t = 0
            else:
                t = t + 1
                print(t)
                t1=41
        elif length>80 :
            cv2.circle(img, (cx, cy), 15, (0, 255, 0), cv2.FILLED)
            cv2.putText(img, str("Ihres Daumens wieder weit weg."), (20, 50),
                        cv2.FONT_HERSHEY_PLAIN, 2,
                        (255, 0, 0), 2)
            #cv2.imshow("Image", img)
            f = open('data.json')
            data = json.load(f)
            x = data[1]
            y2 = json.dumps(x)
            if t1 > 40:
                client.publish("ebrain/DialogEngine1/interaction", y2)
                t1 = 0
            else:
                t1 = t1 + 1
                print(t1)
                t=41



        cv2.rectangle(img, (50, 150), (85, 400), (255, 0, 0), 3)
        cv2.rectangle(img, (50, int(volBar)), (85, 400), (255, 0, 0), cv2.FILLED)
        cv2.putText(img, f'{int(volPer)} %', (40, 450), cv2.FONT_HERSHEY_COMPLEX,
                    1, (255, 0, 0), 3)

        #cTime = time.time()
        #fps = 1 / (cTime - pTime)
        #pTime = cTime
       # cv2.putText(img, f'FPS: {int(fps)}', (40, 50), cv2.FONT_HERSHEY_COMPLEX,
                    #1, (255, 0, 0), 3)

        cv2.imshow("Img", img)
        cv2.waitKey(1)