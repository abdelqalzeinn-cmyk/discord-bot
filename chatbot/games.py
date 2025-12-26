<<<<<<< HEAD
import random
import discord
from typing import Dict, List, Tuple, Optional
from discord.ext import commands

# Hangman game class
class HangmanGame:
    def __init__(self, word: str):
        self.word = word.upper()
        self.guessed_letters = set()
        self.incorrect_guesses = 0
        self.max_attempts = 6
        self.hangman_parts = [
            "",
            "  ____\n |    |\n |    \n |    \n |     \n_|_\n",
            "  ____\n |    |\n |    O\n |    \n |     \n_|_\n",
            "  ____\n |    |\n |    O\n |    |\n |     \n_|_\n",
            "  ____\n |    |\n |   \O\n |    |\n |     \n_|_\n",
            "  ____\n |    |\n |   \O/\n |    |\n |     \n_|_\n",
            "  ____\n |    |\n |   \O/\n |    |\n |   /   \n_|_\n",
            "  ____\n |    |\n |   \O/\n |    |\n |   / \\ \n_|_\n"
        ]

    def get_hangman(self) -> str:
        """Get the current hangman state"""
        return self.hangman_parts[min(self.incorrect_guesses, len(self.hangman_parts) - 1)]

    def get_display_word(self) -> str:
        """Get the word with underscores for unguessed letters"""
        return ' '.join(letter if letter in self.guessed_letters else '_' for letter in self.word)

    def guess_letter(self, letter: str) -> Tuple[bool, str]:
        """
        Guess a letter
        Returns: (game_over, message)
        """
        letter = letter.upper()
        
        if len(letter) != 1 or not letter.isalpha():
            return False, "Please guess a single letter."
            
        if letter in self.guessed_letters:
            return False, f"You've already guessed '{letter}'. Try a different letter."
            
        self.guessed_letters.add(letter)
        
        if letter not in self.word:
            self.incorrect_guesses += 1
            
            if self.incorrect_guesses >= self.max_attempts:
                return True, f"Game Over! The word was: {self.word}\n{self.get_hangman()}"
                
            return False, f"Incorrect guess! {self.max_attempts - self.incorrect_guesses} attempts left.\n{self.get_hangman()}"
        
        if all(letter in self.guessed_letters for letter in self.word):
            return True, f"Congratulations! You guessed the word: {self.word}"
            
        return False, f"Good guess!\n{self.get_display_word()}\n{self.get_hangman()}"

# Quiz game class
class QuizGame:
    def __init__(self, questions: List[Dict[str, str]]):
        self.questions = questions
        self.current_question = None
        self.score = 0
        self.question_number = 0
        self.total_questions = len(questions)
        self.get_new_question()
    
    def get_new_question(self) -> Optional[Dict[str, str]]:
        """Get a new random question"""
        if not self.questions:
            return None
            
        self.current_question = random.choice(self.questions)
        self.questions.remove(self.current_question)
        self.question_number += 1
        return self.current_question
    
    def check_answer(self, answer: str) -> Tuple[bool, str]:
        """
        Check if the answer is correct
        Returns: (is_correct, message)
        """
        if not self.current_question:
            return False, "No active question. Start a new quiz with !quiz."
            
        correct_answer = self.current_question['answer'].lower()
        is_correct = answer.lower() == correct_answer.lower()
        
        if is_correct:
            self.score += 1
            message = f"✅ Correct! {self.current_question.get('explanation', '')}"
        else:
            message = f"❌ Incorrect! The correct answer was: {correct_answer}"
            
        return is_correct, message

