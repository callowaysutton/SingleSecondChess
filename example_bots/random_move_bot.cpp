#include <iostream>
#include <vector>
#include <string>
#include <cstdlib>
#include <ctime>
#include <thread>

// Include the chess library header
#include "chess.hpp"  // Assuming you have the chess library header in your include path

int main() {
    std::string fen;
    std::getline(std::cin, fen);

    // Initialize the board with the given FEN
    chess::Board board = chess::Board(fen);

    // Generate all legal moves
    chess::Movelist moves;
    chess::movegen::legalmoves(moves, board);

    // Seed the random number generator
    std::srand(static_cast<unsigned int>(std::time(nullptr)));

    // Select a random move
    const auto random_move = moves[std::rand() % moves.size()];

    // Output the random move
    std::cout << chess::uci::moveToUci(random_move) << std::endl;

    // Print the first legal move
    // std::cout << chess::uci::moveToUci(moves[0]) << std::endl;

    return 0;
}
