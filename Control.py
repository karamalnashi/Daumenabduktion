import json
import paho.mqtt.client as mqttclient
import cv2
import time
import numpy as np
import pyttsx3

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


volBar = 400
volPer = 0
t,t1=100,100
count = 0
dir=0

# ###################    MQTT Connect  ##################################################
broker_address = "localhost"
port = 1883
user = "mqtt"
password = "test"
def convert (data1):
    data = json.loads(data1)
    say = data["content"]["say"]
    print(say)
    text_speech = pyttsx3.init()
    text_speech.say(say)
    text_speech.runAndWait()

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

    convert(message.payload.decode("utf-8"))

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



        volBar = np.interp(length, [50, 110], [400, 150])
        volPer = np.interp(length,[50, 110],[0, 100])
        print(int(length))

        color = (255, 0, 255)
        if volPer == 100:
            color = (0, 255, 0)
            if dir == 0:
                count += 0.5
                dir = 1
        if volPer == 0:
            color = (0, 255, 0)
            if dir == 1:
                count += 0.5
                dir = 0



        if length <40:
            cv2.circle(img, (cx, cy), 15, (0, 255, 0), cv2.FILLED)
            cv2.putText(img, str("Ihres Daumens wieder weit weg"), (20, 50),
                        cv2.FONT_HERSHEY_PLAIN, 2,
                        (255, 0, 0), 2)
            #cv2.imshow("Image", img)
            f = open('data.json')
            data = json.load(f)
            x = data[0]
            y1 = json.dumps(x)
            if t > 99:
                client.publish("ebrain/DialogEngine1/interaction",y1)
                t = 0
            else:
                t = t + 1
                print(t)
                t1=100
        elif length>110 :
            cv2.circle(img, (cx, cy), 15, (0, 255, 0), cv2.FILLED)
            cv2.putText(img, str("Ihres Daumens an Ihre Hand heran"), (20, 50),
                        cv2.FONT_HERSHEY_PLAIN, 2,
                        (255, 0, 0), 2)
            #cv2.imshow("Image", img)
            f = open('data.json')
            data = json.load(f)
            x = data[1]
            y2 = json.dumps(x)
            if t1 > 99:
                client.publish("ebrain/DialogEngine1/interaction", y2)
                t1 = 0
            else:
                t1 = t1 + 1
                print(t1)
                t=100



        cv2.rectangle(img, (50, 150), (85, 400), (255, 0, 0), 3)
        cv2.rectangle(img, (50, int(volBar)), (85, 400), (255, 0, 0), cv2.FILLED)
        cv2.putText(img, f'{int(volPer)} %', (40, 450), cv2.FONT_HERSHEY_COMPLEX,
                    1, (255, 0, 0), 3)
        cv2.putText(img, "count: " + str(int(count)), (150, 450), cv2.FONT_HERSHEY_PLAIN, 2,
                    (255, 0, 0), 2)

        #cTime = time.time()
        #fps = 1 / (cTime - pTime)
        #pTime = cTime
       # cv2.putText(img, f'FPS: {int(fps)}', (40, 50), cv2.FONT_HERSHEY_COMPLEX,
                    #1, (255, 0, 0), 3)

        cv2.imshow("Img", img)
        cv2.waitKey(1)