import os
import random
import datetime
import discord
import aiohttp
import cohere
import asyncio
import html
import json
import threading
from fastapi import FastAPI
import uvicorn
from discord.ui import Button, View
from discord.ext import commands
from dotenv import load_dotenv
from jokes import JOKES
from typing import Dict, List, Optional
from games import HangmanGame, QuizGame, RPSGame, TicTacToeGame, QUIZ_QUESTIONS, HANGMAN_WORDS

# Load environment variables
load_dotenv()

# Configure Discord intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

# Initialize conversation history storage
conversation_history: Dict[int, List[dict]] = {}

# AFK status storage
afk_users = {}

# Maximum number of messages to keep in history
MAX_HISTORY = 10

def get_history(ctx) -> List[dict]:
    """Get or initialize conversation history for a channel"""
    if ctx.channel.id not in conversation_history:
        conversation_history[ctx.channel.id] = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]
    return conversation_history[ctx.channel.id]

# Initialize bot
bot = commands.Bot(command_prefix='!', intents=intents)

# Enhanced responses with more context
RESPONSES = {
    'hello': [
        'Hi there! I\'m your personal bot. How can I assist you today?',
        'Hello! Ready to help with tasks, reminders, or just chat!',
        'Hey! What can I do for you today?'],
    'how are you': [
        'I\'m running smoothly and ready to help!',
        'All systems operational! How can I assist you today?',
        'Doing great! What can I help you with?'],
    'help': [
        'I can help with: \n• Trivia questions (!trivia [category])\n• Setting reminders (!remindme) \n• Answering questions \n• Basic calculations \n• And more! Try asking!',
        'Need help? Try these commands: !trivia, !remindme, !joke, !quote, !helpme'],
    'bye': [
        'Goodbye! Come back anytime!',
        'See you later! Don\'t hesitate to return if you need anything!',
        'Farewell! Have a great day!'],
    'thanks': [
        'You\'re welcome! 😊',
        'Happy to help!',
        'Anytime!'],
    'joke': JOKES,
    'quote': [
        "The only way to do great work is to love what you do.",
        "In the middle of every difficulty lies opportunity.",
        "The future belongs to those who believe in the beauty of their dreams.",
        "Success is not final, failure is not fatal: It is the courage to continue that counts.",
        "Your time is limited, don't waste it living someone else's life."],
    'weather': [
        'I can\'t check real-time weather, but I recommend checking a weather app!',
        'I don\'t have access to weather data, but I can tell you it\'s a great day to be productive!'],
    'remind': [
        'To set a reminder, type: !remindme [time] [message]\nExample: !remindme 1h Take a break!',
        'I can remind you! Try: !remindme 30m Check the oven'],
    'default': [
        'I\'m not sure I understand. Try asking for !helpme',
        'Hmm, I\'m still learning. Could you rephrase that?',
        'I might not have that feature yet, but I\'m happy to help with other things!'],
    'encourage': [
        "You're stronger than you think. Keep pushing forward! 💪",
        "Every expert was once a beginner. You'll get there! 🚀",
        "The only way to fail is to stop trying. Keep going! 🌟",
        "You've got this! I believe in you! 💪",
        "One step at a time. You're making progress! 👏"]
}

# List of phrases that indicate someone is feeling down
down_phrases = [
    "i'm sad", "i'm feeling down", "i'm depressed", "i'm feeling low",
    "i can't do this", "i want to give up", "i'm not good enough",
    "i'm a failure", "nobody likes me", "i'm alone", "i feel alone",
    "i'm so tired", "i can't go on", "i hate my life", "i'm useless",
    "i'm worthless", "i want to disappear", "i'm a burden", "i feel hopeless",
    "i'm so stressed", "i can't handle this", "i'm overwhelmed", "i'm so anxious",
    "i'm having a bad day", "i'm so upset", "i'm so frustrated", "i'm so angry",
    "i'm so disappointed", "i'm so heartbroken", "i'm so lonely", "i'm so lost",
    "i don't know what to do", "i need help", "i need someone to talk to",
    "i feel like a failure", "i'm so disappointed in myself", "i let everyone down"]

@bot.event
async def on_ready():
    """Event that runs when the bot is ready"""
    print(f'🤖 Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="your commands | !helpme"
        )
    )

@bot.command(name='hello')
async def hello(ctx):
    """Greet the bot"""
    await ctx.send(random.choice(RESPONSES['hello']))

