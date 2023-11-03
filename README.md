# Rock Paper AI

Play the rock paper scissors game against an AI!

## How to run?

Connect a camera to your machine. It is used to determine the player's move.

1. Install Python version 3
2. `pip install -U -r requirements.txt`
3. ` python main.py`

## AI strategies

You can choose from the following strategies that the AI will follow to determine its move:

* Random (`RANDOM`)
* Cheat with 20% change, such that it will win against the player (`SOMETIMES_CHEAT`)
* Markov chain approach based on the last and current player's move (`MARKOV_CHAIN`)

Currently, the AI strategy is set at the beginning of the `main.py` file.
