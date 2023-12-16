import json
import math
import os
import time
from enum import Enum

import cv2
import cvzone
from cvzone.HandTrackingModule import HandDetector
import random
from gtts import gTTS
import os
import threading
import numpy as np
from handshake_detector import HandshakeDetector, HandshakeStatus
import random


def speak_text(text):
    tts = gTTS(text=text, lang='en')
    tts.save("speech.mp3")
    os.system("afplay speech.mp3")


class AiAlgorithmStrategy(Enum):
    RANDOM = 1
    SOMETIMES_CHEAT = 2
    MARKOV_CHAIN = 3


AI_ALGORITHM_STRATEGY = AiAlgorithmStrategy.MARKOV_CHAIN


class Move(Enum):
    ROCK = 0
    PAPER = 1
    SCISSORS = 2


last_frame_key_pressed = False
game_play_id = int(time.time())
ai_hand_shaking_frame_idx = 0
scores = [0, 0]
rounds = -1

# Dimension 0: 3 previous player moves (rock, paper, scissors)
# Dimension 1: 3 previous AI moves (rock, paper, scissors)
# Dimension 2: 3 next player moves (rock, paper, scissors)
markov_chain_matrix = np.zeros((3, 3, 3), dtype=int)


def get_player_move(hands, hand_detector) -> Move:
    player_move = None
    hand = hands[0]
    fingers = hand_detector.fingersUp(hand)
    print(f"player fingers: {fingers}")

    # todo find better
    if fingers == [0, 0, 0, 0, 0] or fingers == [1, 0, 0, 0, 0] or fingers == [0, 0, 0, 0, 1]:
        player_move = Move.ROCK
    elif fingers == [1, 1, 1, 1, 1] or fingers == [0, 1, 1, 1, 1]:
        player_move = Move.PAPER
    elif fingers == [0, 1, 1, 0, 0] or fingers == [1, 1, 1, 0, 0]:
        player_move = Move.SCISSORS

    print(f"player move: {player_move}")

    return player_move


def get_beating_move(move: Move) -> Move:
    if move == Move.ROCK:
        return Move.PAPER
    elif move == Move.PAPER:
        return Move.SCISSORS
    elif move == Move.SCISSORS:
        return Move.ROCK
    else:
        raise AssertionError()


def do_ai_move(player_move, last_ai_move, last_player_move) -> Move:
    global markov_chain_matrix

    if AI_ALGORITHM_STRATEGY == AiAlgorithmStrategy.RANDOM:
        ai_move = random.choice(list(Move))

    elif AI_ALGORITHM_STRATEGY == AiAlgorithmStrategy.SOMETIMES_CHEAT:
        do_cheat = random.random() < 0.2
        if do_cheat:
            ai_move = get_beating_move(player_move)
        else:
            # Fair play
            ai_move = random.choice(list(Move))

    elif AI_ALGORITHM_STRATEGY == AiAlgorithmStrategy.MARKOV_CHAIN:
        if last_player_move is None:
            # First round
            ai_move = random.choice(list(Move))
        else:
            predicted_player_move = np.argmax(markov_chain_matrix[last_player_move.value, last_ai_move.value])
            print(f"Markov predicted_player_move: {predicted_player_move}")

            # Choose a move to beat the predicted move
            ai_move = get_beating_move(Move(predicted_player_move))

    else:
        raise NotImplementedError()

    print(f"AI move: {ai_move}")
    return ai_move


def update_move_ui(playboard, player_move, ai_move, game_status):
    global ai_hand_shaking_frame_idx

    if game_status is not GameStatus.RUNNING_WAITING_FOR_SHAKE_BEGIN \
            and game_status is not GameStatus.RUNNING_SHAKING \
            and player_move is not None:
        player_move_image = cv2.imread(f'resources/{player_move.name}.png', cv2.IMREAD_UNCHANGED)
        player_move_image = cv2.resize(player_move_image, (0, 0), None, 0.4, 0.4)
        playboard = cvzone.overlayPNG(playboard, player_move_image, (810, 230))

    if game_status is not GameStatus.RUNNING_WAITING_FOR_SHAKE_BEGIN \
            and game_status is not GameStatus.RUNNING_SHAKING \
            and ai_move is not None:
        ai_move_image = cv2.imread(f'resources/{ai_move.name}.png', cv2.IMREAD_UNCHANGED)
        playboard = cvzone.overlayPNG(playboard, ai_move_image, (160, 260))

    if game_status == GameStatus.RUNNING_SHAKING:
        # Display robot shaking animation
        ai_move_image = cv2.imread(f'resources/ROCK.png', cv2.IMREAD_UNCHANGED)
        y_shift = int(math.sin(ai_hand_shaking_frame_idx * 0.4) * 50)
        playboard = cvzone.overlayPNG(playboard, ai_move_image, (160, 260 + y_shift))
        ai_hand_shaking_frame_idx += 1

    return playboard


