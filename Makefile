# Compiler and flags
CXX = g++
CXXFLAGS = -std=c++17 -O2 -march=native -Wall -Wextra -Werror -pedantic

# Executables
EXEC1 = p1
EXEC2 = p2
EXEC3 = wrapper

# Source files
SRC1 = example_bots/random_move_bot.cpp
SRC2 = example_bots/ab_tree_bot.cpp
SRC3 = wrapper.cpp

# Add chess.hpp to the include path
CXXFLAGS += -I.

# Default target, build all executables
all: $(EXEC1) $(EXEC2) $(EXEC3)

# Rule for first executable
$(EXEC1): $(SRC1)
	$(CXX) $(CXXFLAGS) -o $(EXEC1) $(SRC1)

# Rule for second executable
$(EXEC2): $(SRC2)
	$(CXX) $(CXXFLAGS) -o $(EXEC2) $(SRC2)

# Rule for third executable
$(EXEC3): $(SRC3)
	$(CXX) $(CXXFLAGS) -o $(EXEC3) $(SRC3)

# Clean up object files and executables
clean:
	rm -rf $(EXEC1) $(EXEC2) $(EXEC3) jail/

# Run the project by cleaning, building and then running ./airgap_runner.sh
run: clean all
	./airgap_runner.sh