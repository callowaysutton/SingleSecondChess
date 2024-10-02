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

    // Print the first legal move
    std::cout << chess::uci::moveToUci(moves[0]) << std::endl;

    return 0;
}
