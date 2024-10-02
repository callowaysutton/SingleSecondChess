#include <iostream>
#include <vector>
#include <string>
#include <cstdlib>
#include <ctime>
#include <thread>

// #define CHESS_NO_EXCEPTIONS

// Include the chess library header
#include "chess.hpp"

// Evaluation function that assigns material values to pieces
int evaluate(const chess::Board& board) {

    // Check if the game is over due to checkmate
    if (board.isGameOver().second == chess::GameResult::LOSE) {
        return -1000000;
    }
    if (board.isGameOver().second == chess::GameResult::WIN) {
        return 1000000;
    }
    // Heavily penalize repeated positions
    if (board.isRepetition() || board.isGameOver().second == chess::GameResult::DRAW) {
        return -1000000;
    }

    // Material values
    const int pawn = 100;
    const int knight = 320;
    const int bishop = 330;
    const int rook = 500;
    const int queen = 900;

    int white_material = 0;
    int black_material = 0;

    // Iterate over all squares
    for (int square = 0; square < 64; ++square) {
        auto piece = board.at(square);
        if (piece != chess::Piece::NONE) {
            int value = 0;

            if (piece.type() == chess::PieceType::KING) {
                value += 10000;
            }
            if (piece.type() == chess::PieceType::PAWN) {
                value += pawn;
            } else if (piece.type() == chess::PieceType::KNIGHT) {
                value += knight;
            } else if (piece.type() == chess::PieceType::BISHOP) {
                value += bishop;
            } else if (piece.type() == chess::PieceType::ROOK) {
                value += rook;
            } else if (piece.type() == chess::PieceType::QUEEN) {
                value += queen;
            }
            if (piece.color() == chess::Color::WHITE) {
                white_material += value;
            } else {
                black_material += value;
            }
        }
    }


    // Return the evaluation from the perspective of the side to move
    if (board.sideToMove() == chess::Color::WHITE) {
        return white_material - black_material;
    } else {
        return black_material - white_material;
    }
}

// Alpha-Beta pruning function
int alpha_beta(chess::Board board, int depth, int alpha, int beta, bool maximizingPlayer) {
    if (depth == 0) {
        return evaluate(board);
    }

    chess::Movelist moves;
    chess::movegen::legalmoves(moves, board);

    if (maximizingPlayer) {
        int maxEval = -1000000;
        for (const auto& move : moves) {
            chess::Board newBoard = board;  // Make a copy of the board
            newBoard.makeMove(move);
            int eval = alpha_beta(newBoard, depth - 1, alpha, beta, false);
            maxEval = std::max(maxEval, eval);
            alpha = std::max(alpha, eval);
            if (beta <= alpha)
                break;  // Beta cutoff
        }
        return maxEval;
    } else {
        int minEval = 1000000;
        for (const auto& move : moves) {
            chess::Board newBoard = board;  // Make a copy of the board
            newBoard.makeMove(move);
            int eval = alpha_beta(newBoard, depth - 1, alpha, beta, true);
            minEval = std::min(minEval, eval);
            beta = std::min(beta, eval);
            if (beta <= alpha)
                break;  // Alpha cutoff
        }
        return minEval;
    }
}

int main() {
    std::string fen;
    std::getline(std::cin, fen);

    // Initialize the board with the given FEN
    chess::Board board = chess::Board(fen);

    // Generate all legal moves
    chess::Movelist moves;
    chess::movegen::legalmoves(moves, board);

    int bestEval = -1000000;
    chess::Move bestMove = moves[0];
    int alpha = -1000000;
    int beta = 1000000;

    // Evaluate each move using Alpha-Beta pruning
    for (const auto& move : moves) {
        chess::Board newBoard = board;  // Make a copy of the board
        newBoard.makeMove(move);
        int eval = alpha_beta(newBoard, 3, alpha, beta, false);
        if (eval > bestEval) {
            bestEval = eval;
            bestMove = move;
        }
        alpha = std::max(alpha, eval);
    }

    // Output the best move in UCI format
    std::cout << chess::uci::moveToUci(bestMove) << std::endl;

    return 0;
}
