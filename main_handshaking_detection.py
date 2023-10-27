import cv2
import cvzone
from cvzone.HandTrackingModule import HandDetector
import time

from handshake_detector import HandshakeDetector
# install: cv2, cvzone, mediapipe, protobuf version 3.20.0

cv2.namedWindow("preview")
vc = cv2.VideoCapture(0)
vc.set(3, 640)
vc.set(4, 480)

detector = HandDetector(maxHands=1)
movePlayer = None

handshake_detector = HandshakeDetector()

while True:
    imgBG = cv2.imread('resources/BG.png')  # background

    success, img = vc.read()
    if img is None:
        continue

    # calculate the resize amount for the square in your design
    imgScaled = cv2.resize(img, (0, 0), None, 0.875, 0.875)
    hands, img = detector.findHands(imgScaled, draw=True)

    imgScaled = imgScaled[:, 80:480]  # crop so that it fits to the box
    # put the exact pixels you want to embed the video
    imgBG[234:654, 795:1195] = imgScaled

    if hands:
        print("Found hand")
        hand = hands[0]
        handshake_detector.calculate_movement_score(hand)

        fingers = detector.fingersUp(hand)
        if fingers == [0, 0, 0, 0, 0]:  # if Rock
            movePlayer = 1
        if fingers == [1, 1, 1, 1, 1]:  # if Paper
            movePlayer = 2
        if fingers == [0, 1, 1, 0, 0]:  # if Scissors
            movePlayer = 3
        # todo add else: 'unvalid move!!'
    else:
        print("No hand found")
        print("")
        handshake_detector.calculate_movement_score(None)

    handshake_status = handshake_detector.get_hand_shaking_status()
    print(f"handshake_status: {handshake_status}")

    cv2.imshow('BG', imgBG)

    key = cv2.waitKey(1)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