@bot.command(name='joke')
async def tell_joke(ctx):
    """Tell a random joke"""
    try:
        async with aiohttp.ClientSession() as session:
            # Try to get a joke from the API first
            async with session.get('https://v2.jokeapi.dev/joke/Any?type=single') as response:
                if response.status == 200:
                    joke_data = await response.json()
                    if 'joke' in joke_data:
                        await ctx.send(joke_data['joke'])
                    elif 'setup' in joke_data and 'delivery' in joke_data:
                        await ctx.send(f"{joke_data['setup']}\n\n{joke_data['delivery']}")
                    else:
                        # Fallback to local jokes if API response is unexpected
                        await ctx.send(random.choice(JOKES))
                else:
                    # Fallback to local jokes if API is down
                    await ctx.send(random.choice(JOKES))
    except Exception as e:
        # Fallback to local jokes if there's an error
        print(f"Error fetching joke: {e}")
        await ctx.send(random.choice(JOKES))

@bot.command(name='quote')
async def get_quote(ctx):
    """Get a random inspirational quote"""
    await ctx.send(random.choice(RESPONSES['quote']))

@bot.command(name='time')
async def get_time(ctx):
    """Get the current time"""
    now = datetime.datetime.now()
    await ctx.send(f"⏰ The current time is: {now.strftime('%I:%M %p')}")

@bot.command(name='remindme')
async def set_reminder(ctx, time, *, message):
    """Set a reminder"""
    await ctx.send(f"⏰ I'll remind you to \"{message}\" in {time}")

@bot.command(name='dontgiveup')
async def encourage(ctx):
    """Get encouragement when you're feeling down"""
    await ctx.send(random.choice(RESPONSES['encourage']))

@bot.command(name='afk')
async def set_afk(ctx, *, reason: str = "AFK"):
    """Set yourself as AFK with an optional reason"""
    user_id = ctx.author.id
    afk_users[user_id] = {
        'reason': reason,
        'time': datetime.datetime.now(),
        'original_nick': ctx.author.display_name
    }
    # Try to update nickname if possible
    try:
        if ctx.guild:
            await ctx.author.edit(nick=f"[AFK] {ctx.author.display_name[:26]}")
    except:
        pass  # No permission to change nickname
    await ctx.send(f"{ctx.author.mention} is now AFK: {reason} 🚶‍♂️")

@bot.command(name='clear')
async def clear_history(ctx):
    """Clear the conversation history for this channel"""
    if ctx.channel.id in conversation_history:
        # Keep only the system message
        conversation_history[ctx.channel.id] = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]
        await ctx.send("Conversation history cleared! 🧹")
    else:
        await ctx.send("No conversation history to clear.")

@bot.command(name='helpme', aliases=['cmds', 'commands'])
async def help_command(ctx):
    """Show all available commands organized by categories"""
    try:
        # Main categories
        categories = {
            "🎲 **Trivia & Games**": [
                "`!trivia [category]` - Get a random trivia question",
                "`!rps <rock/paper/scissors>` - Play Rock, Paper, Scissors",
                "`!hangman` - Start a new Hangman game",
                "`!quiz` - Take a quiz on various topics (type answers or letters)",
                "`!tictactoe @user` - Play Tic Tac Toe with a friend",
                "`!move 1-9` - Make a move in Tic Tac Toe"
            ],
            "💬 **Chat & AI**": [
                "Mention me or reply to my messages to chat!",
                "`!clear` - Clear conversation history",
                "`!ask [question]` - Ask me anything"
            ],
            "🛠️ **Utility**": [
                "`!afk [reason]` - Set AFK status",
                "`!time` - Show current time",
                "`!remindme [time] [message]` - Set a reminder"
            ],
            "😄 **Fun**": [
                "`!joke` - Get a random joke",
                "`!quote` - Get an inspirational quote",
                "`!fact` - Get a random interesting fact"
            ],
            "ℹ️ **Info**": [
                "`!helpme`, `!cmds`, or `!commands` - Show this help message"
            ]
        }
        # Build the help message
        help_text = ["🤖 **Bot Commands**\n*Type a command for more info*"]
        # Add each category with its commands
        for category, commands in categories.items():
            help_text.append(f"\n\n{category}")
            help_text.extend([f"\n{cmd}" for cmd in commands])
        # Add footer
        help_text.append("\n\n💡 *Need help? Type `!helpme [command]` for more info*")
        # Ensure the message isn't too long
        full_message = "".join(help_text)
        if len(full_message) > 2000:
            full_message = full_message[:1996] + "..."
        # Send the message
        await ctx.send(full_message)
    except Exception as e:
        print(f"Error in help command: {e}")
        await ctx.send("❌ An error occurred while displaying help. Please try again later.")

# Store active trivia questions
bot.trivia_questions = {}
bot.active_games = {}  # Store active games by channel ID

