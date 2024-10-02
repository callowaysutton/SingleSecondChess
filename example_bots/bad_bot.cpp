// Reads from stdin and writes random alphanumeric characters to stdout

#include <iostream>
#include <string>
#include <cstdlib>
#include <ctime>
#include <random>

int main() {
    std::string input;
    std::getline(std::cin, input);

    std::srand(static_cast<unsigned int>(std::time(nullptr)));
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, 61);

    for (char c : input) {
        if (std::isalnum(c)) {
            std::cout << c;
        } else {
            std::cout << static_cast<char>(dis(gen) + (c < 58 ? 48 : (c < 91 ? 55 : 61)));
        }
    }

    return 0;
}