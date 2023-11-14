import time
from enum import Enum


class HandshakeStatus(Enum):
    # Hand is currently shaking
    SHAKING = 2

    # Hand has never shaked or finished shaking
    STEADY = 3

    # Hand has left the camera frame or was not detected
    FAILED = 4


class HandshakeDetector:
    def __init__(self) -> None:
        # Enable to print intermediate values for parameter tuning
        self._debug = False

        self._num_no_hand_detected = 0

        self._prev_landmarks = None
        self._prev_time = time.time()
        self._frame_movement_threshold = 25

        self._movement_history = []
        self._movement_history_running_average_window = 10
        self._movement_score_percent_threshold = 30

        # Percentage of the last _movement_history_running_average_window many frames where the hand was moving
        self.movement_score_percent = 0

        self.failed = False

    def debug(self, msg):
        if self._debug:
            print(msg)

    def calculate_movement_score(self, hand):
        if hand is None:
            self._num_no_hand_detected += 1

            # It could also be another constant other than self.running_average_window
            if self._num_no_hand_detected > self._movement_history_running_average_window:
                self.debug("Resetting handshake detector (no hand recognized for too long time)")
                self._prev_landmarks = None
                self._movement_history = []
                self._movement_score_percent_history = []
                self._num_no_hand_detected = 0
                self.failed = True

            return 0

        # Calculate time difference since the previous frame
        current_time = time.time()
        time_diff = current_time - self._prev_time

        hand_landmarks = hand["lmList"]
        if self._prev_landmarks is not None:
            assert len(hand_landmarks) == len(self._prev_landmarks)

        self.movement_score_percent = 0

        if self._prev_landmarks is not None:
            landmark_movements = []
            for idx, landmark in enumerate(hand_landmarks):
                # Calculate the change in position
                dx = landmark[0] - self._prev_landmarks[idx][0]
                dy = landmark[1] - self._prev_landmarks[idx][1]

                # Calculate the movement amount score based on the change in position
                # Use the Euclidean distance to measure the movement
                # Divide by a constant to make the number more human-friendly
                # It's the first derivative of the current position (=speed)
                this_landmark_movement = int(
                    (dx ** 2 + dy ** 2) / (time_diff ** 2) / 1000)
                landmark_movements.append(this_landmark_movement)

            this_frame_movement = int(
                sum(landmark_movements) / len(landmark_movements))
            self.debug(f"this_frame_movement: {this_frame_movement}")

            # Determine if hand is moving and append to history
            is_hand_moving = this_frame_movement > self._frame_movement_threshold
            # print(f"is_hand_moving: {is_hand_moving}")
            self._movement_history.append(is_hand_moving)

            if is_hand_moving:
                self.failed = False

            # Keep the list length within the running_average_window
            if len(self._movement_history) > self._movement_history_running_average_window:
                self._movement_history.pop(0)

            # Calculate the running average of frames where the hand was moving
            self.movement_score_percent = int(
                sum(self._movement_history) / len(self._movement_history) * 100)

        # Update the previous landmarks and time for the next frame
        self._prev_landmarks = hand_landmarks
        self._prev_time = current_time

        self.debug(f"movement_score_percent: {self.movement_score_percent}")
        return self.movement_score_percent

    def get_hand_shaking_status(self):
        """
        Calculates hand shaking status using the second derivative (acceleration)
        """
        handshake_status = HandshakeStatus.STEADY

        if self.failed:
            handshake_status = HandshakeStatus.FAILED

        if self.movement_score_percent > self._movement_score_percent_threshold:
            handshake_status = HandshakeStatus.SHAKING

        self.debug(f"handshake_status: {handshake_status}")
        return handshake_status