@bot.command(name='trivia')
async def trivia(ctx, category: str = None):
    """Get a random trivia question with interactive buttons!"""
    categories = {
        'general': 9, 'books': 10, 'films': 11, 'music': 12, 'theatre': 13,
        'tv': 14, 'games': 15, 'boardgames': 16, 'science': 17, 'computers': 18,
        'math': 19, 'mythology': 20, 'sports': 21, 'geography': 22, 'history': 23,
        'politics': 24, 'art': 25, 'celebrities': 26, 'animals': 27, 'vehicles': 28,
        'comics': 29, 'gadgets': 30, 'anime': 31, 'cartoons': 32
    }
    # Get category ID or use general knowledge
    category_id = categories.get(category.lower(), 9) if category and category.lower() in categories else 9
    category_name = next((k for k, v in categories.items() if v == category_id), 'general')
    try:
        # Fetch a question from the Open Trivia Database
        url = f"https://opentdb.com/api.php?amount=1&category={category_id}&type=multiple"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['response_code'] == 0 and data['results']:
                        question_data = data['results'][0]
                        question = html.unescape(question_data['question'])
                        correct_answer = html.unescape(question_data['correct_answer'])
                        incorrect_answers = [html.unescape(ans) for ans in question_data['incorrect_answers']]
                        # Combine and shuffle answers
                        answers = incorrect_answers + [correct_answer]
                        random.shuffle(answers)
                        # Get difficulty emoji
                        difficulty_emoji = {
                            'easy': '🟢',
                            'medium': '🟡',
                            'hard': '🔴'
                        }.get(question_data['difficulty'], '❓')
                        # Create the view with buttons
                        class TriviaView(discord.ui.View):
                            def __init__(self, correct_answer, answers, question_text, category_name, difficulty):
                                super().__init__(timeout=60)  # 60 seconds timeout
                                self.correct_answer = correct_answer
                                self.answers = answers
                                self.question_text = question_text
                                self.category_name = category_name
                                self.difficulty = difficulty
                                self.answered = False
                                # Create a button for each answer
                                for i, answer in enumerate(answers, 1):
                                    button = discord.ui.Button(
                                        label=answer[:80],  # Limit button label length
                                        style=discord.ButtonStyle.primary,
                                        custom_id=str(i)
                                    )
                                    button.callback = self.button_callback
                                    self.add_item(button)
                            async def on_timeout(self):
                                if not self.answered:
                                    for item in self.children:
                                        item.disabled = True
                                    await self.message.edit(
                                        content=f"⏰ Time's up! The correct answer was: **{self.correct_answer}**",
                                        view=self
                                    )
                            async def button_callback(self, interaction: discord.Interaction):
                                if self.answered:
                                    return await interaction.response.send_message(
                                        "This question has already been answered!",
                                        ephemeral=True
                                    )
                                self.answered = True
                                selected = int(interaction.data['custom_id']) - 1
                                if self.answers[selected] == self.correct_answer:
                                    # Correct answer
                                    for item in self.children:
                                        if int(item.custom_id) == selected + 1:
                                            item.style = discord.ButtonStyle.success
                                            item.disabled = True
                                    await interaction.response.edit_message(
                                        content=f"🎉 **Correct!** The answer was: **{self.correct_answer}**",
                                        view=self
                                    )
                                else:
                                    # Wrong answer
                                    for item in self.children:
                                        if int(item.custom_id) == selected + 1:
                                            item.style = discord.ButtonStyle.danger
                                            item.disabled = True
                                    await interaction.response.edit_message(
                                        content=f"😐 **Incorrect!** The correct answer was: **{self.correct_answer}**",
                                        view=self
                                    )
                        # Send the question with buttons
                        view = TriviaView(correct_answer, answers, question, category_name, difficulty_emoji)
                        await ctx.send(f"**{category_name}** - {difficulty_emoji}\n{question}", view=view)
    except Exception as e:
        print(f"Error fetching trivia question: {e}")
        await ctx.send("❌ An error occurred while fetching the trivia question. Please try again later.")

class RPSView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)
        self.choice = None

    @discord.ui.button(label='🪨 Rock', style=discord.ButtonStyle.primary)
    async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_choice(interaction, "rock")

    @discord.ui.button(label='📄 Paper', style=discord.ButtonStyle.primary)
    async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_choice(interaction, "paper")

    @discord.ui.button(label='✂️ Scissors', style=discord.ButtonStyle.primary)
    async def scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_choice(interaction, "scissors")

    async def handle_choice(self, interaction: discord.Interaction, choice: str):
        self.choice = choice
        bot_choice = RPSGame.get_random_choice()
        result = RPSGame.get_winner(choice, bot_choice)

        if result == "tie":
            message = f"🤝 It's a tie! We both chose {bot_choice}."
        elif result == "player":
            message = f"🎉 You win! {choice.capitalize()} beats {bot_choice}."
        else:
            message = f"😢 You lose! {bot_choice.capitalize()} beats {choice}."

        await interaction.response.edit_message(
            content=f"You chose: {choice.capitalize()}\n{message}",
            view=None
        )
        self.stop()

    async def on_timeout(self):
        # Disable all buttons when view times out
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)