def update_scores(player_move, ai_move, scores, rounds):

    player_won = 0
    if (player_move == Move.ROCK and ai_move == Move.SCISSORS) or \
            (player_move == Move.PAPER and ai_move == Move.ROCK) or \
            (player_move == Move.SCISSORS and ai_move == Move.PAPER):
        # Player Wins
        scores[1] += 1
        player_won= 1

    elif (player_move == Move.ROCK and ai_move == Move.PAPER) or \
            (player_move == Move.PAPER and ai_move == Move.SCISSORS) or \
            (player_move == Move.SCISSORS and ai_move == Move.ROCK):
        # AI Wins
        scores[0] += 1
        player_won = -1

    rounds += 1

    return scores, player_won, rounds


def update_markov_chain(last_player_move, last_ai_move, player_move):
    global markov_chain_matrix

    if last_player_move is None:
        print("First round, cannot yet update Markov chain matrix")
    else:
        markov_chain_matrix[last_player_move.value, last_ai_move.value, player_move.value] += 1

        print("markov_chain_matrix:")

        print_markov_chain_matrix_for(Move.ROCK, Move.ROCK)
        print_markov_chain_matrix_for(Move.ROCK, Move.PAPER)
        print_markov_chain_matrix_for(Move.ROCK, Move.SCISSORS)

        print_markov_chain_matrix_for(Move.PAPER, Move.ROCK)
        print_markov_chain_matrix_for(Move.PAPER, Move.PAPER)
        print_markov_chain_matrix_for(Move.PAPER, Move.SCISSORS)

        print_markov_chain_matrix_for(Move.SCISSORS, Move.ROCK)
        print_markov_chain_matrix_for(Move.SCISSORS, Move.PAPER)
        print_markov_chain_matrix_for(Move.SCISSORS, Move.SCISSORS)


def print_markov_chain_matrix_for(last_player_move: Move, last_ai_move: Move):
    global markov_chain_matrix

    print(
        f"  Last P move: {last_player_move.name}, last AI move: {last_ai_move.name}, num next P ROCK moves: {markov_chain_matrix[last_player_move.value, last_ai_move.value, Move.ROCK.value]}")
    print(
        f"  Last P move: {last_player_move.name}, last AI move: {last_ai_move.name}, num next P PAPER moves: {markov_chain_matrix[last_player_move.value, last_ai_move.value, Move.PAPER.value]}")
    print(
        f"  Last P move: {last_player_move.name}, last AI move: {last_ai_move.name}, num next P SCISSORS moves: {markov_chain_matrix[last_player_move.value, last_ai_move.value, Move.SCISSORS.value]}")


def save_game_play_log():
    global game_play_id, markov_chain_matrix, scores

    game_play_log_path = os.path.join("game_play_logs", f"{game_play_id}.json")
    with open(game_play_log_path, 'w') as f:
        f.write(
            json.dumps({
                "game_play_id": game_play_id,
                "ai_algorithm_strategy": AI_ALGORITHM_STRATEGY.name,
                "markov_chain_matrix": markov_chain_matrix.tolist(),
                "scores": scores,
            }, indent=4)
        )


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
    global last_frame_key_pressed
    return last_frame_key_pressed


