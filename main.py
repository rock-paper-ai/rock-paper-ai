import cv2
import cvzone
from cvzone.HandTrackingModule import HandDetector
import time
# install: cv2, cvzone, mediapipe, protobuf version 3.20.0

cv2.namedWindow("preview")
vc = cv2.VideoCapture(0)
vc.set(3,640)
vc.set(4,480)

detector = HandDetector(maxHands=1)

timer = 0
showResult = False
gameStarted = False
movePlayer = None
# success, img = vc.read()

while True:
    imgBG = cv2.imread('resources/BG.png') # background

    success, img = vc.read()
    if img is not None:
        imgScaled = cv2.resize(img, (0, 0), None, 0.875, 0.875) #calculate the resize amount for the square in your design
        imgScaled = imgScaled[:, 80:480] #crop so that it fits to the box
        imgBG[234:654, 795:1195] = imgScaled #put the exact pixels you want to embed the video

    # find hands
    hands, img = detector.findHands(imgScaled)
    if gameStarted:
        if showResult is False:
            timer = time.time() - startTime
            cv2.putText(imgBG, str(int(timer)), (605, 435), cv2.FONT_HERSHEY_PLAIN, 6, (255, 0, 255), 4)

            if timer > 3:
                showResult=True
                timer = 0
                if hands:
                    hand = hands[0]
                    fingers = detector.fingersUp(hand)
                    if fingers == [0,0,0,0,0]: # if Rock
                        movePlayer = 1
                    if fingers == [1,1,1,1,1]: # if Paper
                        movePlayer = 2
                    if fingers == [0,1,1,0,0]: # if Scissors
                        movePlayer = 3
                    #todo add else: 'unvalid move!!'
                    if movePlayer is not None:
                        print(movePlayer)

    #if img is not None:
    #cv2.imshow("image", img)
    cv2.imshow('BG', imgBG)
    #cv2.imshow('imgScaled', imgScaled)

    key = cv2.waitKey(1)
    if key == ord('s'): #start the game when pressed s
        gameStarted = True
        startTime = time.time()
    # success, img = vc.read()
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