@bot.command(name='rps')
async def rock_paper_scissors(ctx):
    """Play Rock-Paper-Scissors with the bot"""
    view = RPSView()
    view.message = await ctx.send("Choose your move:", view=view)

@bot.command()
async def hangman(ctx):
    """Start a game of Hangman"""
    channel_id = ctx.channel.id
    if channel_id in bot.active_games and isinstance(bot.active_games[channel_id], HangmanGame):
        await ctx.send("There's already an active Hangman game in this channel!")
        return
    
    word = random.choice(HANGMAN_WORDS)
    game = HangmanGame(word)
    bot.active_games[channel_id] = game
    
    view = HangmanView(game, channel_id)  
    await ctx.send(
        f"🎮 **New Hangman Game!** 🎮\n"
        f"Guess the word: {game.get_display_word()}\n"
        f"You have {game.max_attempts} attempts.\n"
        f"{game.get_hangman()}\n\n"
        "Type a letter to guess!",
        view=view
    )
    
class HangmanView(discord.ui.View):
    def __init__(self, game, channel_id):
        super().__init__(timeout=300)
        self.game = game
        self.channel_id = channel_id
        self.letters = [chr(i) for i in range(65, 91)]  # A-Z
        self.available_letters = [l for l in self.letters if l not in game.guessed_letters]
        
        # Add text input for letter guessing
        self.guess_input = discord.ui.TextInput(
            label='Type a letter to guess:',
            placeholder='Enter a single letter (A-Z)',
            min_length=1,
            max_length=1,
            style=discord.TextStyle.short
        )
        
        # Add submit button
        self.submit_button = discord.ui.Button(
            label='✅ Submit Guess',
            style=discord.ButtonStyle.primary
        )
        self.submit_button.callback = self.submit_guess
        self.add_item(self.submit_button)
        
        # Add stop button
        self.stop_button = discord.ui.Button(
            label='⏹️ Stop Game',
            style=discord.ButtonStyle.danger
        )
        self.stop_button.callback = self.stop_game
        self.add_item(self.stop_button)
    
    async def submit_guess(self, interaction: discord.Interaction):
        # Show a modal for text input
        modal = discord.ui.Modal(title="Guess a Letter")
        modal.add_item(self.guess_input)
        
        async def on_submit(interaction: discord.Interaction):
            guess = self.guess_input.value.upper()
            if not guess.isalpha() or len(guess) != 1:
                await interaction.response.send_message("Please enter a single letter (A-Z)", ephemeral=True)
                return
                
            if guess in self.game.guessed_letters:
                await interaction.response.send_message(f"You've already guessed '{guess}'!", ephemeral=True)
                return
                
            await self.process_letter(interaction, guess)
            
        modal.on_submit = on_submit
        await interaction.response.send_modal(modal)
    
    def get_letter_display(self):
        """Create a visual representation of used and available letters"""
        used = []
        available = []
        
        for letter in self.letters:
            if letter in self.game.guessed_letters:
                used.append(f"~~{letter}~~")
            else:
                available.append(letter)
                
        return "\n" + " ".join(used) + "\n" + " ".join(available)
    
    async def process_letter(self, interaction: discord.Interaction, letter):
        game_over, message = self.game.guess_letter(letter)
        
        if game_over:
            if self.channel_id in bot.active_games:
                del bot.active_games[self.channel_id]
            await interaction.response.edit_message(
                content=f"{message}\n\nGame Over!" + self.get_letter_display(),
                view=None
            )
        else:
            # Update available letters
            self.available_letters = [l for l in self.letters if l not in self.game.guessed_letters]
            
            # Update the message with the new game state
            content = (
                f"🎮 **Hangman Game** 🎮\n"
                f"Guess the word: {self.game.get_display_word()}\n"
                f"Incorrect guesses: {self.game.incorrect_guesses}/{self.game.max_attempts}\n"
                f"{self.game.get_hangman()}\n\n"
                f"Guessed letters: {', '.join(sorted(self.game.guessed_letters)) if self.game.guessed_letters else 'None'}"
            )
            
            if interaction.response.is_done():
                await interaction.followup.edit_message(
                    message_id=interaction.message.id,
                    content=content,
                    view=self
                )
            else:
                await interaction.response.edit_message(
                    content=content,
                    view=self
                )
    
    async def stop_game(self, interaction: discord.Interaction):
        """Handle the stop game button press"""
        # Remove the game from active games
        if self.channel_id in bot.active_games:
            del bot.active_games[self.channel_id]
        
        # Disable all components
        for item in self.children:
            item.disabled = True
        
        # Update the message to show the game was stopped
        await interaction.response.edit_message(
            content="⏹️ Game stopped by user.",
            view=self
        )
        self.stop()  # Stop the view

