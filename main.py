import cv2
import cvzone
from cvzone.HandTrackingModule import HandDetector
import time
import random
# install: cv2, cvzone, mediapipe, protobuf version 3.20.0

cv2.namedWindow("preview")
vc = cv2.VideoCapture(0)
vc.set(3,640)
vc.set(4,480)

detector = HandDetector(maxHands=1)

timer = 0
showResult = False
gameStarted = False
scores = [0,0]
possibleMoves = ['Rock', 'Paper', 'Scissors']
# success, img = vc.read()

while True:
    imgBG = cv2.imread('resources/BG.png') # background

    success, img = vc.read()
    #if img is not None:
    imgScaled = cv2.resize(img, (0, 0), None, 0.875, 0.875) #calculate the resize amount for the square in your design
    imgScaled = imgScaled[:, 80:480] #crop so that it fits to the box

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
                    movePlayer = None
                    hand = hands[0]
                    fingers = detector.fingersUp(hand)
                    print(fingers)
                    if fingers == [0,0,0,0,0]: # if Rock
                        movePlayer = 1
                    if fingers == [1,1,1,1,1]: # if Paper
                        movePlayer = 2
                    if fingers == [0,1,1,0,0]: # if Scissors
                        movePlayer = 3
                    #todo add else: 'unvalid move!!'
                    if movePlayer is not None:
                        print(str(possibleMoves[movePlayer-1]))

                    randomNumber = random.randint(1, 3)
                    imgAI = cv2.imread(f'Resources/{randomNumber}.png', cv2.IMREAD_UNCHANGED)
                    imgBG = cvzone.overlayPNG(imgBG, imgAI, (149, 310))

                    # Player Wins
                    if (movePlayer == 1 and randomNumber == 3) or \
                            (movePlayer == 2 and randomNumber == 1) or \
                            (movePlayer == 3 and randomNumber == 2):
                        scores[1] += 1

                    # AI Wins
                    if (movePlayer == 3 and randomNumber == 1) or \
                            (movePlayer == 1 and randomNumber == 2) or \
                            (movePlayer == 2 and randomNumber == 3):
                        scores[0] += 1
                    print(scores)

    #if img is not None:
    imgBG[234:654, 795:1195] = imgScaled #put the exact pixels you want to embed the video

    if showResult:
        imgBG = cvzone.overlayPNG(imgBG, imgAI, (149, 310))

    cv2.putText(imgBG, str(scores[0]), (410, 215), cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 6)
    cv2.putText(imgBG, str(scores[1]), (1112, 215), cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 6)
    #cv2.putText(imgBG, str(possibleMoves[movePlayer+1]), (1112, 200), cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 6)

    #if img is not None:
    #cv2.imshow("image", img)
    cv2.imshow('BG', imgBG)
    #cv2.imshow('imgScaled', imgScaled)

    key = cv2.waitKey(1)
    if key == ord('s'): #start the game when pressed s
        gameStarted = True
        startTime = time.time()
        showResult = False
    # success, img = vc.read()
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
