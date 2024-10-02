#!/bin/bash

# Count occurrences of each string
player1_wins=$(grep -r "Player 1 wins!" logs/ | wc -l)
player2_wins=$(grep -r "Player 2 wins!" logs/ | wc -l)
draws=$(grep -r "Draw!" logs/ | wc -l)

# Output the results
echo "Player 1 wins: $player1_wins"
echo "Player 2 wins: $player2_wins"
echo "Draws: $draws"