def main():
    global ai_hand_shaking_frame_idx, scores, last_frame_key_pressed, rounds

    ai_lost = ['You won!', 'Keep going!', 'Nice one!', 'Well done!', 'Wow!', 'Impressive!', 'Good job!', 'Fantastic!']
    ai_won = ['Haha you lost!', 'Level up your game!', 'Maybe next time?', 'Cant beat me!', 'Nice try!', 'Victory is mine!', 'Too easy!']
    ai_neural = ['Great minds think alike', 'Tie!', 'Its a draw!', 'Same choice!', 'We match!', 'No winner this time!']

    vc = cv2.VideoCapture(0)
    vc.set(3, 640)
    vc.set(4, 480)

    game_status = GameStatus.NOT_RUNNING

    hand_detector = HandDetector(maxHands=1)
    handshake_detector = HandshakeDetector()

    player_move = None
    last_player_move = None
    last_ai_move = None
    ai_move = None

    while True:
        playboard = cv2.imread('resources/BG.png')  # background

        success, camera_img = vc.read()
        camera_img_scaled = cv2.resize(camera_img, (0, 0), None, 0.875, 0.875)
        camera_img_scaled = cv2.flip(camera_img_scaled, 1)
        camera_img_scaled = camera_img_scaled[:, 80:480]  # crop so that it fits to the box

        hands, camera_img = hand_detector.findHands(camera_img_scaled, flipType=False)

        playboard[213:633, 798:1198] = camera_img_scaled

        if game_status != GameStatus.NOT_RUNNING:
            if hands:
                handshake_detector.calculate_movement_score(hands[0])

                handshake_status = handshake_detector.get_hand_shaking_status()

                if game_status == GameStatus.RUNNING_SHAKING and handshake_status == HandshakeStatus.STEADY:
                    # Player finished shaking

                    print(f"bef up: {player_move}")
                    last_player_move = player_move
                    last_ai_move = ai_move
                    player_move = get_player_move(hands, hand_detector)
                    print(f"aft up: {player_move}")
                    if player_move is None:
                        game_status = GameStatus.RUNNING_SHAKE_DONE_INVALID_PLAYER_MOVE
                    else:
                        game_status = GameStatus.RUNNING_SHOWING_RESULT
                        ai_move = do_ai_move(player_move, last_ai_move, last_player_move)
                        scores, player_won, rounds = update_scores(player_move, ai_move, scores, rounds)
                        if rounds % 3 == 0:
                            ai_text = ''
                            if player_won == 1:
                                i = random.randint(0, len(ai_lost)-1)
                                ai_text = ai_lost[i]
                                x = threading.Thread(target=speak_text, args=(ai_text,))
                                x.start()
                            elif player_won == -1:
                                i = random.randint(0, len(ai_won)-1)
                                ai_text = ai_won[i]
                                x = threading.Thread(target=speak_text, args=(ai_text,))
                                #x = threading.Thread(target=speak_text, args=(f"HA HA, I WON",))
                                x.start()
                            else:
                                i = random.randint(0, len(ai_neural)-1)
                                ai_text = ai_neural[0]
                                x = threading.Thread(target=speak_text, args=(ai_text,))
                                #x = threading.Thread(target=speak_text, args=(f"Great minds think alike.",))
                                x.start()

                        # Update Markov chain
                        update_markov_chain(last_player_move, last_ai_move, player_move)
                        save_game_play_log()

                elif (
                        game_status == GameStatus.RUNNING_WAITING_FOR_SHAKE_BEGIN and handshake_status == HandshakeStatus.SHAKING):
                    game_status = GameStatus.RUNNING_SHAKING
                    ai_hand_shaking_frame_idx = 0  # Start AI shaking animation from the beginning

                elif game_status == GameStatus.RUNNING_SHOWING_RESULT or \
                        game_status == GameStatus.RUNNING_SHAKE_DONE_INVALID_PLAYER_MOVE:
                    if is_key_pressed():
                        game_status = GameStatus.RUNNING_WAITING_FOR_SHAKE_BEGIN

            else:
                handshake_detector.calculate_movement_score(None)

            # Update UI
            playboard = update_move_ui(playboard, player_move, ai_move, game_status)
            playboard = update_score_ui(playboard, scores)
        playboard = update_game_status_text(playboard, game_status)

        playboard = update_score_ui(playboard, scores)

        cv2.imshow('BG', playboard)

        if game_status == GameStatus.NOT_RUNNING:
            if is_key_pressed():
                game_status = GameStatus.RUNNING_WAITING_FOR_SHAKE_BEGIN
                x = threading.Thread(target=speak_text, args=("Let's play!",))
                x.start()

        last_frame_key_pressed = False
        pressed_key = cv2.pollKey()
        if pressed_key & 0xFF == ord('q'):
            break
        elif pressed_key != -1:
            print(f"A non-q key was pressed")
            last_frame_key_pressed = True


if __name__ == "__main__":
    main()