# Rock-Paper-Scissors game class
class RPSGame:
    CHOICES = ["rock", "paper", "scissors"]
    
    @staticmethod
    def get_winner(player_choice: str, bot_choice: str) -> str:
        """Determine the winner of a Rock-Paper-Scissors game"""
        player_choice = player_choice.lower()
        bot_choice = bot_choice.lower()
        
        if player_choice == bot_choice:
            return "tie"
            
        if (player_choice == "rock" and bot_choice == "scissors") or \
           (player_choice == "paper" and bot_choice == "rock") or \
           (player_choice == "scissors" and bot_choice == "paper"):
            return "player"
            
        return "bot"
    
    @staticmethod
    def get_random_choice() -> str:
        """Get a random choice for the bot"""
        return random.choice(RPSGame.CHOICES)

class TicTacToeGame:
    def __init__(self, player1: discord.Member, player2: discord.Member = None, difficulty: str = 'medium'):
        self.board = [" " for _ in range(9)]
        self.players = [player1, player2] if player2 else [player1]
        self.current_player = 0
        self.symbols = ["❌", "⭕"]
        self.winner = None
        self.game_over = False
        self.difficulty = difficulty.lower() if player2 is None else None
        self.is_ai_game = player2 is None
    
    def make_move(self, position: int) -> bool:
        """Make a move on the board. Returns True if move was valid, False otherwise."""
        if position < 0 or position >= 9 or self.board[position] != " " or self.game_over:
            return False
            
        self.board[position] = self.symbols[self.current_player]
        
        # Check for win or draw
        if self.check_winner():
            self.winner = self.players[self.current_player]
            self.game_over = True
        elif " " not in self.board:
            self.game_over = True
        else:
            self.current_player = 1 - self.current_player
            
        return True
    
    def make_ai_move(self) -> bool:
        """Make an AI move based on difficulty level. Returns True if move was made, False if game is over."""
        if self.game_over:
            return False
            
        if not self.is_ai_game:
            return False
            
        # Get AI's symbol and opponent's symbol
        ai_symbol = self.symbols[self.current_player]
        opponent_symbol = self.symbols[1 - self.current_player]
        
        available_moves = self.get_available_moves()
        if not available_moves:
            return False
            
        # Easy difficulty - completely random moves
        if self.difficulty == 'easy':
            return self.make_move(random.choice(available_moves))
            
        # Medium difficulty - basic strategy (blocks wins, takes center/corners)
        if self.difficulty == 'medium':
            # 30% chance to make a random move
            if random.random() < 0.3:
                return self.make_move(random.choice(available_moves))
                
        # Hard difficulty (default) - optimal strategy
        # 1. Check if AI can win in the next move
        winning_move = self.get_winning_move(ai_symbol)
        if winning_move is not None:
            return self.make_move(winning_move)
        
        # 2. Check if opponent can win in the next move and block them
        blocking_move = self.get_winning_move(opponent_symbol)
        if blocking_move is not None:
            return self.make_move(blocking_move)
        
        # 3. Take center if available
        if self.board[4] == " ":
            return self.make_move(4)
            
        # 4. Take a corner if available
        corners = [0, 2, 6, 8]
        available_corners = [c for c in corners if self.board[c] == " "]
        if available_corners:
            return self.make_move(random.choice(available_corners))
            
        # 5. Take a side if available
        sides = [1, 3, 5, 7]
        available_sides = [s for s in sides if self.board[s] == " "]
        if available_sides:
            return self.make_move(random.choice(available_sides))
            
        return False
    
    def check_winner(self) -> bool:
        """Check if current player has won."""
        symbol = self.symbols[self.current_player]
        # Check rows, columns and diagonals
        win_conditions = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
            [0, 4, 8], [2, 4, 6]              # Diagonals
        ]
        return any(all(self.board[i] == symbol for i in condition) for condition in win_conditions)
    
    def get_available_moves(self) -> list[int]:
        """Return list of available move indices."""
        return [i for i, spot in enumerate(self.board) if spot == " "]
    
    def get_winning_move(self, symbol: str) -> int:
        """Return a winning move for the given symbol if available, else None."""
        for move in self.get_available_moves():
            # Try the move
            self.board[move] = symbol
            # Check if it's a winning move
            win_conditions = [
                [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
                [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
                [0, 4, 8], [2, 4, 6]              # Diagonals
            ]
            for condition in win_conditions:
                if all(self.board[i] == symbol for i in condition):
                    # Undo the move
                    self.board[move] = " "
                    return move
            # Undo the move
            self.board[move] = " "
        return None
    
    def get_board_display(self) -> str:
        """Return a string representation of the board."""
        board = ""
        for i in range(0, 9, 3):
            board += " | ".join(self.board[i:i+3]) + "\n"
            if i < 6:
                board += "---------"
            board += "\n"
        return board

# Sample quiz questions with multiple choice options
QUIZ_QUESTIONS = [
    {
        "question": "What is the capital of France?",
        "answer": "Paris",
        "options": ["London", "Berlin", "Madrid", "Paris"],
        "explanation": "Paris is known as the 'City of Light' and is famous for the Eiffel Tower."
    },
    {
        "question": "Which planet is known as the Red Planet?",
        "answer": "Mars",
        "options": ["Venus", "Mars", "Jupiter", "Saturn"],
        "explanation": "Mars appears reddish due to iron oxide (rust) on its surface."
    },
    {
        "question": "What is the largest mammal in the world?",
        "answer": "Blue Whale",
        "options": ["African Elephant", "Blue Whale", "Giraffe", "Polar Bear"],
        "explanation": "Blue Whales can grow up to 100 feet long and weigh as much as 200 tons!"
    },
    {
        "question": "Who painted the Mona Lisa?",
        "answer": "Leonardo da Vinci",
        "options": ["Pablo Picasso", "Vincent van Gogh", "Leonardo da Vinci", "Michelangelo"],
        "explanation": "Painted between 1503 and 1519, it's one of the most famous paintings in the world."
    },
    {
        "question": "What is the chemical symbol for gold?",
        "answer": "Au",
        "options": ["Ag", "Fe", "Au", "Cu"],
        "explanation": "The symbol Au comes from the Latin word for gold, 'aurum'."
    }
]

# Sample hangman words
HANGMAN_WORDS = [
    "PYTHON", "JAVASCRIPT", "PROGRAMMING", "DEVELOPER", "COMPUTER",
    "KEYBOARD", "MONITOR", "INTERNET", "ALGORITHM", "FUNCTION"
]
=======
import random
import discord
from typing import Dict, List, Tuple, Optional
from discord.ext import commands

# Hangman game class
class HangmanGame:
    def __init__(self, word: str):
        self.word = word.upper()
        self.guessed_letters = set()
        self.incorrect_guesses = 0
        self.max_attempts = 6
        self.hangman_parts = [
            "",
            "  ____\n |    |\n |    \n |    \n |     \n_|_\n",
            "  ____\n |    |\n |    O\n |    \n |     \n_|_\n",
            "  ____\n |    |\n |    O\n |    |\n |     \n_|_\n",
            "  ____\n |    |\n |   \O\n |    |\n |     \n_|_\n",
            "  ____\n |    |\n |   \O/\n |    |\n |     \n_|_\n",
            "  ____\n |    |\n |   \O/\n |    |\n |   /   \n_|_\n",
            "  ____\n |    |\n |   \O/\n |    |\n |   / \\ \n_|_\n"
        ]

    def get_hangman(self) -> str:
        """Get the current hangman state"""
        return self.hangman_parts[min(self.incorrect_guesses, len(self.hangman_parts) - 1)]

    def get_display_word(self) -> str:
        """Get the word with underscores for unguessed letters"""
        return ' '.join(letter if letter in self.guessed_letters else '_' for letter in self.word)

    def guess_letter(self, letter: str) -> Tuple[bool, str]:
        """
        Guess a letter
        Returns: (game_over, message)
        """
        letter = letter.upper()
        
        if len(letter) != 1 or not letter.isalpha():
            return False, "Please guess a single letter."
            
        if letter in self.guessed_letters:
            return False, f"You've already guessed '{letter}'. Try a different letter."
            
        self.guessed_letters.add(letter)
        
        if letter not in self.word:
            self.incorrect_guesses += 1
            
            if self.incorrect_guesses >= self.max_attempts:
                return True, f"Game Over! The word was: {self.word}\n{self.get_hangman()}"
                
            return False, f"Incorrect guess! {self.max_attempts - self.incorrect_guesses} attempts left.\n{self.get_hangman()}"
        
        if all(letter in self.guessed_letters for letter in self.word):
            return True, f"Congratulations! You guessed the word: {self.word}"
            
        return False, f"Good guess!\n{self.get_display_word()}\n{self.get_hangman()}"

# Quiz game class
class QuizGame:
    def __init__(self, questions: List[Dict[str, str]]):
        self.questions = questions
        self.current_question = None
        self.score = 0
        self.question_number = 0
        self.total_questions = len(questions)
        self.get_new_question()
    
    def get_new_question(self) -> Optional[Dict[str, str]]:
        """Get a new random question"""
        if not self.questions:
            return None
            
        self.current_question = random.choice(self.questions)
        self.questions.remove(self.current_question)
        self.question_number += 1
        return self.current_question
    
    def check_answer(self, answer: str) -> Tuple[bool, str]:
        """
        Check if the answer is correct
        Returns: (is_correct, message)
        """
        if not self.current_question:
            return False, "No active question. Start a new quiz with !quiz."
            
        correct_answer = self.current_question['answer'].lower()
        is_correct = answer.lower() == correct_answer.lower()
        
        if is_correct:
            self.score += 1
            message = f"✅ Correct! {self.current_question.get('explanation', '')}"
        else:
            message = f"❌ Incorrect! The correct answer was: {correct_answer}"
            
        return is_correct, message

# Rock-Paper-Scissors game class
class RPSGame:
    CHOICES = ["rock", "paper", "scissors"]
    
    @staticmethod
    def get_winner(player_choice: str, bot_choice: str) -> str:
        """Determine the winner of a Rock-Paper-Scissors game"""
        player_choice = player_choice.lower()
        bot_choice = bot_choice.lower()
        
        if player_choice == bot_choice:
            return "tie"
            
        if (player_choice == "rock" and bot_choice == "scissors") or \
           (player_choice == "paper" and bot_choice == "rock") or \
           (player_choice == "scissors" and bot_choice == "paper"):
            return "player"
            
        return "bot"
    
    @staticmethod
    def get_random_choice() -> str:
        """Get a random choice for the bot"""
        return random.choice(RPSGame.CHOICES)

class TicTacToeGame:
    def __init__(self, player1: discord.Member, player2: discord.Member):
        self.board = [" " for _ in range(9)]
        self.players = [player1, player2]
        self.current_player = 0
        self.symbols = ["❌", "⭕"]
        self.winner = None
        self.game_over = False
    
    def make_move(self, position: int) -> bool:
        """Make a move on the board. Returns True if move was valid, False otherwise."""
        if position < 0 or position >= 9 or self.board[position] != " " or self.game_over:
            return False
            
        self.board[position] = self.symbols[self.current_player]
        
        # Check for win or draw
        if self.check_winner():
            self.winner = self.players[self.current_player]
            self.game_over = True
        elif " " not in self.board:
            self.game_over = True
        else:
            self.current_player = 1 - self.current_player
            
        return True
    
    def make_ai_move(self) -> bool:
        """Make an AI move. Returns True if move was made, False if game is over."""
        if self.game_over:
            return False
            
        # Get AI's symbol and opponent's symbol
        ai_symbol = self.symbols[self.current_player]
        opponent_symbol = self.symbols[1 - self.current_player]
        
        # 1. Check if AI can win in the next move
        winning_move = self.get_winning_move(ai_symbol)
        if winning_move is not None:
            return self.make_move(winning_move)
        
        # 2. Check if opponent can win in the next move and block them
        blocking_move = self.get_winning_move(opponent_symbol)
        if blocking_move is not None:
            return self.make_move(blocking_move)
        
        # 3. Try to take the center if it's available
        if self.board[4] == " ":
            return self.make_move(4)
        
        # 4. Try to take a corner
        corners = [0, 2, 6, 8]
        available_corners = [c for c in corners if self.board[c] == " "]
        if available_corners:
            return self.make_move(random.choice(available_corners))
        
        # 5. Take any available side
        sides = [1, 3, 5, 7]
        available_sides = [s for s in sides if self.board[s] == " "]
        if available_sides:
            return self.make_move(random.choice(available_sides))
            
        return False
    
    def check_winner(self) -> bool:
        """Check if current player has won."""
        symbol = self.symbols[self.current_player]
        # Check rows, columns and diagonals
        win_conditions = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
            [0, 4, 8], [2, 4, 6]              # Diagonals
        ]
        return any(all(self.board[i] == symbol for i in condition) for condition in win_conditions)
    
    def get_available_moves(self) -> list[int]:
        """Return list of available move indices."""
        return [i for i, spot in enumerate(self.board) if spot == " "]
    
    def get_winning_move(self, symbol: str) -> int:
        """Return a winning move for the given symbol if available, else None."""
        for move in self.get_available_moves():
            # Try the move
            self.board[move] = symbol
            # Check if it's a winning move
            win_conditions = [
                [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
                [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
                [0, 4, 8], [2, 4, 6]              # Diagonals
            ]
            for condition in win_conditions:
                if all(self.board[i] == symbol for i in condition):
                    # Undo the move
                    self.board[move] = " "
                    return move
            # Undo the move
            self.board[move] = " "
        return None
    
    def get_board_display(self) -> str:
        """Return a string representation of the board."""
        board = ""
        for i in range(0, 9, 3):
            board += " | ".join(self.board[i:i+3]) + "\n"
            if i < 6:
                board += "---------"
            board += "\n"
        return board

# Sample quiz questions with multiple choice options
QUIZ_QUESTIONS = [
    {
        "question": "What is the capital of France?",
        "answer": "Paris",
        "options": ["London", "Berlin", "Madrid", "Paris"],
        "explanation": "Paris is known as the 'City of Light' and is famous for the Eiffel Tower."
    },
    {
        "question": "Which planet is known as the Red Planet?",
        "answer": "Mars",
        "options": ["Venus", "Mars", "Jupiter", "Saturn"],
        "explanation": "Mars appears reddish due to iron oxide (rust) on its surface."
    },
    {
        "question": "What is the largest mammal in the world?",
        "answer": "Blue Whale",
        "options": ["African Elephant", "Blue Whale", "Giraffe", "Polar Bear"],
        "explanation": "Blue Whales can grow up to 100 feet long and weigh as much as 200 tons!"
    },
    {
        "question": "Who painted the Mona Lisa?",
        "answer": "Leonardo da Vinci",
        "options": ["Pablo Picasso", "Vincent van Gogh", "Leonardo da Vinci", "Michelangelo"],
        "explanation": "Painted between 1503 and 1519, it's one of the most famous paintings in the world."
    },
    {
        "question": "What is the chemical symbol for gold?",
        "answer": "Au",
        "options": ["Ag", "Fe", "Au", "Cu"],
        "explanation": "The symbol Au comes from the Latin word for gold, 'aurum'."
    }
]

# Sample hangman words
HANGMAN_WORDS = [
    "PYTHON", "JAVASCRIPT", "PROGRAMMING", "DEVELOPER", "COMPUTER",
    "KEYBOARD", "MONITOR", "INTERNET", "ALGORITHM", "FUNCTION"
]
>>>>>>> 71be574313c6a352c72e5658a8bffc248098cdcc