@bot.command(name='guess_letter')
async def guess_letter(ctx, letter: str):
    """This command is no longer used. Please use the buttons in the Hangman game interface to guess letters."""
    await ctx.send("Please use the buttons in the Hangman game interface to guess letters.")
    # Try to resend the current game state if it exists
    channel_id = ctx.channel.id
    if channel_id in bot.active_games and isinstance(bot.active_games[channel_id], HangmanGame):
        game = bot.active_games[channel_id]
        await ctx.send(
            f"Current game state:\n"
            f"Word: {game.get_display_word()}\n"
            f"Incorrect guesses: {game.incorrect_guesses}/{game.max_attempts}\n"
            f"{game.get_hangman()}"
        )

@bot.command(name='quiz')
async def start_quiz(ctx):
    """Start a new quiz game"""
    channel_id = ctx.channel.id
    if channel_id in bot.active_games and isinstance(bot.active_games[channel_id], QuizGame):
        await ctx.send("There's already an active quiz in this channel!")
        return
    
    # Create a copy of the questions to avoid modifying the original list
    questions = QUIZ_QUESTIONS.copy()
    game = QuizGame(questions)
    bot.active_games[channel_id] = game
    
    await ask_quiz_question(ctx, game)

async def ask_quiz_question(ctx, game):
    """Ask the current quiz question with multiple choice options"""
    question = game.get_new_question()
    
    if not question:
        await ctx.send("No more questions! Thanks for playing!")
        return
    
    # Get options and shuffle them if they exist, otherwise use just the answer
    options = question.get('options', [question['answer']])
    
    # If options don't include the answer, add it
    if question['answer'] not in options:
        options.append(question['answer'])
    
    # Shuffle the options
    random.shuffle(options)
    
    # Create the options text with letters (A, B, C, D)
    options_text = []
    for i, option in enumerate(options, 1):
        letter = chr(64 + i)  # 65 is 'A' in ASCII
        options_text.append(f"{letter}. {option}")
    
    # Send the question with options
    await ctx.send(
        f"❓ **Question {game.question_number} of {game.total_questions}**\n"
        f"{question['question']}\n\n"
        f"**Options:**\n" + "\n".join(options_text) + "\n\n"
        "**How to answer:**\n"
        "• Type just the letter (A, B, C, or D) **OR**\n"
        "• Type the full text of your answer\n\n"
        "Example: `A` or `Python` are both valid answers!"
    )

@bot.command(name='answer')
async def answer_question(ctx, *, user_answer: str):
    """Answer the current quiz question"""
    channel_id = ctx.channel.id
    
    # Check if there's an active quiz or if this is a direct answer to a quiz question
    if channel_id not in bot.active_games or not isinstance(bot.active_games[channel_id], QuizGame):
        # If the message is just a letter (A, B, C, D) and there's an active quiz, treat it as an answer
        if user_answer.upper() in ['A', 'B', 'C', 'D'] and channel_id in bot.active_games and \
           isinstance(bot.active_games[channel_id], QuizGame):
            game = bot.active_games[channel_id]
            is_correct, message = game.check_answer(user_answer)
            await ctx.send(message)
            
            # Ask next question or end game
            if len(game.questions) > 0:
                await asyncio.sleep(2)  # Short delay before next question
                await ask_quiz_question(ctx, game)
                await ctx.send("Type your answer or the letter of your choice (A, B, C, or D)!")
            else:
                await ctx.send(f"🎉 Quiz complete! Your score: {game.score}/{game.total_questions}")
                if channel_id in bot.active_games:
                    del bot.active_games[channel_id]
        else:
            await ctx.send("No active quiz! Start one with `!quiz`")
        return
    
    # Handle regular answer command
    game = bot.active_games[channel_id]
    is_correct, message = game.check_answer(user_answer)
    
    await ctx.send(message)
    
    # Ask next question or end game
    if len(game.questions) > 0:
        await asyncio.sleep(2)  # Short delay before next question
        await ask_quiz_question(ctx, game)
        await ctx.send("Type your answer or the letter of your choice (A, B, C, or D)!")
    else:
        await ctx.send(f"🎉 Quiz complete! Your score: {game.score}/{game.total_questions}")
        if channel_id in bot.active_games:
            del bot.active_games[channel_id]

