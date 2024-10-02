#include <iostream>
#include <sstream>
#include <string>
#include <vector>
#include <cstdio>
#include <cstdlib>
#include <unistd.h>
#include <sys/ioctl.h>
#include <linux/perf_event.h>
#include <asm/unistd.h>
#include <cstring>
#include <regex>
#include <unordered_map>
#include "chess.hpp"

int main() {
    std::string fen = chess::constants::STARTPOS;
    chess::Board board = chess::Board(fen);

    bool global_executable = false;

    // Check if the p1/p2 executables exist locally or in /bin
    if (access("./p1", F_OK) != -1) {
        std::cout << "Found p1 executable locally." << std::endl;
    } else if (access("/bin/p1", F_OK) != -1) {
        std::cout << "Found p1 executable in /bin." << std::endl;
        global_executable = true;
    } else {
        std::cerr << "p1 executable not found." << std::endl;
        return 1;
    }

    bool game_over = false;
    int turn = 0; // 0 for player1, 1 for player2

    std::unordered_map<std::string, int> position_counts;
    position_counts[fen] = 1;

    while (!game_over) {
        std::string command;
        if (global_executable) {
            // Construct command for the current player
            command = "echo \"" + fen + "\" | timeout 5 perf stat -e instructions:u /bin/p" + std::to_string(turn + 1) + " 2>&1";
        } else {
            // Construct command for the current player
            command = "echo \"" + fen + "\" | timeout 5 perf stat -e instructions:u ./p" + std::to_string(turn + 1) + " 2>&1";
        }

        // Open a pipe to read the bot's stdout and stderr
        FILE* bot_pipe = popen(command.c_str(), "r");
        if (!bot_pipe) {
            std::cerr << "Failed to run bot." << std::endl;

            // Print the error message
            perror("popen");
            return 1;
        }

        char buffer[1024];
        std::string output_str;

        while (fgets(buffer, sizeof(buffer), bot_pipe) != NULL) {
            output_str += buffer;
        }

        // Print the whole output
        // std::cout << output_str << std::endl;

        // Get the exit status
        int status = pclose(bot_pipe);

        if (WIFEXITED(status)) {
            int exit_status = WEXITSTATUS(status);
            if (exit_status == 124) {
                std::cout << "Player " << (turn + 1) << " exceeded time limit." << std::endl;
                std::cout << "Player " << (turn == 0 ? "2" : "1") << " wins!" << std::endl;
                game_over = true;
                continue;
            } else if (exit_status != 0) {
                std::cout << "Player " << (turn + 1) << " program exited with error status " << exit_status << "." << std::endl;
                std::cout << "Player " << (turn == 0 ? "2" : "1") << " wins!" << std::endl;
                game_over = true;
                continue;
            }
        } else if (WIFSIGNALED(status)) {
            int term_signal = WTERMSIG(status);
            std::cout << "Player " << (turn + 1) << " program terminated by signal " << term_signal << "." << std::endl;
            std::cout << "Player " << (turn == 0 ? "2" : "1") << " wins!" << std::endl;
            game_over = true;
            continue;
        }

        // Parse move_str and instructions count
        std::istringstream iss(output_str);
        std::string line;
        uint64_t instructions = 0;
        std::string move_str;

        std::regex uci_move_regex("^[a-h][1-8][a-h][1-8][nbrqNBRQ]?$");

        while (std::getline(iss, line)) {
            // Trim leading and trailing whitespace
            size_t first = line.find_first_not_of(" \t\r\n");
            size_t last = line.find_last_not_of(" \t\r\n");
            if (first != std::string::npos && last != std::string::npos) {
                line = line.substr(first, (last - first + 1));
            } else {
                line = "";
            }

            // Check if the line contains "instructions"
            if (line.find("instructions") != std::string::npos) {
                // Extract the number preceding "instructions"
                size_t instr_pos = line.find("instructions");
                if (instr_pos != std::string::npos) {
                    // Get the substring before "instructions"
                    std::string before_instr = line.substr(0, instr_pos);
                    // Trim any trailing whitespace
                    before_instr.erase(before_instr.find_last_not_of(" \t\r\n") + 1);

                    // Now, the number may have commas, remove them
                    before_instr.erase(std::remove(before_instr.begin(), before_instr.end(), ','), before_instr.end());

                    // Remove any non-digit characters
                    before_instr.erase(std::remove_if(before_instr.begin(), before_instr.end(),
                                                      [](unsigned char c) { return !std::isdigit(c); }),
                                       before_instr.end());

                    // Convert to uint64_t
                    if (!before_instr.empty()) {
                        try {
                            instructions = std::stoull(before_instr);
                        } catch (const std::exception& e) {
                            std::cerr << "Failed to parse instructions count: " << e.what() << std::endl;
                            return 1;
                        }
                    }
                }
            } else if (!line.empty()) {
                // If the line matches the UCI move regex, treat it as the move
                if (std::regex_match(line, uci_move_regex)) {
                    move_str = line;
                }
            }
        }

        // Output the extracted instructions count and move
        std::cout << "Instructions: " << instructions << std::endl;
        std::cout << "Player " << (turn + 1) << " Move: " << move_str << std::endl;
        std::cout << "FEN: " << fen << std::endl;

        // Check instruction limit
        if (instructions > 5000000000ULL) {
            std::cout << "Player " << (turn + 1) << " exceeded instruction limit." << std::endl;
            std::cout << "Player " << (turn == 0 ? "2" : "1") << " wins!" << std::endl;
            game_over = true;
            continue;
        }

        // Now validate the move
        chess::Movelist moves;
        chess::movegen::legalmoves(moves, board);

        // Compare UCI move strings
        bool move_is_valid = false;
        chess::Move valid_move;
        for (const auto &move : moves) {
            std::ostringstream oss;
            oss << move;

            if (oss.str() == move_str) {
                move_is_valid = true;
                valid_move = move;
                break;
            }
        }

        if (move_is_valid) {
            std::cout << "Move " << move_str << " is valid." << std::endl;

            // Apply the move
            board.makeMove(valid_move);

            // Update the FEN
            fen = board.getFen();

            // Print the board
            std::cout << board << std::endl;
        } else {
            std::cout << "Move " << move_str << " is invalid." << std::endl;
            // Indicate which bot made the invalid move
            std::cout << "Player " << (turn + 1) << " made an invalid move." << std::endl;
            std::cout << "Player " << (turn == 0 ? "2" : "1") << " wins!" << std::endl;
            game_over = true;
            continue;
        }

        // Check if the game is over
        if (board.isGameOver().second != chess::GameResult::NONE) {
            std::cout << "Game over!" << std::endl;

            // Print the game result
            if (board.isGameOver().second == chess::GameResult::DRAW) {
                // Print out the reason
                if (board.isGameOver().first == chess::GameResultReason::STALEMATE) {
                    std::cout << "Stalemate!" << std::endl;
                } else if (board.isGameOver().first == chess::GameResultReason::INSUFFICIENT_MATERIAL) {
                    std::cout << "Insufficient material!" << std::endl;
                } else if (board.isGameOver().first == chess::GameResultReason::FIFTY_MOVE_RULE) {
                    std::cout << "Fifty move rule!" << std::endl;
                } else if (board.isGameOver().first == chess::GameResultReason::THREEFOLD_REPETITION) {
                    std::cout << "Threefold repetition!" << std::endl;
                }

                std::cout << "Draw!" << std::endl;
            } else {
                std::cout << "Player " << (turn + 1) << " wins!" << std::endl;
            }
            game_over = true;
            continue;
        }

        // Switch turns
        turn = 1 - turn;
    }

    return 0;
}
