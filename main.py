from enum import Enum
import cv2
import cvzone
from cvzone.HandTrackingModule import HandDetector
import time
import random

from handshake_detector import HandshakeDetector, HandshakeStatus
# install: cv2, cvzone, mediapipe, protobuf version 3.20.0

possibleMoves = ['Rock', 'Paper', 'Scissors']

def get_player_move(hands, hand_detector):
    player_move = None
    hand = hands[0]
    fingers = hand_detector.fingersUp(hand)
    print(f"player fingers: {fingers}")

    # todo find better
    if fingers == [0, 0, 0, 0, 0] or fingers == [1, 0, 0, 0, 0] or fingers == [0, 0, 0, 0, 1]:  # if Rock
        player_move = 1
    elif fingers == [1, 1, 1, 1, 1]:  # if Paper
        player_move = 2
    elif fingers == [0, 1, 1, 0, 0] or fingers == [0, 1, 1, 1, 1]:  # if Scissors
        player_move = 3
    else:
        player_move = -1 # Unrecognized

    if player_move is not None:
        print(f"player move: {possibleMoves[player_move-1]}")

    return player_move


def do_ai_move(player_move):
    ai_move = random.randint(1, 3)
    print(f"AI move: {ai_move}")
    return ai_move


def update_move_ui(playboard, player_move, ai_move):
    if player_move == -1:
        # todo fix the icon and show error message

        ai_move_image = cv2.imread(f'resources/error.png', cv2.IMREAD_UNCHANGED)
        print('Could not recognise your move!')

    if ai_move is not None:
        ai_move_image = cv2.imread(f'resources/{ai_move}.png', cv2.IMREAD_UNCHANGED)
        playboard = cvzone.overlayPNG(playboard, ai_move_image, (149, 310))
    return playboard


def update_scores(player_move, ai_move, scores):
    # Player Wins
    if (player_move == 1 and ai_move == 3) or \
            (player_move == 2 and ai_move == 1) or \
            (player_move == 3 and ai_move == 2):
        scores[1] += 1

    # AI Wins
    if (player_move == 3 and ai_move == 1) or \
            (player_move == 1 and ai_move == 2) or \
            (player_move == 2 and ai_move == 3):
        scores[0] += 1
    # print(scores)
    return scores

def update_score_ui(playboard, scores):

    #if showResult:
     #       imgBG = cvzone.overlayPNG(imgBG, imgAI, (149, 310))

    cv2.putText(playboard, str(scores[0]), (410, 215),
                cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 6)
    cv2.putText(playboard, str(scores[1]), (1112, 215),
                cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 6)
    return playboard

def update_game_status_text(playboard, game_status):
    if game_status == GameStatus.RUNNING_WAITING_FOR_SHAKE_BEGIN:
        cv2.putText(playboard, "Shake your hand to start", (410, 215),
                    cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 6)
    elif game_status == GameStatus.RUNNING_SHAKING:
        cv2.putText(playboard, "...", (410, 215),
                    cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 6)
    elif game_status == GameStatus.RUNNING_SHOWING_RESULT:
        cv2.putText(playboard, "Press any key to continue", (410, 215),
                    cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 6)
    elif game_status == GameStatus.RUNNING_SHAKE_DONE_INVALID_PLAYER_MOVE:
        cv2.putText(playboard, "Did not recognize your move. Press any key to continue", (410, 215),
                    cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 6)
    elif game_status == GameStatus.NOT_RUNNING:
        cv2.putText(playboard, "Press any key to start", (410, 215),
                    cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 6)
    return playboard

class GameStatus(Enum):
    NOT_RUNNING = 1
    RUNNING_WAITING_FOR_SHAKE_BEGIN = 2
    RUNNING_SHAKING = 3
    RUNNING_SHOWING_RESULT = 4
    RUNNING_SHAKE_DONE_INVALID_PLAYER_MOVE = 5

def main():
    cv2.namedWindow("preview")
    vc = cv2.VideoCapture(0)
    vc.set(3, 640)
    vc.set(4, 480)

    game_status = GameStatus.NOT_RUNNING
    scores = [0, 0]

    hand_detector = HandDetector(maxHands=1)
    handshake_detector = HandshakeDetector()

    player_move = None
    ai_move = None

    while True:
        playboard = cv2.imread('resources/BG.png')  # background

        success, img = vc.read()
        # if img is not None:
        # calculate the resize amount for the square in your design
        imgScaled = cv2.resize(img, (0, 0), None, 0.875, 0.875)
        imgScaled = imgScaled[:, 80:480]  # crop so that it fits to the box

        # find hands
        hands, img = hand_detector.findHands(imgScaled)
        if game_status != GameStatus.NOT_RUNNING:
            if hands:
                handshake_detector.calculate_movement_score(hands[0])

                handshake_status = handshake_detector.get_hand_shaking_status()
                print(f"handshake_status: {handshake_status}")

                if game_status == GameStatus.RUNNING_SHAKING and handshake_status == HandshakeStatus.STEADY:
                    # Player finished shaking
                    
                    player_move = get_player_move(hands, hand_detector)
                    if player_move == -1:
                        game_status = GameStatus.RUNNING_SHAKE_DONE_INVALID_PLAYER_MOVE
                    else:
                        game_status = GameStatus.RUNNING_SHOWING_RESULT
                        ai_move = do_ai_move(player_move)
                        scores = update_scores(player_move, ai_move, scores)

                elif (game_status == GameStatus.RUNNING_WAITING_FOR_SHAKE_BEGIN and handshake_status == HandshakeStatus.SHAKING):
                    game_status = GameStatus.RUNNING_SHAKING

                elif game_status == GameStatus.RUNNING_SHOWING_RESULT or \
                    game_status == GameStatus.RUNNING_SHAKE_DONE_INVALID_PLAYER_MOVE:
                    cv2.waitKey(0) # Wait for any key to be pressed, freeze the output window
                    game_status = GameStatus.RUNNING_WAITING_FOR_SHAKE_BEGIN
                    ai_move = None
                    player_move = None
                    
            else:
                handshake_detector.calculate_movement_score(None)

            print(f"game_status: {game_status}")

            # Update UI
            playboard = update_move_ui(playboard, player_move, ai_move)
            playboard = update_score_ui(playboard, scores)
        playboard = update_game_status_text(playboard, game_status)

        # if img is not None:
        # put the exact pixels you want to embed the video
        playboard[234:654, 795:1195] = imgScaled

        playboard = update_score_ui(playboard, scores)
        # cv2.putText(imgBG, str(possibleMoves[player_move+1]), (1112, 200), cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 6)

        # if img is not None:
        # cv2.imshow("image", img)
        cv2.imshow('BG', playboard)
        # cv2.imshow('imgScaled', imgScaled)

        if game_status == GameStatus.NOT_RUNNING:
            cv2.waitKey(0) # Wait for any key to be pressed, freeze the output window
            game_status = GameStatus.RUNNING_WAITING_FOR_SHAKE_BEGIN

        # success, img = vc.read()
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


if __name__ == "__main__":
    main()