@bot.command(name='stop')
async def stop_game(ctx):
    """Stop the current game in this channel"""
    channel_id = ctx.channel.id
    
    if channel_id not in bot.active_games:
        await ctx.send("There's no active game to stop in this channel!")
        return
    
    # Get the game and clean up
    game = bot.active_games[channel_id]
    del bot.active_games[channel_id]
    
    # Send appropriate message based on game type
    if isinstance(game, HangmanGame):
        await ctx.send(f"⏹️ Hangman game stopped. The word was: **{game.word}**")
    elif isinstance(game, QuizGame):
        await ctx.send(f"⏹️ Quiz stopped. Your final score was: {game.score}/{game.question_number-1}")
    elif isinstance(game, TicTacToeGame):
        await ctx.send("⏹️ Tic Tac Toe game stopped.")
    else:
        await ctx.send("⏹️ Game stopped.")

class TicTacToeView(discord.ui.View):
    def __init__(self, game, channel_id):
        super().__init__(timeout=300)  # 5 minute timeout
        self.game = game
        self.channel_id = channel_id
        self.move_input = discord.ui.TextInput(
            label='Enter your move (1-9)',
            placeholder='Type a number from 1 to 9',
            min_length=1,
            max_length=1,
            style=discord.TextStyle.short
        )
        
        # Add submit button
        self.submit_button = discord.ui.Button(
            label='🎮 Make Move',
            style=discord.ButtonStyle.primary
        )
        self.submit_button.callback = self.submit_move
        self.add_item(self.submit_button)
        
        # Add stop button
        self.stop_button = discord.ui.Button(
            label='⏹️ Stop Game',
            style=discord.ButtonStyle.danger
        )
        self.stop_button.callback = self.stop_game
        self.add_item(self.stop_button)
    
    async def submit_move(self, interaction: discord.Interaction):
        # Show a modal for move input
        modal = discord.ui.Modal(title="Make Your Move")
        modal.add_item(self.move_input)
        
        async def on_submit(interaction: discord.Interaction):
            try:
                position = int(self.move_input.value)
                if position < 1 or position > 9:
                    await interaction.response.send_message("Please enter a number between 1 and 9!", ephemeral=True)
                    return
                    
                # Adjust position from 1-9 to 0-8
                pos = position - 1
                
                # Make the move
                if not self.game.make_move(pos):
                    await interaction.response.send_message("Invalid move! Please choose a number that hasn't been taken.", ephemeral=True)
                    return
                
                # Get the updated board
                board = self.game.get_board_display()
                
                # Check game state
                if self.game.game_over:
                    if self.game.winner:
                        await interaction.response.edit_message(
                            content=(
                                f"🎮 **Tic Tac Toe** 🎮\n"
                                f"{self.game.players[0].mention} (❌) vs {self.game.players[1].mention} (⭕)\n\n"
                                f"🎉 **{self.game.winner.mention} wins!** 🎉\n\n"
                                f"{board}"
                            ),
                            view=None
                        )
                    else:
                        await interaction.response.edit_message(
                            content=(
                                f"🎮 **Tic Tac Toe** 🎮\n"
                                f"{self.game.players[0].mention} (❌) vs {self.game.players[1].mention} (⭕)\n\n"
                                f"🤝 **It's a draw!** 🤝\n\n"
                                f"{board}"
                            ),
                            view=None
                        )
                    if self.channel_id in bot.active_games:
                        del bot.active_games[self.channel_id]
                else:
                    # Update the message for the next player
                    await interaction.response.edit_message(
                        content=(
                            f"🎮 **Tic Tac Toe** 🎮\n"
                            f"{self.game.players[0].mention} (❌) vs {self.game.players[1].mention} (⭕)\n"
                            f"It's {self.game.players[self.game.current_player].mention}'s turn ({self.game.symbols[self.game.current_player]})\n\n"
                            f"{board}"
                        )
                    )
            except ValueError:
                await interaction.response.send_message("Please enter a valid number!", ephemeral=True)
        
        modal.on_submit = on_submit
        await interaction.response.send_modal(modal)
    
    async def stop_game(self, interaction: discord.Interaction):
        # Remove the game from active games
        if self.channel_id in bot.active_games:
            del bot.active_games[self.channel_id]
        
        # Disable all components
        for item in self.children:
            if hasattr(item, 'disabled'):
                item.disabled = True
        
        # Update the message to show the game was stopped
        await interaction.response.edit_message(
            content="⏹️ Tic Tac Toe game stopped by user.",
            view=self
        )
        self.stop()  # Stop the view

