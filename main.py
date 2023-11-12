from enum import Enum
import cv2
import cvzone
from cvzone.HandTrackingModule import HandDetector
import random

import numpy
from handshake_detector import HandshakeDetector, HandshakeStatus


class AiAlgorithmStrategy(Enum):
    RANDOM = 1
    SOMETIMES_CHEAT = 2
    MARKOV_CHAIN = 3


AI_ALGORITHM_STRATEGY = AiAlgorithmStrategy.RANDOM


class Move(Enum):
    ROCK = 0
    PAPER = 1
    SCISSORS = 2


def get_player_move(hands, hand_detector) -> Move:
    player_move = None
    hand = hands[0]
    fingers = hand_detector.fingersUp(hand)
    print(f"player fingers: {fingers}")

    # todo find better
    if fingers == [0, 0, 0, 0, 0] or fingers == [1, 0, 0, 0, 0] or fingers == [0, 0, 0, 0, 1]:
        player_move = Move.ROCK
    elif fingers == [1, 1, 1, 1, 1]:
        player_move = Move.PAPER
    elif fingers == [0, 1, 1, 0, 0] or fingers == [0, 1, 1, 1, 1] or fingers == [1, 1, 1, 0, 0]:
        player_move = Move.SCISSORS

    print(f"player move: {player_move}")

    return player_move


def do_ai_move(player_move) -> Move:
    if AI_ALGORITHM_STRATEGY == AiAlgorithmStrategy.RANDOM:
        ai_move = random.choice(list(Move))

    elif AI_ALGORITHM_STRATEGY == AiAlgorithmStrategy.SOMETIMES_CHEAT:
        do_cheat = random.random() < 0.2
        if do_cheat:
            if player_move == Move.ROCK:
                ai_move = Move.PAPER
            elif player_move == Move.PAPER:
                ai_move = Move.SCISSORS
            elif player_move == Move.SCISSORS:
                ai_move = Move.ROCK
        else:
            # Fair play
            ai_move = random.choice(list(Move))

    else:
        raise NotImplementedError()

    print(f"AI move: {ai_move}")
    return ai_move


def update_move_ui(playboard, player_move, ai_move):
    if player_move is not None:
        player_move_image = cv2.imread(f'resources/{player_move.name}.png', cv2.IMREAD_UNCHANGED)
        player_move_image = cv2.resize(player_move_image, (0, 0), None, 0.4, 0.4)
        playboard = cvzone.overlayPNG(playboard, player_move_image, (810, 230))

    if ai_move is not None:
        ai_move_image = cv2.imread(f'resources/{ai_move.name}.png', cv2.IMREAD_UNCHANGED)
        playboard = cvzone.overlayPNG(playboard, ai_move_image, (160, 260))
    return playboard


def update_scores(player_move, ai_move, scores):
    if (player_move == Move.ROCK and ai_move == Move.SCISSORS) or \
            (player_move == Move.PAPER and ai_move == Move.ROCK) or \
            (player_move == Move.SCISSORS and ai_move == Move.PAPER):
        # Player Wins
        scores[1] += 1

    if (player_move == Move.ROCK and ai_move == Move.PAPER) or \
            (player_move == Move.PAPER and ai_move == Move.SCISSORS) or \
            (player_move == Move.SCISSORS and ai_move == Move.ROCK):
        # AI Wins
        scores[0] += 1

    return scores


def update_score_ui(playboard, scores):
    cv2.putText(playboard, f"{scores[0]:02d}", (550, 410),
                cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 6)
    cv2.putText(playboard, f"{scores[1]:02d}", (655, 410),
                cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 6)
    return playboard


def update_game_status_text(playboard, game_status):
    if game_status == GameStatus.RUNNING_WAITING_FOR_SHAKE_BEGIN or game_status == GameStatus.RUNNING_SHAKING:
        cv2.putText(playboard, "Shake your hand and make a move!", (385, 697),
                    cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 2)

    elif game_status == GameStatus.RUNNING_SHOWING_RESULT:
        cv2.putText(playboard, "Press any key to continue.", (420, 697),
                    cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 2)

    elif game_status == GameStatus.RUNNING_SHAKE_DONE_INVALID_PLAYER_MOVE:
        cv2.putText(playboard, "Did not recognize your move. Press any key to continue.", (200, 697),
                    cv2.FONT_HERSHEY_PLAIN, 2, (32, 212, 254), 2)
    elif game_status == GameStatus.NOT_RUNNING:
        cv2.putText(playboard, "Press any key to start the game!", (385, 697),
                    cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 2)
    return playboard


class GameStatus(Enum):
    NOT_RUNNING = 1
    RUNNING_WAITING_FOR_SHAKE_BEGIN = 2
    RUNNING_SHAKING = 3
    RUNNING_SHOWING_RESULT = 4
    RUNNING_SHAKE_DONE_INVALID_PLAYER_MOVE = 5


def is_key_pressed():
    key = cv2.waitKey(1)
    return key > 0


def main():
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

        success, camera_img = vc.read()
        camera_img_scaled = cv2.resize(camera_img, (0, 0), None, 0.875, 0.875)
        camera_img_scaled = camera_img_scaled[:, 80:480]  # crop so that it fits to the box

        hands, camera_img = hand_detector.findHands(camera_img_scaled)

        playboard[213:633, 798:1198] = numpy.flip(camera_img_scaled, 1)

        if game_status != GameStatus.NOT_RUNNING:
            if hands:
                handshake_detector.calculate_movement_score(hands[0])

                handshake_status = handshake_detector.get_hand_shaking_status()

                if game_status == GameStatus.RUNNING_SHAKING and handshake_status == HandshakeStatus.STEADY:
                    # Player finished shaking

                    player_move = get_player_move(hands, hand_detector)
                    if player_move is None:
                        game_status = GameStatus.RUNNING_SHAKE_DONE_INVALID_PLAYER_MOVE
                    else:
                        game_status = GameStatus.RUNNING_SHOWING_RESULT
                        ai_move = do_ai_move(player_move)
                        scores = update_scores(player_move, ai_move, scores)

                elif (game_status == GameStatus.RUNNING_WAITING_FOR_SHAKE_BEGIN and handshake_status == HandshakeStatus.SHAKING):
                    game_status = GameStatus.RUNNING_SHAKING

                elif game_status == GameStatus.RUNNING_SHOWING_RESULT or \
                        game_status == GameStatus.RUNNING_SHAKE_DONE_INVALID_PLAYER_MOVE:
                    if is_key_pressed():
                        game_status = GameStatus.RUNNING_WAITING_FOR_SHAKE_BEGIN
                        ai_move = None
                        player_move = None

            else:
                handshake_detector.calculate_movement_score(None)

            playboard[213:633, 798:1198] = numpy.flip(camera_img_scaled, 1)

            # Update UI
            playboard = update_move_ui(playboard, player_move, ai_move)
            playboard = update_score_ui(playboard, scores)
        playboard = update_game_status_text(playboard, game_status)

        playboard = update_score_ui(playboard, scores)

        cv2.imshow('BG', playboard)

        if game_status == GameStatus.NOT_RUNNING:
            if is_key_pressed():
                game_status = GameStatus.RUNNING_WAITING_FOR_SHAKE_BEGIN

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


if __name__ == "__main__":
    main()