@bot.command(name='tictactoe', aliases=['ttt'])
async def tictactoe(ctx, opponent: discord.Member = None):
    """Start a Tic Tac Toe game with another user"""
    if opponent is None:
        await ctx.send("Please mention a user to play against! Example: `!tictactoe @username`")
        return
        
    if opponent == ctx.author:
        await ctx.send("You can't play against yourself!")
        return
        
    if opponent.bot:
        await ctx.send("You can't play against a bot!")
        return
        
    channel_id = ctx.channel.id
    
    # Check if there's already a game in this channel
    if channel_id in bot.active_games:
        await ctx.send("There's already an active game in this channel! Use `!stop` to end it first.")
        return
    
    # Create and store the game
    game = TicTacToeGame(ctx.author, opponent)
    bot.active_games[channel_id] = game
    
    # Create the view with buttons
    view = TicTacToeView(game, channel_id)
    
    # Send initial game board
    board = game.get_board_display()
    message = await ctx.send(
        f"🎮 **Tic Tac Toe** 🎮\n"
        f"{ctx.author.mention} (❌) vs {opponent.mention} (⭕)\n"
        f"It's {ctx.author.mention}'s turn! (❌)\n\n"
        f"**How to play:**\n"
        f"Click the 'Make Move' button and enter a number (1-9).\n"
        f"Positions are numbered from left to right, top to bottom.\n\n"
        f"{board}",
        view=view
    )
    view.message = message

@bot.command(name='listgames')
async def list_games(ctx):
    """List all available games"""
    embed = discord.Embed(
        title="🎮 Available Games",
        description="Here are the games you can play:",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="🎮 Game Controls",
        value=(
            "`!tictactoe @user` - Play Tic Tac Toe with another user\n"
            "`!hangman` - Play Hangman\n"
            "`!quiz` - Start a quiz\n"
            "`!answer <your answer>` - Answer the current quiz question\n"
            "`!stop` - Stop the current game in this channel"
        ),
        inline=False
    )
    embed.add_field(
        name="🤖 AI Chat",
        value=(
            "`!ask <question>` - Ask the AI a question\n"
            "`!joke` - Get a joke\n"
            "`!quote` - Get a quote\n"
            "`!weather <location>` - Get the weather for a location\n"
            "`!remind <reminder>` - Set a reminder"
        ),
        inline=False
    )
    embed.add_field(
        name="🎯 Hangman",
        value="`!hangman` - Start a new Hangman game with a virtual keyboard",
        inline=False
    )
    embed.add_field(
        name="🧠 Quiz",
        value="`!quiz` - Start a new quiz\n"
              "`!answer <your answer>` - Answer the current quiz question",
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.command(name='ask')
async def ask_ai(ctx, *, question):
    """Ask the AI a question with conversation history"""
    try:
        async with ctx.typing():
            # Get or initialize conversation history for this channel
            history = get_history(ctx)
            
            # Add user's question to history
            history.append({"role": "user", "content": question})
            
            # Keep only the most recent messages (plus system message)
            if len(history) > MAX_HISTORY + 1:  # +1 for system message
                history = [history[0]] + history[-(MAX_HISTORY):-1] + [history[-1]]
            
            # Initialize the client with your API key
            co = cohere.ClientV2(api_key=os.getenv('COHERE_API_KEY'))
            
            # Make the API call with conversation history
            response = co.chat(
                model="command-a-03-2025",
                messages=history,
                temperature=0.4,
                max_tokens=500  # Limit response length
            )
            
            # Extract the text from the response
            try:
                # Access the text content from the response
                # The response structure is different in the Cohere API
                if hasattr(response, 'message') and hasattr(response.message, 'content'):
                    if isinstance(response.message.content, list) and len(response.message.content) > 0:
                        answer = response.message.content[0].text
                    else:
                        answer = str(response.message.content)
                else:
                    answer = str(response)
            except Exception as e:
                print(f"Error extracting response: {e}")
                answer = str(response)  # Fallback to string representation
            
            # If answer is still None or empty, use the full response
            if not answer:
                answer = str(response)
            
            # Add AI's response to history
            history.append({"role": "assistant", "content": answer})
            # Update the conversation history
            conversation_history[ctx.channel.id] = history
            
            # Split the answer into chunks of 2000 characters (Discord's message limit)
            chunk_size = 1900  # Slightly less to account for the emoji and continuation markers
            chunks = [answer[i:i+chunk_size] for i in range(0, len(answer), chunk_size)]
            
            # Send each chunk as a separate message
            for i, chunk in enumerate(chunks):
                try:
                    # Add a header to subsequent chunks
                    if i > 0:
                        chunk = f"(Continued from previous message)\n\n{chunk}"
                    await ctx.send(f"🤖 {chunk}")
                except Exception as e:
                    print(f"Error sending message chunk {i+1}: {e}")
                    continue
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(f"Ask AI Error: {error_msg}")
        await ctx.send("I'm having trouble thinking right now. Could you try again?")
        if 'response' in locals():
            print(f"Response type: {type(response)}")
            print(f"Response content: {response}")

@bot.event
async def on_message(message):
    # Don't respond to ourselves
    if message.author == bot.user:
        return
    
    # Check if user is returning from AFK
    user_id = message.author.id
    if user_id in afk_users:
        afk_data = afk_users.pop(user_id)
        time_afk = datetime.datetime.now() - afk_data['time']
        
        # Try to restore original nickname
        try:
            if message.guild:
                await message.author.edit(nick=afk_data['original_nick'])
        except:
            pass  # No permission to change nickname
        
        # Send welcome back message
        await message.channel.send(
            f"Welcome back {message.author.mention}! "
            f"You were AFK for {str(time_afk).split('.')[0]}. "
            f"(Reason: {afk_data['reason']})"
        )
    
    # Process commands
    await bot.process_commands(message)
    
    # Don't respond to other bots
    if message.author.bot:
        return
    
    # Check if this is an answer to a trivia question
    if message.reference and message.reference.message_id in bot.trivia_questions:
        trivia_data = bot.trivia_questions[message.reference.message_id]
        
        # Check if the question has expired
        if datetime.datetime.now() > trivia_data['expires']:
            del bot.trivia_questions[message.reference.message_id]
            return
        
        try:
            # Try to parse the answer as a number
            answer = int(message.content.strip())
            
            if answer == trivia_data['correct']:
                await message.add_reaction('✅')
                await message.reply(f"🎉 Correct! The answer was: **{trivia_data['answer']}**", mention_author=False)
            else:
                await message.add_reaction('❌')
                await message.reply(
                    f"That's not quite right! The correct answer was: **{trivia_data['answer']}**",
                    mention_author=False
                )
            
            # Remove the question since it's been answered
            if message.reference.message_id in bot.trivia_questions:
                del bot.trivia_questions[message.reference.message_id]
        except ValueError:
            # If it's not a number, ignore it
            pass
        except Exception as e:
            print(f"Error processing trivia answer: {e}")
            return
    
    # Check if someone mentioned an AFK user
    for mention in message.mentions:
        if mention.id in afk_users and mention.id != message.author.id:
            afk_data = afk_users[mention.id]
            afk_time = datetime.datetime.now() - afk_data['time']
            
            await message.reply(
                f"{mention.display_name} is AFK: {afk_data['reason']} "
                f"(for {str(afk_time).split('.')[0]} ago)",
                mention_author=False
            )
    
    # Check if this is a reply to the bot's message
    is_reply_to_bot = (
        message.reference and
        message.reference.message_id and
        message.reference.resolved and
        message.reference.resolved.author == bot.user
    )
    
    # Check if the bot is mentioned, it's a DM, or a reply to the bot
    if bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel) or is_reply_to_bot:
        try:
            # Get the message content without the mention if it exists
            content = message.content.replace(f'<@{bot.user.id}>', '').strip()
            
            # If there's content after the mention or it's a reply
            if content or is_reply_to_bot:
                # Create a context for the message
                ctx = await bot.get_context(message)
                
                # Use the ask_ai function to handle the response with conversation history
                await ask_ai(ctx, question=content or message.content)
            else:
                # If just mentioned without a message, send a greeting
                await message.reply(random.choice(RESPONSES['hello']), mention_author=False)
            return
        except Exception as e:
            print(f"Error handling message: {e}")
            await message.reply("Sorry, I encountered an error processing your message. Please try again!", mention_author=False)
            return
    
    # Check for emotional support phrases in regular messages
    content_lower = message.content.lower()
    if any(phrase in content_lower for phrase in down_phrases):
        await message.reply(random.choice(RESPONSES['encourage']), mention_author=False)

def get_response(message):
    """Get a response based on the message content"""
    # Convert to lowercase for case-insensitive matching
    message_lower = message.lower()
    original_message = message
    
    # Remove any leading/trailing whitespace
    message = message.strip()
    
    # Check for empty message
    if not message:
        return None
    
    # Check for matching phrases in the message
    for phrase in RESPONSES:
        if phrase in message_lower and phrase not in ['joke', 'quote', 'weather', 'remind']:
            return random.choice(RESPONSES[phrase])
    
    # If it's a question
    if '?' in original_message:
        return "That's an interesting question! I'm still learning, but I'm happy to help with what I can."
    
    # Default response if no matches
    return random.choice(RESPONSES['default'])

def run_http_server():
    """Run the FastAPI server in a separate thread"""
    app = FastAPI()
    
    @app.get("/")
    async def health_check():
        return {"status": "ok", "message": "Bot is running"}
    
    port = int(os.getenv('PORT', 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

# Run the bot and HTTP server
if __name__ == "__main__":
    # Get the bot token from environment variables
    TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    if not TOKEN:
        print("Error: DISCORD_BOT_TOKEN environment variable not set!")
        exit(1)

    # Start the HTTP server in a separate thread
    import threading
    server_thread = threading.Thread(target=run_http_server, daemon=True)
    server_thread.start()

    # Start the bot
    print("Starting bot...")
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"Error running bot: {e}")
        exit(1)