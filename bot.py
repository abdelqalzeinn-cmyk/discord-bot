
import os
import random
import datetime
import discord
import aiohttp
import traceback
import cohere
import openai
import asyncio
import html
import json
import threading
import time
import io
import contextlib
import textwrap
import re
import unicodedata
import enum
import signal
import sys
from fastapi import FastAPI
import uvicorn
import re  # Add this line at the top with other imports
# The client will automatically use the GOOGLE_API_KEY environment variable
# Make sure to set GOOGLE_API_KEY in your .env file
from discord.ui import Button, View, Select
from discord.ext import commands
from discord import app_commands
from discord import Message, TextChannel, DMChannel, Intents, Interaction
from typing import Union, List, Dict, Optional
from dotenv import load_dotenv
from jokes import JOKES
from typing import Dict, List, Optional, Union
from games import HangmanGame, QuizGame, RPSGame, TicTacToeGame, QUIZ_QUESTIONS, HANGMAN_WORDS
from datetime import datetime, time, timedelta, UTC
import re
import unicodedata

def is_suspicious(prompt: str) -> bool:
    """Check if a prompt contains suspicious patterns"""
    # Skip empty or very short prompts
    if len(prompt) < 5:
        return False
        
    # Check for excessive special characters (more than 40% of the prompt)
    special_chars = len(re.findall(r'[!@#$%^&*()_+{}\[\]:;<>,.?~\\/-]', prompt))
    if special_chars > len(prompt) * 0.4:
        return True
    
    # Check for excessive numbers (more than 40% of the prompt)
    numbers = len(re.findall(r'\d', prompt))
    if numbers > len(prompt) * 0.4:
        return True
    
    # Check for suspicious patterns (only if they appear multiple times)
    suspicious_patterns = [
        r'[\._-]{4,}',  # 4 or more of . _ or -
        r'\s{4,}',      # 4 or more spaces
    ]
    
    # Only flag if multiple suspicious patterns are found
    suspicious_count = sum(1 for pattern in suspicious_patterns if re.search(pattern, prompt))
    return suspicious_count >= 2

async def log_suspicious_activity(ctx, prompt: str, reason: str):
    """Log suspicious activity to the moderation channel"""
    if 'MODERATION_CHANNEL_ID' in globals() and MODERATION_CHANNEL_ID:
        channel = bot.get_channel(MODERATION_CHANNEL_ID)
        if channel:
            await channel.send(
                f"🚨 Suspicious activity detected:\n"
                f"User: {ctx.author} ({ctx.author.id})\n"
                f"Channel: {getattr(ctx.channel, 'name', 'DM')}\n"
                f"Prompt: `{prompt}`\n"
                f"Reason: {reason}"
            )

# Add this with your other constants
MODERATION_CHANNEL_ID = 1430767506141872228

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
# Allowed channels (add your channel IDs here)
ALLOWED_CHANNELS = {
    # Everyone can use the bot in these channels
    1440330105799839856,  # bot-commands channel ID (replace with your actual channel ID)
}
# Users who can use the bot in any channel (add user IDs here)
# ... (your existing ALLOWED_USERS list)
ALLOWED_USERS = {
    1304359498919444557,
    1329161792936476683,
    982303576128897104,
}# Only these two IDs can use the terminal command
TERMINAL_ADMINS = {
    1304359498919444557, # User 1 (You)
    1329161792936476683  # User 2 (The one you just added)
}
# --- PASTE THE BANNED WORDS HERE ---
# Rate limiting
RATE_LIMIT = 5  # Number of requests
RATE_LIMIT_WINDOW = 60  # Time window in seconds
GENERATION_COUNTER = {}  # {user_id: [timestamp1, timestamp2, ...]}

# Banned words list
BANNED_WORDS = [
    # Nudity and explicit content
    "nsfw", "naked", "nude", "nudity", "nudist", "naturist", "bikini", "lingerie", "underwear", "panties",
    "topless", "bottomless", "cleavage", "upskirt", "downblouse", "explicit", "xxx", "porn", "porno", "pornography",
    "hentai", "ecchi", "r34", "rule34", "lewds", "lewd", "suggestive", "provocative", "seductive", "erotic", "skin",
    
    # Body parts (explicit)
    "breasts", "boobs", "tits", "titties", "nipples", "areola", "areolas", "cleavage", "clevage", "clev",
    "vagina", "pussy", "pussies", "vulva", "labia", "clit", "clitoris", "penis", "dick", "cock", "dildo", "dicks", 
    "cocks", "balls", "testicles", "testes", "scrotum", "ass", "asshole", "arse", "arsehole", "butt", "buttocks",
    "anus", "anal", "butthole", "rectum", "bum", "bums", "booty", "twerking", "thong", "g-string", "gstring",
    
    # Sexual content
    "sex", "sexual", "sexy", "sexuality", "intercourse", "fuck", "fucking", "fucker", "fucked", "fucks",
    "screw", "screwing", "screwed", "screws", "fellate", "fellatio", "blowjob", "blow job", "handjob", "hand job",
    "bj", "hj", "orgasm", "orgasmic", "orgasms", "masturbat", "jerk off", "jerkoff", "jacking off", "wank",
    "wanking", "wanker", "ejaculat", "cum", "semen", "sperm", "creampie", "cream pie", "cowgirl", "doggy style",
    "missionary", "69", "sixty nine", "sixtynine", "kamasutra", "kama sutra", "kinky", "bdsm", "bondage", "domination",
    "submission", "submissive", "dominant", "domme", "dom", "sub", "slave", "master", "mistress", "fetish",
    
    # Violence and gore
    "gore", "gory", "blood", "bloody", "violence", "violent", "brutal", "brutality", "torture", "torturing",
    "mutilat", "decapitat", "behead", "beheading", "dismember", "dismemberment", "cannibal", "cannibalism",
    "snuff", "snuff film", "snuff movie", "guro", "gurokawa", "ryona", "vore", "scat", "scatology", "coprophilia",
    
    # Common misspellings and variations
    "pron", "p0rn", "pr0n", "porn0", "p0rn0", "pr0n0", "porn0graphy", "p0rn0graphy", "pr0n0graphy",
    "secks", "s3x", "s3xy", "sexy", "sexe", "sexi", "sexii", "sexiii", "sexiiii", "sexiiiii",
    "fuk", "fuking", "fukin", "fuker", "fuked", "fukkin", "fukking", "fukn", "fukr", "fukw",
    "d1ck", "d1ckhead", "d1ckwad", "d1ckface", "d1ckhead", "d1ckwad", "d1ckface",
    "testicales", "testicle", "testes", "genital", "breast", "butt", "buttock", "backshots",
    # Common bypass attempts
    "p0rn", "s3x", "s3xy", "a$$", "@$$", "b00b", "b00bs", "v4g1n4",
    # Common misspellings
    "t3st1cl3s", "t3st1cl3", "t3st1c13s", "t3st1c1e5", "t3st1c135",
    "t35t1cl35", "t35t1cl3", "t35t1c13s", "t35t1c1e5", "t35t1c135"
]
# -----------------------------------
def is_allowed_channel():
    # ... (rest of your code)
    async def predicate(ctx):
        # Allow if user is in ALLOWED_USERS
        if ctx.author.id in ALLOWED_USERS:
            return True
        # Allow if in an allowed channel
        if ctx.channel.id in ALLOWED_CHANNELS:
            return True
        # Allow DMs
        if isinstance(ctx.channel, discord.DMChannel):
            return True
        # If we get here, the channel is not allowed
        allowed_mentions = [f'<#{channel_id}>' for channel_id in ALLOWED_CHANNELS]
        await ctx.send(
            f" This command can only be used in these channels: {' '.join(allowed_mentions)}\n"
            "Or contact an admin to be added to the allowed users list."
        )
        return False
    return commands.check(predicate)
# Maximum number of messages to keep in history
MAX_HISTORY = 10
def get_history(ctx) -> List[dict]:
    """Get or initialize conversation history for a channel"""
    if ctx.channel.id not in conversation_history:
        conversation_history[ctx.channel.id] = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]
    return conversation_history[ctx.channel.id]
async def send_long_message(destination: Union[TextChannel, DMChannel], content: str, **kwargs):
    """Helper function to send messages that may exceed Discord's 2000 character limit.
    Args:
        destination: The channel or DM to send the message to
        content: The message content to send
        **kwargs: Additional arguments to pass to send()
    """
    # Discord's message limit is 2000 characters
    max_length = 2000
    # If the message is short enough, send it as is
    if len(content) <= max_length:
        return await destination.send(content, **kwargs)
    # Split the message into chunks of max_length characters
    chunks = []
    # First, try to split by double newlines (paragraphs)
    paragraphs = content.split('\n\n')
    current_chunk = ""
    for paragraph in paragraphs:
        # Clean up the paragraph
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        # If the paragraph is too long, split it by sentences
        if len(paragraph) > max_length - 10:  # Leave room for continuation markers
            # Split by common sentence endings
            import re
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                # Ensure sentence ends with punctuation
                if not re.search(r'[.!?]$', sentence):
                    sentence += '.'
                # If sentence is still too long, split by words
                if len(sentence) > max_length - 10:
                    words = sentence.split(' ')
                    current_sentence = ""
                    for word in words:
                        # If word is too long, split by characters
                        if len(word) > max_length - 10:
                            if current_sentence:
                                chunks.append(current_sentence)
                                current_sentence = ""
                            # Split the long word into chunks
                            for i in range(0, len(word), max_length - 10):
                                chunk = word[i:i + max_length - 10]
                                chunks.append(chunk)
                        else:
                            # Check if adding this word would exceed the limit
                            if current_sentence and len(current_sentence) + len(word) + 1 > max_length - 10:
                                chunks.append(current_sentence)
                                current_sentence = word
                            else:
                                current_sentence = f"{current_sentence} {word}".strip()
                    if current_sentence:
                        chunks.append(current_sentence)
                else:
                    # Add sentence to current chunk if it fits
                    if current_chunk and len(current_chunk) + len(sentence) + 2 <= max_length - 10:
                        current_chunk = f"{current_chunk}\n\n{sentence}" if current_chunk else sentence
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = sentence
        else:
            # Add paragraph to current chunk if it fits
            if current_chunk and len(current_chunk) + len(paragraph) + 2 <= max_length - 10:
                current_chunk = f"{current_chunk}\n\n{paragraph}" if current_chunk else paragraph
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = paragraph
    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk)
    # Send all chunks with continuation markers and rate limiting
    for i, chunk in enumerate(chunks):
        try:
            # Add continuation message if needed
            if i > 0:
                chunk = f"(continued from previous message)\n\n{chunk}"
            # Add ellipsis if this isn't the last chunk
            if i < len(chunks) - 1:
                chunk = chunk.rstrip('.,!?') + '...'
            # Send the chunk with error handling
            try:
                await destination.send(chunk, **kwargs)
                # Add a small delay between messages to avoid rate limiting
                if i < len(chunks) - 1:
                    await asyncio.sleep(1)  # 1 second delay between messages
            except discord.HTTPException as e:
                print(f"Failed to send message chunk: {e}")
                continue  # Skip to next chunk if one fails
        except Exception as e:
            print(f"Error processing message chunk: {e}")
            continue

# Initialize bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Initialize bot with prefix commands and tree for slash commands
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        self.synced = False

    async def setup_hook(self) -> None:
        # Sync commands on startup
        if not self.synced:
            try:
                # Sync global commands
                await self.tree.sync()
                
                # Also sync for the specific guild for faster updates during development
                guild = discord.Object(id=1440330105799839856)  # Replace with your guild ID
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                
                self.synced = True
                print(f"✅ Synced slash commands globally and for guild {guild.id}")
            except Exception as e:
                print(f"❌ Error syncing commands: {e}")

# Initialize the bot
bot = MyBot()

# Set up a simple event to confirm bot is ready
@bot.event
async def on_ready():
    print(f'[BOT] Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    
    # Set the bot's presence
    await bot.change_presence(activity=discord.Game(name="/help for commands"))
    
    # Try to sync commands on ready
    try:
        # Sync global commands
        synced = await bot.tree.sync()
        
        # Also sync for the specific guild for faster updates during development
        guild = discord.Object(id=1440330105799839856)  # Replace with your guild ID
        bot.tree.copy_global_to(guild=guild)
        synced_guild = await bot.tree.sync(guild=guild)
        
        print(f'[BOT] Synced {len(synced)} global commands')
        print(f'[BOT] Synced {len(synced_guild)} guild commands')
    except Exception as e:
        print(f'[BOT] Error syncing commands: {e}')

# Command handlers for prefix commands (!)
prefix_commands = {}

def prefix_command(name: str, description: str = ""):
    """Decorator to register prefix commands"""
    def decorator(func):
        prefix_commands[name.lower()] = {
            'function': func,
            'description': description or func.__doc__ or "No description"
        }
        return func
    return decorator

# Simple ping command to test slash commands
@bot.tree.command(name="ping", description="Check if the bot is responding")
async def ping(interaction: discord.Interaction):
    """Simple ping command to test if the bot is responding"""
    await interaction.response.send_message("Pong! 🏓", ephemeral=True)

# Prefix command handler for !ping
@prefix_command(name="ping", description="Check if the bot is responding")
async def ping_prefix(ctx):
    """Simple ping command for prefix commands"""
    await ctx.send("Pong! 🏓")

# Message event handler for prefix commands
@bot.event
async def on_message(message):
    # Don't respond to ourselves or other bots
    if message.author == bot.user or message.author.bot:
        return

    # Process commands with ! prefix
    if message.content.startswith('!'):
        # Split the message into command and arguments
        parts = message.content[1:].split()
        if not parts:
            return

        command_name = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        # Find and execute the command
        if command_name in prefix_commands:
            handler = prefix_commands[command_name]
            try:
                # Call the command function with the message as context
                ctx = await bot.get_context(message)
                await handler['function'](ctx)
                return  # Prevent processing commands twice
            except Exception as e:
                print(f"Error executing command {command_name}: {e}")
                await message.channel.send(f"❌ Error executing command: {e}")
    
    # Process other message events and commands
    await bot.process_commands(message)

# Manual sync command for bot owner
@bot.tree.command(name='sync', description='Sync slash commands (Bot Owner Only)')
@commands.is_owner()
async def sync_commands(interaction: discord.Interaction):
    """Manually sync slash commands"""
    try:
        # Sync global commands
        await interaction.response.defer(ephemeral=True)
        await bot.tree.sync()
        
        # Also sync for the specific guild
        guild = discord.Object(id=1440330105799839856)  # Replace with your guild ID
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
        
        await interaction.followup.send(
            "✅ Successfully synced slash commands!\n"
            "It may take a few minutes for the commands to appear. "
            "If they don't show up, try restarting Discord with Ctrl+R",
            ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(
            f"❌ Failed to sync commands: {e}",
            ephemeral=True
        )

# Initialize bot attributes
bot.trivia_questions = {}  # Initialize trivia_questions dictionary
bot.scheduled_messages = []  # Store scheduled messages

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
        'You\'re welcome! ',
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
        "You're stronger than you think. Keep pushing forward! ",
        "Every expert was once a beginner. You'll get there! ",
        "The only way to fail is to stop trying. Keep going! ",
        "You've got this! I believe in you! ",
        "One step at a time. You're making progress! "]
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
async def send_long_message(channel, content: str, max_length: int = 2000):
    """Helper function to split and send long messages"""
    if len(content) <= max_length:
        await channel.send(content)
        return
    # Split by double newlines first to try to keep paragraphs together
    parts = []
    current_part = ""
    for paragraph in content.split('\n\n'):
        if len(current_part) + len(paragraph) + 2 > max_length:
            if current_part:
                parts.append(current_part)
                current_part = ""
            # If a single paragraph is too long, split by spaces
            if len(paragraph) > max_length:
                words = paragraph.split(' ')
                for word in words:
                    if len(current_part) + len(word) + 1 > max_length:
                        if current_part:
                            parts.append(current_part)
                            current_part = ""
                    current_part += (" " if current_part else "") + word
            else:
                current_part = paragraph
        else:
            current_part += ("\n\n" if current_part else "") + paragraph
    if current_part:
        parts.append(current_part)
    # Send all parts with continuation markers
    for i, part in enumerate(parts):
        if i > 0:
            part = f"(Continued from previous message)\n\n{part}"
        await channel.send(part)
@bot.event
async def on_ready():
    """Event that runs when the bot is ready"""
    print(f'[BOT] Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')
    await bot.change_presence(activity=discord.Game(name="with Python"))
    
@bot.tree.command(name='hello', description='Greet the bot')
async def hello(interaction: discord.Interaction):
    """Greet the bot"""
    await interaction.response.send_message(random.choice(RESPONSES['hello']))

@prefix_command(name='hello', description='Greet the bot')
async def hello_prefix(ctx):
    """Greet the bot (prefix command)"""
    await ctx.send(random.choice(RESPONSES['hello']))

@bot.tree.command(name='joke', description='Tell a random joke')
async def tell_joke(interaction: discord.Interaction):
    """Tell a random joke"""
    try:
        async with aiohttp.ClientSession() as session:
            # Try to get a joke from the API first
            async with session.get('https://v2.jokeapi.dev/joke/Any?type=single') as response:
                if response.status == 200:
                    joke_data = await response.json()
                    if 'joke' in joke_data:
                        await interaction.response.send_message(joke_data['joke'])
                        return
                    elif 'setup' in joke_data and 'delivery' in joke_data:
                        await interaction.response.send_message(f"{joke_data['setup']}\n\n{joke_data['delivery']}")
                        return
    except Exception as e:
        print(f"Error fetching joke: {e}")
    
    # Fallback to local jokes if there's an error
    await interaction.response.send_message(random.choice(JOKES))

@prefix_command(name='joke', description='Tell a random joke')
async def joke_prefix(ctx):
    """Tell a random joke (prefix command)"""
    try:
        async with aiohttp.ClientSession() as session:
            # Try to get a joke from the API first
            async with session.get('https://v2.jokeapi.dev/joke/Any?type=single') as response:
                if response.status == 200:
                    joke_data = await response.json()
                    if 'joke' in joke_data:
                        await ctx.send(joke_data['joke'])
                        return
                    elif 'setup' in joke_data and 'delivery' in joke_data:
                        await ctx.send(f"{joke_data['setup']}\n\n{joke_data['delivery']}")
                        return
    except Exception as e:
        print(f"Error fetching joke: {e}")
    
    # Fallback to local jokes if there's an error
    await ctx.send(random.choice(JOKES))
@bot.tree.command(name='quote', description='Get a random inspirational quote')
async def get_quote(interaction: discord.Interaction):
    """Get a random inspirational quote"""
    await interaction.response.send_message(random.choice(RESPONSES['quote']))

@prefix_command(name='quote', description='Get a random inspirational quote')
async def quote_prefix(ctx):
    """Get a random inspirational quote (prefix command)"""
    await ctx.send(random.choice(RESPONSES['quote']))

@bot.tree.command(name='fact', description='Get a random interesting fact')
async def get_fact(interaction: discord.Interaction):
    """Get a random interesting fact"""
    facts = [
        "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly edible!",
        "A single cloud can weigh more than a million pounds.",
        "There are more stars in the universe than grains of sand on all the Earth's beaches.",
        "Octopuses have three hearts and blue blood.",
        "A group of flamingos is called a 'flamboyance'.",
        "Bananas are berries, but strawberries aren't.",
        "The human brain uses about 20% of the body's total energy.",
        "There are more possible games of chess than atoms in the observable universe.",
        "A day on Venus is longer than a year on Venus.",
        "Cows have best friends and get stressed when they're separated.",
        "The Great Wall of China is not visible from space without aid.",
        "A bolt of lightning contains enough energy to toast 100,000 slices of bread.",
        "There are more fake flamingos in the world than real ones.",
        "The shortest war in history was between Britain and Zanzibar in 1896. Zanzibar surrendered after 38 minutes.",
        "A human's little finger contributes over 50% of the hand's strength.",
        "The inventor of the frisbee was turned into a frisbee after he died.",
        "Some cats are actually allergic to humans."
    ]
    await interaction.response.send_message(random.choice(facts))

@prefix_command(name='fact', description='Get a random interesting fact')
async def fact_prefix(ctx):
    """Get a random interesting fact (prefix command)"""
    facts = [
        "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly edible!",
        "A single cloud can weigh more than a million pounds.",
        "There are more stars in the universe than grains of sand on all the Earth's beaches.",
        "Octopuses have three hearts and blue blood.",
        "A group of flamingos is called a 'flamboyance'.",
        "Bananas are berries, but strawberries aren't.",
        "The human brain uses about 20% of the body's total energy.",
        "There are more possible games of chess than atoms in the observable universe.",
        "A day on Venus is longer than a year on Venus.",
        "Cows have best friends and get stressed when they're separated.",
        "The Great Wall of China is not visible from space without aid.",
        "A bolt of lightning contains enough energy to toast 100,000 slices of bread.",
        "There are more fake flamingos in the world than real ones.",
        "The shortest war in history was between Britain and Zanzibar in 1896. Zanzibar surrendered after 38 minutes.",
        "A human's little finger contributes over 50% of the hand's strength.",
        "The inventor of the frisbee was turned into a frisbee after he died.",
        "Some cats are actually allergic to humans."
    ]
    await ctx.send(random.choice(facts))
@bot.tree.command(name='time', description='Get the current time')
async def get_time(interaction: discord.Interaction):
    """Get the current time"""
    now = datetime.datetime.now()
    await interaction.response.send_message(f"⏰ The current time is: {now.strftime('%I:%M %p')}")

@prefix_command(name='time', description='Get the current time')
async def time_prefix(ctx):
    """Get the current time (prefix command)"""
    now = datetime.datetime.now()
    await ctx.send(f"⏰ The current time is: {now.strftime('%I:%M %p')}")

@bot.tree.command(name='remindme', description='Set a reminder')
@app_commands.describe(
    time="When to remind (e.g., 1h, 30m, 2d)",
    message="The reminder message"
)
async def set_reminder(interaction: discord.Interaction, time: str, message: str):
    """Set a reminder"""
    await interaction.response.send_message(f"⏰ I'll remind you to \"{message}\" in {time}")
@bot.tree.command(name='encourage', description='Get encouragement when you\'re feeling down')
async def encourage(interaction: discord.Interaction):
    """Get encouragement when you're feeling down"""
    await interaction.response.send_message(random.choice(RESPONSES['encourage']))

@prefix_command(name='encourage', description='Get encouragement when you\'re feeling down')
async def encourage_prefix(ctx):
    """Get encouragement when you're feeling down (prefix command)"""
    await ctx.send(random.choice(RESPONSES['encourage']))

@bot.tree.command(name='afk', description='Set yourself as AFK with an optional reason')
@app_commands.describe(reason="Reason for being AFK")
async def set_afk(interaction: discord.Interaction, reason: str = "AFK"):
    """Set yourself as AFK with an optional reason"""
    user_id = interaction.user.id
    afk_users[user_id] = {
        'reason': reason,
        'time': datetime.datetime.now(),
        'original_nick': interaction.user.display_name
    }
    # Try to update nickname if possible
    try:
        if interaction.guild:
            await interaction.user.edit(nick=f"[AFK] {interaction.user.display_name[:26]}")
    except:
        pass  # No permission to change nickname
    await interaction.response.send_message(f"{interaction.user.mention} is now AFK: {reason} ‍")
@bot.tree.command(name='clear', description='Clear the conversation history for this channel')
async def clear_history(interaction: discord.Interaction):
    """Clear the conversation history for this channel"""
    if interaction.channel_id in conversation_history:
        # Keep only the system message
        conversation_history[interaction.channel_id] = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]
        await interaction.response.send_message("Conversation history cleared!", ephemeral=True)
    else:
        await interaction.response.send_message("No conversation history to clear.", ephemeral=True)
@bot.tree.command(name='help', description='Show all available commands organized by categories')
async def help_command(interaction: discord.Interaction):
    """Show all available commands organized by categories"""
    try:
        # Main categories
        categories = {
    "Trivia & Games": [
        "`!trivia [category]` - Get a random trivia question",
        "`!rps <rock/paper/scissors>` - Play Rock, Paper, Scissors",
        "`!hangman` - Start a new Hangman game",
        "`!quiz` - Take a quiz on various topics (type answers or letters)",
        "`!tictactoe @user` - Play Tic Tac Toe with a friend",
        "`!move 1-9` - Make a move in Tic Tac Toe"
    ],
    "Chat & AI": [
        "Mention me or reply to my messages to chat!",
        "`!clear` - Clear conversation history",
        "`!ask [question]` - Ask me anything",
        "`!generate [prompt]` - Generate an image (Allowed users only)"
    ],
    "Utility": [
        "`!afk [reason]` - Set AFK status",
        "`!time` - Show current time",
        "`!remindme [time] [message]` - Set a reminder",
        "`!reload` - Reload the bot (Admin only)",
        "`!echo [message]` - Make the bot repeat your message"
    ],
    "Fun": [
        "`!joke` - Get a random joke",
        "`!quote` - Get an inspirational quote",
        "`!fact` - Get a random interesting fact"
    ],
    "Info": [
        "`!helpme`, `!cmds`, or `!commands` - Show this help message"
    ]
}
        # Rest of the function...
        # Build the help message
        help_text = ["Bot Commands\n*Type a command for more info*"]
        # Add each category with its commands
        for category, commands in categories.items():
            help_text.append(f"\n\n{category}")
            help_text.extend([f"\n{cmd}" for cmd in commands])
        # Add footer
        help_text.append("\n\n *Need help? Type `!helpme [command]` for more info*")
        # Ensure the message isn't too long
        full_message = "".join(help_text)
        if len(full_message) > 2000:
            full_message = full_message[:1996] + "..."
        # Send the message
        await send_long_message(ctx, full_message)
    except Exception as e:
        print(f"Error in help command: {e}")
@bot.tree.command(name='reload', description='Reload the bot (Admin only)')
@is_allowed_channel()
async def reload_bot(interaction: discord.Interaction):
    """Reload the bot (Admin only)"""
    if interaction.user.id not in TERMINAL_ADMINS:
        return await interaction.response.send_message(" **Restricted:** This command is for authorized admins only.", ephemeral=True)
    await interaction.response.send_message("Reloading bot... This may take a few seconds.", ephemeral=True)
    import sys
    import os
    # Clear all active games
    if hasattr(bot, 'active_games'):
        bot.active_games.clear()
    # Restart the bot
    os.execv(sys.executable, ['python'] + sys.argv)
@bot.tree.command(name='terminal', description='Run Python code (Admin only)')
@app_commands.describe(code="Python code to execute")
async def internal_terminal(interaction: discord.Interaction, code: str):
    """Run Python code (Admin only)"""
    # Check if the user is authorized
    if interaction.user.id not in TERMINAL_ADMINS:
        return await interaction.response.send_message(
            " **Restricted:** This command is for authorized terminal admins only.",
            ephemeral=True
        )
    
    # Defer the response since this might take a while
    await interaction.response.defer(ephemeral=True)
    
    # Clean up the code input
    if code.startswith('```'):
        code = '\n'.join(code.split('\n')[1:-1])
    else:
        code = code.strip('` \n')
    
    stdout = io.StringIO()
    try:
        env = {
            'bot': bot, 
            'interaction': interaction, 
            'author': interaction.user,
            'guild': interaction.guild,
            'channel': interaction.channel
        }
        env.update(globals())
        
        exec_text = f'async def func():\n{textwrap.indent(code, "  ")}'
        exec(exec_text, env)
        func = env['func']
        
        with contextlib.redirect_stdout(stdout):
            ret = await func()
            
        output = stdout.getvalue()
        result = f"```py\n{output or 'Success (no output)'}"
        if ret is not None:
            result += f"\n# Return value: {ret}"
        result += "```"
        
        # Ensure the message isn't too long
        if len(result) > 2000:
            result = result[:1990] + "\n... (truncated)"
            
        await interaction.followup.send(result, ephemeral=True)
        
    except Exception as e:
        error_msg = f"```py\n{traceback.format_exc()}"
        if str(e):
            error_msg += f"\n# Error: {e}"
        error_msg += "```"
        
        if len(error_msg) > 2000:
            error_msg = error_msg[:1990] + "\n... (truncated)"
            
        await interaction.followup.send(error_msg, ephemeral=True)
@bot.tree.command(name='echo', description='Make the bot repeat your message')
@app_commands.describe(message="The message to repeat")
async def echo_message(interaction: discord.Interaction, message: str):
    """Make the bot repeat your message in the current channel"""
    try:
        # Check permissions before sending
        if not interaction.channel.permissions_for(interaction.user).manage_messages:
            return await interaction.response.send_message(
                "You need 'Manage Messages' permission to use this command.", 
                ephemeral=True,
                delete_after=5
            )
        
        # Send the message
        await interaction.response.send_message(message, ephemeral=False)
        
        # Delete the bot's message after 1 minute
        await asyncio.sleep(60)
        try:
            # Get the message we just sent to delete it
            async for msg in interaction.channel.history(limit=1):
                if msg.author == interaction.client.user and msg.content == message:
                    await msg.delete()
                    break
        except:
            pass  # Message already deleted or no permissions
            
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        try:
            await interaction.followup.send(error_msg, ephemeral=True, delete_after=10)
        except:
            # If we can't send the error message, try to send it to the user's DM
            try:
                await interaction.user.send(f"Failed to send message in {interaction.channel.mention}: {error_msg}")
            except:
                pass  # Can't send DM either, just give up
# Define category choices for the trivia command
class TriviaCategory(enum.Enum):
    GENERAL = "general"
    BOOKS = "books"
    FILMS = "films"
    MUSIC = "music"
    THEATRE = "theatre"
    TV = "tv"
    GAMES = "games"
    BOARDGAMES = "boardgames"
    SCIENCE = "science"
    COMPUTERS = "computers"
    MATH = "math"
    MYTHOLOGY = "mythology"
    SPORTS = "sports"
    GEOGRAPHY = "geography"
    HISTORY = "history"
    POLITICS = "politics"
    ART = "art"
    CELEBRITIES = "celebrities"
    ANIMALS = "animals"
    VEHICLES = "vehicles"
    COMICS = "comics"
    GADGETS = "gadgets"
    ANIME = "anime"
    CARTOONS = "cartoons"

@bot.tree.command(name='trivia', description='Get a random trivia question')
@app_commands.describe(category="Category for the trivia question")
async def trivia(interaction: discord.Interaction, category: TriviaCategory = None):
    """Get a random trivia question with interactive buttons!"""
    categories = {
        'general': 9, 'books': 10, 'films': 11, 'music': 12, 'theatre': 13,
        'tv': 14, 'games': 15, 'boardgames': 16, 'science': 17, 'computers': 18,
        'math': 19, 'mythology': 20, 'sports': 21, 'geography': 22, 'history': 23,
        'politics': 24, 'art': 25, 'celebrities': 26, 'animals': 27, 'vehicles': 28,
        'comics': 29, 'gadgets': 30, 'anime': 31, 'cartoons': 32
    }
    
    # Get category ID or use general knowledge
    category_str = category.value if category else 'general'
    category_id = categories.get(category_str, 9)
    category_name = category_str
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
                        }.get(question_data['difficulty'], '')
                        
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
                                    try:
                                        await self.message.edit(
                                            content=f"⏰ Time's up! The correct answer was: **{self.correct_answer}**",
                                            view=self
                                        )
                                    except:
                                        pass  # Message already deleted or other error
                            
                            async def button_callback(self, interaction: discord.Interaction):
                                if self.answered:
                                    return await interaction.response.send_message(
                                        "This question has already been answered!",
                                        ephemeral=True
                                    )
                                
                                self.answered = True
                                selected = int(interaction.data['custom_id']) - 1
                                
                                # Update all buttons
                                for i, item in enumerate(self.children):
                                    if i == selected:
                                        # Mark selected answer as correct/wrong
                                        item.style = (
                                            discord.ButtonStyle.success 
                                            if self.answers[selected] == self.correct_answer 
                                            else discord.ButtonStyle.danger
                                        )
                                    else:
                                        # Disable other buttons
                                        item.disabled = True
                                    
                                    # If this is the correct answer, highlight it
                                    if hasattr(item, 'label') and item.label == self.correct_answer:
                                        item.style = discord.ButtonStyle.success
                                
                                # Send the response
                                if self.answers[selected] == self.correct_answer:
                                    response_text = f"✅ **Correct!** The answer was: **{self.correct_answer}**"
                                else:
                                    response_text = f"❌ **Incorrect!** The correct answer was: **{self.correct_answer}**"
                                
                                try:
                                    await interaction.response.edit_message(
                                        content=f"**{self.category_name}** - {self.difficulty}\n{self.question_text}\n\n{response_text}",
                                        view=self
                                    )
                                except Exception as e:
                                    print(f"Error updating trivia message: {e}")
                        
                        # Create and send the trivia question
                        view = TriviaView(correct_answer, answers, question, category_name, difficulty_emoji)
                        
                        # Send the initial message with the question
                        message = await interaction.response.send_message(
                            f"**{category_name}** - {difficulty_emoji}\n{question}",
                            view=view
                        )
                        
                        # Store the message in the view for later updates
                        if hasattr(interaction, 'response'):
                            # For interaction-based responses
                            view.message = await interaction.original_response()
                        else:
                            # Fallback for regular message-based responses
                            view.message = message
    except Exception as e:
        print(f"Error fetching trivia question: {e}")
        await send_long_message(ctx, " An error occurred while fetching the trivia question. Please try again later.")
class RPSView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)
        self.choice = None
    @discord.ui.button(label=' Rock', style=discord.ButtonStyle.primary)
    async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_choice(interaction, "rock")
    @discord.ui.button(label=' Paper', style=discord.ButtonStyle.primary)
    async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_choice(interaction, "paper")
    @discord.ui.button(label=' Scissors', style=discord.ButtonStyle.primary)
    async def scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_choice(interaction, "scissors")
    async def handle_choice(self, interaction: discord.Interaction, choice: str):
        self.choice = choice
        bot_choice = RPSGame.get_random_choice()
        result = RPSGame.get_winner(choice, bot_choice)
        if result == "tie":
            message = f" It's a tie! We both chose {bot_choice}."
        elif result == "player":
            message = f" You win! {choice.capitalize()} beats {bot_choice}."
        else:
            message = f" You lose! {bot_choice.capitalize()} beats {choice}."
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
@bot.tree.command(name='rps', description='Play Rock-Paper-Scissors with the bot')
async def rock_paper_scissors(interaction: discord.Interaction):
    """Play Rock-Paper-Scissors with the bot"""
    view = RPSView()
    await interaction.response.send_message("Choose your move:", view=view)
    view.message = await interaction.original_response()
@bot.tree.command(name='hangman', description='Start a game of Hangman')
async def hangman(interaction: discord.Interaction):
    """Start a game of Hangman"""
    channel_id = interaction.channel.id
    if channel_id in bot.active_games and isinstance(bot.active_games[channel_id], HangmanGame):
        await interaction.response.send_message("There's already an active Hangman game in this channel!", ephemeral=True)
        return
    
    word = random.choice(HANGMAN_WORDS)
    game = HangmanGame(word)
    bot.active_games[channel_id] = game
    view = HangmanView(game, channel_id)
    
    # Send the initial game message
    await interaction.response.send_message(
        f" **New Hangman Game!** \n"
        f"Guess the word: {game.get_display_word()}\n"
        f"You have {game.max_attempts} attempts.\n"
        f"{game.get_hangman()}\n\n"
        f"**Available Letters:**\n{view.get_letter_display()}",
        view=view
    )
    
    # Store the message in the view for later updates
    view.message = await interaction.original_response()

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
            label=' Submit Guess',
            style=discord.ButtonStyle.primary
        )
        self.submit_button.callback = self.submit_guess
        self.add_item(self.submit_button)
        # Add stop button
        self.stop_button = discord.ui.Button(
            label='⏹ Stop Game',
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
                f" **Hangman Game** \n"
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
            content="⏹ Game stopped by user.",
            view=self
        )
        self.stop()  # Stop the view
@bot.tree.command(name='guess', description='Guess a letter in the Hangman game')
@app_commands.describe(letter='The letter to guess (A-Z)')
async def guess_letter(interaction: discord.Interaction, letter: str):
    """This command is no longer used. Please use the buttons in the Hangman game interface to guess letters."""
    await interaction.response.send_message(
        "This command is no longer used. "
        "Please use the buttons in the Hangman game interface to make your guesses.",
        ephemeral=True
    )
    # Try to resend the current game state if it exists
    channel_id = interaction.channel.id
    if channel_id in bot.active_games and isinstance(bot.active_games[channel_id], HangmanGame):
        game = bot.active_games[channel_id]
        await interaction.response.send_message(
            f"Current game state:\n"
            f"Word: {game.get_display_word()}\n"
            f"Incorrect guesses: {game.incorrect_guesses}/{game.max_attempts}\n"
            f"{game.get_hangman()}"
        )
@bot.tree.command(name='quiz', description='Start a new quiz game')
@app_commands.checks.has_permissions(send_messages=True)
async def start_quiz(interaction: discord.Interaction):
    """Start a new quiz game"""
    channel_id = interaction.channel.id
    if channel_id in bot.active_games and isinstance(bot.active_games[channel_id], QuizGame):
        await interaction.response.send_message(
            "There's already an active quiz in this channel!",
            ephemeral=True
        )
        return
    
    # Create a copy of the questions to avoid modifying the original list
    questions = QUIZ_QUESTIONS.copy()
    game = QuizGame(questions)
    bot.active_games[channel_id] = game
    
    # Acknowledge the interaction and start the quiz
    await interaction.response.send_message("Starting a new quiz game! Get ready for the first question...")
    await ask_quiz_question(interaction, game)
async def ask_quiz_question(interaction: discord.Interaction, game):
    """Ask the current quiz question with multiple choice options"""
    question = game.get_new_question()
    if not question:
        await interaction.followup.send("No more questions! Thanks for playing!")
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
    
    # Create a view with buttons for each option
    class QuizView(discord.ui.View):
        def __init__(self, game, question, options):
            super().__init__(timeout=60)  # 60 second timeout
            self.game = game
            self.question = question
            self.options = options
            self.correct_answer = question['answer']
            
            # Add buttons for each option
            for i, option in enumerate(options):
                letter = chr(65 + i)  # A, B, C, D
                button = discord.ui.Button(
                    label=f"{letter}. {option}",
                    style=discord.ButtonStyle.primary,
                    custom_id=str(i)
                )
                button.callback = self.button_callback
                self.add_item(button)
        
        async def button_callback(self, interaction: discord.Interaction):
            selected = int(interaction.data['custom_id'])
            selected_answer = self.options[selected]
            
            # Check if the answer is correct
            if selected_answer == self.correct_answer:
                self.game.score += 1
                result = "✅ **Correct!**"
            else:
                result = f"❌ **Incorrect!** The correct answer was: **{self.correct_answer}**"
            
            # Disable all buttons
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    item.disabled = True
                    if item.custom_id == str(selected):
                        item.style = discord.ButtonStyle.success if selected_answer == self.correct_answer else discord.ButtonStyle.danger
            
            # Update the message with the result
            await interaction.response.edit_message(
                content=(
                    f" **Question {self.game.question_number - 1} of {self.game.total_questions}**\n"
                    f"{self.question['question']}\n\n"
                    f"**Your answer:** {selected_answer}\n"
                    f"{result}\n\n"
                    f"**Score:** {self.game.score}/{self.game.question_number - 1}"
                ),
                view=self
            )
            
            # Ask the next question or end the quiz
            if self.game.question_number <= self.game.total_questions:
                await asyncio.sleep(3)  # Short delay before next question
                await ask_quiz_question(interaction, self.game)
            else:
                await interaction.followup.send(
                    f"🎉 **Quiz Complete!** 🎉\n"
                    f"**Final Score:** {self.game.score}/{self.game.total_questions}"
                )
                # Clean up
                channel_id = interaction.channel.id
                if channel_id in bot.active_games:
                    del bot.active_games[channel_id]
        
        async def on_timeout(self):
            # Disable all buttons when view times out
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    item.disabled = True
            try:
                await self.message.edit(view=self)
                await self.message.reply("⏰ Time's up! The quiz has ended due to inactivity.")
            except:
                pass  # Message already deleted or other error
    
    # Create and send the quiz question with buttons
    view = QuizView(game, question, options)
    
    # Send the question with the view
    message = await interaction.followup.send(
        f" **Question {game.question_number} of {game.total_questions}**\n"
        f"{question['question']}\n\n"
        "**Select your answer:**",
        view=view,
        wait=True
    )
    
    # Store the message in the view for later updates
    view.message = message
@bot.tree.command(name='answer', description='Answer the current quiz question')
@app_commands.describe(answer='Your answer to the current quiz question')
@app_commands.checks.has_permissions(send_messages=True)
async def answer_question(interaction: discord.Interaction, answer: str):
    """Answer the current quiz question"""
    channel_id = interaction.channel.id
    
    # Check if there's an active quiz
    if channel_id not in bot.active_games or not isinstance(bot.active_games[channel_id], QuizGame):
        await interaction.response.send_message(
            "There's no active quiz in this channel! Start one with `/quiz`",
            ephemeral=True
        )
        return
    
    # Get the current game
    game = bot.active_games[channel_id]
    
    # Check if the game is waiting for an answer
    if not hasattr(game, 'current_question') or not game.current_question:
        await interaction.response.send_message(
            "There's no active question to answer! Start a new quiz with `/quiz`",
            ephemeral=True
        )
        return
    
    # Process the answer
    is_correct, message = game.check_answer(answer)
    
    # Send the result
    await interaction.response.send_message(message, ephemeral=True)
    
    # If there are more questions, ask the next one
    if len(game.questions) > 0:
        await asyncio.sleep(2)  # Short delay before next question
        await ask_quiz_question(interaction, game)
    else:
        # Quiz is complete
        await interaction.followup.send(
            f"🎉 **Quiz Complete!** 🎉\n"
            f"**Final Score:** {game.score}/{game.total_questions}"
        )
        # Clean up
        if channel_id in bot.active_games:
            del bot.active_games[channel_id]
@bot.tree.command(name='stop', description='Stop the current game in this channel')
@app_commands.checks.has_permissions(manage_messages=True)
async def stop_game(interaction: discord.Interaction):
    """Stop the current game in this channel"""
    channel_id = interaction.channel.id
    if channel_id not in bot.active_games:
        await interaction.response.send_message(
            "There's no active game to stop in this channel!",
            ephemeral=True
        )
        return
    
    # Get the game and clean up
    game = bot.active_games[channel_id]
    del bot.active_games[channel_id]
    
    # Send appropriate message based on game type
    if isinstance(game, HangmanGame):
        message = f"⏹ Hangman game stopped. The word was: **{game.word}**"
    elif isinstance(game, QuizGame):
        message = f"⏹ Quiz stopped. Your final score was: {game.score}/{game.question_number-1}"
    elif isinstance(game, TicTacToeGame):
        message = "⏹ Tic Tac Toe game stopped."
    else:
        message = "⏹ Game stopped."
    
    await interaction.response.send_message(message, ephemeral=False)
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
            label=' Make Move',
            style=discord.ButtonStyle.primary
        )
        self.submit_button.callback = self.submit_move
        self.add_item(self.submit_button)
        # Add stop button
        self.stop_button = discord.ui.Button(
            label='⏹ Stop Game',
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
                                f" **Tic Tac Toe** \n"
                                f"{self.game.players[0].mention} () vs {self.game.players[1].mention} ()\n\n"
                                f" **{self.game.winner.mention} wins!** \n\n"
                                f"{board}"
                            ),
                            view=None
                        )
                    else:
                        await interaction.response.edit_message(
                            content=(
                                f" **Tic Tac Toe** \n"
                                f"{self.game.players[0].mention} () vs {self.game.players[1].mention} ()\n\n"
                                f" **It's a draw!** \n\n"
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
                            f" **Tic Tac Toe** \n"
                            f"{self.game.players[0].mention} () vs {self.game.players[1].mention} ()\n"
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
            content="⏹ Tic Tac Toe game stopped by user.",
            view=self
        )
        self.stop()  # Stop the view

@bot.tree.command(name='tictactoe', description='Start a Tic Tac Toe game')
@app_commands.describe(
    opponent="The user to play against (or 'bot' to play against AI)",
    difficulty="AI difficulty level (easy, medium, hard)"
)
async def tictactoe(interaction: discord.Interaction, opponent: discord.Member = None, difficulty: str = 'medium'):
    """Start a Tic Tac Toe game"""
    # Handle playing against the bot
    if opponent and (opponent.bot or str(opponent).lower() == 'bot'):
        difficulty = difficulty.lower()
        if difficulty not in ['easy', 'medium', 'hard']:
            difficulty = 'medium'
        
        channel_id = interaction.channel.id
        
        # Check if there's already a game in this channel
        if channel_id in bot.active_games:
            await interaction.response.send_message(
                "There's already an active game in this channel! Use `/stop` to end it first.",
                ephemeral=True
            )
            return
            
        # Create and store the game with AI
        game = TicTacToeGame(interaction.user, difficulty=difficulty)
        bot.active_games[channel_id] = game
        
        # Create the view with buttons
        view = TicTacToeView(game, channel_id)
        
        # Send initial game board
        board = game.get_board_display()
        message = await send_long_message(ctx,
            f" **Tic Tac Toe**  (vs AI - {difficulty.capitalize()})\n"
            f"{ctx.author.mention} () vs  Bot ()\n"
            f"It's {ctx.author.mention}'s turn! ()\n\n"
            f"**How to play:**\n"
            f"Click the 'Make Move' button and enter a number (1-9).\n"
            f"Positions are numbered from left to right, top to bottom.\n\n"
            f"{board}",
            view=view
        )
        view.message = message
        return
    # Handle playing against another user
    if opponent is None:
        await send_long_message(
            ctx,
            "Please specify an opponent or 'bot' to play against the AI.\n"
            "Examples:\n"
            "`!tictactoe @username` - Play against a user\n"
            "`!tictactoe bot` - Play against the AI (medium difficulty)\n"
            "`!tictactoe bot easy` - Play against an easy AI"
        )
        return
    if opponent == interaction.user:
        await interaction.response.send_message(
            "You can't play against yourself! Try '/tictactoe bot' to play against the AI.",
            ephemeral=True
        )
        return
        
    channel_id = interaction.channel.id
    
    # Check if there's already a game in this channel
    if channel_id in bot.active_games:
        await interaction.response.send_message(
            "There's already an active game in this channel! Use '/stop' to end it first.",
            ephemeral=True
        )
        return
    
    # Create and store the game
    game = TicTacToeGame(interaction.user, opponent)
    bot.active_games[channel_id] = game
    
    # Create the view with buttons
    view = TicTacToeView(game, channel_id)
    
    # Get the initial board state
    board = game.get_board_display()
    
    # Send the initial game message
    await interaction.response.send_message(
        f"**Tic Tac Toe**\n"
        f"{interaction.user.mention} (X) vs {opponent.mention} (O)\n"
        f"It's {interaction.user.mention}'s turn!\n\n"
        f"**How to play:**\n"
        f"Click the 'Make Move' button and enter a number (1-9).\n"
        f"Positions are numbered from left to right, top to bottom.\n\n"
        f"{board}",
        view=view
    )
    
    # Store the message in the view for later updates
    view.message = await interaction.original_response()

@bot.tree.command(name='ask', description='Ask the AI a question with conversation history')
@is_allowed_channel()
async def ask_ai(interaction: discord.Interaction, question: str):
    """Ask the AI a question with conversation history"""
    try:
        await interaction.response.defer()
        
        # Get or initialize conversation history for this channel
        history = get_history(interaction)
        
        # Add user's question to history
        history.append({"role": "user", "content": question})
        
        # Keep only the most recent messages (plus system message)
        if len(history) > MAX_HISTORY + 1:  # +1 for system message
            history = [history[0]] + history[-(MAX_HISTORY):-1] + [history[-1]]
        
        # Initialize the client with your API key
        co = cohere.ClientV2(api_key=os.getenv('COHERE_API_KEY'))
        
        try:
            # Make the API call with conversation history
            response = co.chat(
                model="command-a-03-2025",
                messages=history,
                temperature=0.4,
                max_tokens=500  # Limit response length
            )
            
            # Extract the text from the response
            try:
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
                answer = "I'm sorry, I couldn't generate a response. Could you try asking something else?"
            
            # Add AI's response to history
            history.append({"role": "assistant", "content": answer})
            
            # Update the conversation history
            conversation_history[interaction.channel.id] = history
            
            # Split the answer into chunks of 2000 characters (Discord's message limit)
            chunk_size = 1900  # Slightly less to account for the emoji and continuation markers
            chunks = [answer[i:i+chunk_size] for i in range(0, len(answer), chunk_size)]
            
            # Send the first chunk as a followup to the interaction
            if chunks:
                await interaction.followup.send(chunks[0])
            
            # Send remaining chunks as separate messages
            for chunk in chunks[1:]:
                try:
                    await interaction.channel.send(f"(Continued from previous message)\n\n{chunk}")
                except Exception as e:
                    print(f"Error sending message chunk: {e}")
                    continue
                    
        except Exception as e:
            error_msg = f"Error in Cohere API call: {str(e)}"
            print(f"Ask AI Error: {error_msg}")
            await interaction.followup.send("I'm having trouble connecting to the AI service. Please try again later.")
            
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"Ask AI Error: {error_msg}")
        try:
            await interaction.followup.send("I'm having trouble thinking right now. Could you try again?")
        except:
            # If we can't send a followup, try sending a regular message
            try:
                await interaction.channel.send("I'm having trouble thinking right now. Could you try again?")
            except Exception as e:
                print(f"Failed to send error message: {e}")
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
        try:
            if message.guild:
                await message.author.edit(nick=afk_data['original_nick'])
        except:
            pass  # No permission to change nickname
        await send_long_message(message.channel, f"Welcome back {message.author.mention}! You were AFK for {str(time_afk).split('.')[0]}. (Reason: {afk_data['reason']})")
    
    # Don't respond to other bots
    if message.author.bot:
        return

    # Process commands first
    await bot.process_commands(message)

    # Check if this is a reply to the bot
    is_reply_to_bot = False
    referenced_message = None
    if message.reference:
        try:
            print(f"DEBUG: Message is a reply to message ID: {message.reference.message_id}")
            # Get the referenced message
            if hasattr(message.reference, 'resolved') and message.reference.resolved:
                referenced_message = message.reference.resolved
            elif message.reference.message_id:
                channel = bot.get_channel(message.reference.channel_id) or message.channel
                if channel:
                    try:
                        referenced_message = await channel.fetch_message(message.reference.message_id)
                    except discord.NotFound:
                        print(f"Could not find referenced message {message.reference.message_id}")
            
            if referenced_message:
                print(f"DEBUG: Found referenced message from {referenced_message.author} (Bot: {referenced_message.author == bot.user})")
                print(f"DEBUG: Referenced message content: {referenced_message.content}")
                if referenced_message.author.id == bot.user.id:
                    is_reply_to_bot = True
                    print("DEBUG: This is a reply to the bot's message")
        except Exception as e:
            print(f"Error checking reply: {e}")

    # Check if this is an answer to a trivia question
    if hasattr(bot, 'trivia_questions') and message.reference and message.reference.message_id in bot.trivia_questions:
        trivia_data = bot.trivia_questions[message.reference.message_id]
        if datetime.datetime.now() > trivia_data['expires']:
            del bot.trivia_questions[message.reference.message_id]
            return
        try:
            answer = int(message.content.strip())
            if answer == trivia_data['correct']:
                await message.add_reaction('✅')
                await send_long_message(message.channel, f" Correct! The answer was: **{trivia_data['answer']}**")
            else:
                await message.add_reaction('❌')
                await message.reply(
                    f"That's not quite right! The correct answer was: **{trivia_data['answer']}**",
                    mention_author=False
                )
            if message.reference.message_id in bot.trivia_questions:
                del bot.trivia_questions[message.reference.message_id]
        except ValueError:
            pass
        except Exception as e:
            print(f"Error processing trivia answer: {e}")
        return

    # Check if someone mentioned an AFK user
    for mention in message.mentions:
        if mention.id in afk_users and mention.id != message.author.id:
            afk_data = afk_users[mention.id]
            afk_time = datetime.datetime.now() - afk_data['time']
            await send_long_message(message.channel, f"{mention.display_name} is AFK: {afk_data['reason']} (for {str(afk_time).split('.')[0]} ago)")

    # Handle messages where the bot is mentioned, it's a DM, or a reply to the bot
    if (bot.user.mentioned_in(message) or 
        isinstance(message.channel, discord.DMChannel) or 
        is_reply_to_bot):
        try:
            print(f"DEBUG: Processing message - Type: {type(message).__name__}, Content: '{message.content}'")
            print(f"DEBUG: is_reply_to_bot: {is_reply_to_bot}, is_mention: {bot.user.mentioned_in(message)}, is_dm: {isinstance(message.channel, discord.DMChannel)}")
            
            # Remove bot mention if present
            content = message.content.replace(f'<@{bot.user.id}>', '').strip()
            
            # If it's a reply to the bot, get the original message content
            if is_reply_to_bot and (not content or content.isspace()):
                try:
                    print("DEBUG: Processing reply to bot's message")
                    channel = bot.get_channel(message.reference.channel_id) or message.channel
                    if channel:
                        print(f"DEBUG: Fetching referenced message {message.reference.message_id} from channel {channel.id}")
                        referenced_msg = await channel.fetch_message(message.reference.message_id)
                        if referenced_msg.author.id == bot.user.id:
                            # If replying with no content, use the original message's content
                            if referenced_msg.embeds:
                                content = referenced_msg.embeds[0].description or ""
                                print(f"DEBUG: Using embedded content from referenced message: {content}")
                            else:
                                content = referenced_msg.content
                                print(f"DEBUG: Using text content from referenced message: {content}")
                except Exception as e:
                    print(f"ERROR: Failed to process reply: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Create a proper context for the message
            try:
                import traceback
                
                # First try to get the context normally
                ctx = await bot.get_context(message)
                
                # If we don't have a valid command, create a minimal context manually
                if not ctx.valid:
                    print("DEBUG: Creating minimal context")
                    
                    # Create a simple context without trying to modify valid
                    ctx = await bot.get_context(message)
                    
                    # Create a custom context class that's always valid
                    class ContextWrapper(discord.ext.commands.Context):
                        def __init__(self, **kwargs):
                            super().__init__(**kwargs)
                            self._valid = True
                        
                        @property
                        def valid(self):
                            return True
                    
                    ctx = ContextWrapper(bot=bot, message=message, view=ctx.view, prefix=bot.command_prefix)
                
                print(f"DEBUG: Context created - valid: {getattr(ctx, 'valid', False)}, command: {getattr(ctx, 'command', None)}")
            except Exception as e:
                import traceback
                error_msg = f"Error creating context: {str(e)}\n{traceback.format_exc()}"
                print(error_msg)
                await send_long_message(message.channel, "Sorry, I encountered an error processing your message. Please try again!")
                return
            
            print(f"DEBUG: Final content to process: '{content}'")
            
            # Use the ask_ai function to handle the response
            if content or is_reply_to_bot:
                question = content or message.content
                print(f"DEBUG: Calling ask_ai with question: '{question}'")
                await ask_ai(ctx, question=question)
            else:
                print("DEBUG: No content to process, sending hello response")
                await send_long_message(message.channel, random.choice(RESPONSES['hello']))
                
        except Exception as e:
            import traceback
            error_msg = f"ERROR in message handling: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            try:
                await send_long_message(message.channel, "Sorry, I encountered an error processing your message. Please try again!")
            except Exception as send_error:
                print(f"ERROR sending error message: {send_error}")
            import traceback
            traceback.print_exc()

# ... (rest of the code remains the same)

# --- Place this WITH your other global variables (around line 30) ---
# Initialize Google Client (Use your actual API key)
# google_client = genai.Client(api_key="AIzaSyCHoOpWo49JH6cFOe0ybGAn0VeUBBoRk54") 

# --- Place this command near your other commands (e.g. after !ask) ---

# --- Add this import at the top with your other imports ---
 

# --- Replace your existing 'generate' command with this one ---
import requests
import io
import discord
from discord.ext import commands

import re
import unicodedata

def is_suspicious(text):
    """Check if text contains suspicious patterns"""
    # Check for excessive special characters
    special_chars = len(re.findall(r'[^\w\s]', text))
    if special_chars > len(text) * 0.3:  # More than 30% special chars
        return True
        
    # Check for suspicious patterns
    suspicious_patterns = [
        r'\d{10,}',  # Long numbers
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',  # URLs
        r'[\w\.-]+@[\w\.-]+\.\w+',  # Email addresses
        r'[\s\S]*(.)\1{5,}[\s\S]*',  # Repeated characters (6+ times)
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
            
    return False

def normalize_text(text):
    # Convert to lowercase
    text = text.lower()
    # Remove accents and special characters
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    # Replace common leet speak and special characters
    leet_map = {
        '1': 'i', '!': 'i', '3': 'e', '4': 'a', '@': 'a',
        '0': 'o', '5': 's', '7': 't', '8': 'b', '$': 's',
        '9': 'g', '()': 'o', '[]': 'o', '|)': 'd', '|]': 'd',
        '|=': 'f', 'ph': 'f', 'vv': 'w', 'vvv': 'm', 'vvvv': 'w'
    }
    for k, v in leet_map.items():
        text = text.replace(k, v)
    # Remove all non-alphanumeric characters
    text = re.sub(r'[^a-z0-9]', '', text)
    return text

def contains_banned_word(text, banned_words):
    # Normalize the input text
    normalized_text = normalize_text(text)
    
    # Split into words and check each one
    words = re.findall(r'[a-z0-9]+', normalized_text)
    
    # Check for exact matches first
    for word in words:
        if word in banned_words:
            return word
    
    # Block all anatomical/medical terms regardless of context
    blocked_anatomical_terms = [
        'reproductive', 'genital', 'organ', 'penis', 'vagina', 'testicl', 'testes', 
        'scrotum', 'vulva', 'labia', 'clitoris', 'breast', 'areola', 'nipple',
        'anus', 'rectum', 'buttock', 'pubic', 'pelvic', 'semen', 'sperm', 'penile',
        'vaginal', 'anal', 'sexual', 'sex', 'nude', 'naked', 'exposed','skin'
    ]
    
    # Check for any blocked terms
    text_lower = text.lower()
    for term in blocked_anatomical_terms:
        if term in text_lower:
            return term
            
    # Check for partial matches in longer words (3+ chars)
    for word in words:
        if len(word) > 3:
            for banned in [b for b in banned_words if len(b) >= 3]:
                if banned in word:
                    return banned
                    
    return None
@bot.tree.command(name='report', description='Report a false positive in content filtering')
@app_commands.describe(reason='The reason for reporting this as a false positive')
@app_commands.checks.cooldown(1, 300)  # 1 report per 5 minutes per user
async def report_false_positive(interaction: discord.Interaction, reason: str):
    """Report a false positive in the content filter"""
    channel = bot.get_channel(MODERATION_CHANNEL_ID)
    if channel:
        # Get the referenced message if any
        ref_message = None
        if interaction.message.reference and isinstance(interaction.message.reference.resolved, discord.Message):
            ref_message = interaction.message.reference.resolved.content
        
        # Send the report to the moderation channel
        await channel.send(
            f"⚠️ False positive report from {interaction.user.mention}:\n"
            f"Message: {ref_message or 'No message referenced'}\n"
            f"Reason: {reason}\n"
            f"Channel: {interaction.channel.mention} ({interaction.channel_id})"
        )
        
        # Send a confirmation to the user
        await interaction.response.send_message(
            "✅ Your report has been submitted. Thank you for your feedback!",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "❌ Could not find the moderation channel. Please contact an administrator.",
            ephemeral=True
        )

@bot.command(name='suggestban') 
async def suggest_ban_word(ctx, *, word: str):
    """Suggest a word to add to the banned words list"""
    channel = bot.get_channel(MODERATION_CHANNEL_ID)
    if channel:
        await channel.send(
            f"🔍 New word suggestion from {ctx.author}:\n"
            f"Word: `{word}`\n"
            f"Context: {ctx.message.reference.resolved.content if ctx.message.reference else 'No context provided'}"
        )
        await ctx.send("✅ Your suggestion has been submitted for review. Thank you!")
# Update the command to use the new check
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio

# Add this with your other global variables
GENERATION_COUNTER = defaultdict(list)
RATE_LIMIT = 2  # 2 generations
RATE_LIMIT_WINDOW = 60  # per 60 seconds

import aiohttp
import urllib.parse
import io
import time
from discord import app_commands

# Rate limiting
GENERATION_COUNTER = {}
RATE_LIMIT = 2  # 2 generations
RATE_LIMIT_WINDOW = 60  # per 60 seconds

async def generate_image(prompt: str, model: str = "turbo"):
    """Generate an image using Pollinations AI"""
    # Encode the prompt for the URL
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?model={model}&width=1024&height=1024&nologo=true"
    
    # Download the image from Pollinations
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.read()
            else:
                raise Exception(f"API returned status {response.status}")

# Slash command
from contextlib import nullcontext  # Add this at the top with other imports

# Slash command
@bot.tree.command(name="generate", description="Generate an image using AI")
@app_commands.describe(
    prompt="The text prompt to generate an image from",
    model="The model to use (turbo or flux)"
)
async def generate_slash(interaction: discord.Interaction, prompt: str, model: str = "turbo"):
    """Generate an image using AI (slash command)"""
    # Check for banned words
    prompt_lower = prompt.lower()
    for word in BANNED_WORDS:
        if word in prompt_lower:
            print(f"Blocked prompt containing banned word: {word}")
            await interaction.response.send_message(
                "❌ This prompt contains content that violates our guidelines.",
                ephemeral=True
            )
            return
    
    # Validate model
    model = model.lower()
    if model not in ["turbo", "flux"]:
        await interaction.response.send_message(
            "❌ Invalid model. Please use 'turbo' or 'flux'.",
            ephemeral=True
        )
        return
    
    # Defer the response to prevent timeout
    await interaction.response.defer(thinking=True)
    
    # Call the shared handler
    await handle_generate(interaction, prompt, model)

@bot.command(name='generate', aliases=['photo', 'pic', 'imagine'])
async def generate_prefix(ctx, *, prompt: str):
    """Generate an image using AI (prefix command)"""
    # For prefix commands, we use the default 'turbo' model
    await handle_generate(ctx, prompt)

# Add this near the top with other constants
BANNED_WORDS = [
    # Nudity and explicit content
    "nsfw", "naked", "nude", "nudity", "nudist", "naturist", "bikini", "lingerie", "underwear", "panties",
    "topless", "bottomless", "cleavage", "upskirt", "downblouse", "explicit", "xxx", "porn", "porno", "pornography",
    "hentai", "ecchi", "r34", "rule34", "lewds", "lewd", "suggestive", "provocative", "seductive", "erotic",
    
    # Body parts (explicit)
    "breasts", "boobs", "tits", "titties", "nipples", "areola", "areolas", "cleavage", "clevage", "clev",
    "vagina", "pussy", "pussies", "vulva", "labia", "clit", "clitoris", "penis", "dick", "cock", "dildo", "dicks", 
    "cocks", "balls", "testicles", "testes", "scrotum", "ass", "asshole", "arse", "arsehole", "butt", "buttocks",
    "anus", "anal", "butthole", "rectum", "bum", "bums", "booty", "twerking", "thong", "g-string", "gstring", "skin",
    
    # Sexual content
    "sex", "sexual", "sexy", "sexuality", "intercourse", "fuck", "fucking", "fucker", "fucked", "fucks",
    "screw", "screwing", "screwed", "screws", "fellate", "fellatio", "blowjob", "blow job", "handjob", "hand job",
    "bj", "hj", "orgasm", "orgasmic", "orgasms", "masturbat", "jerk off", "jerkoff", "jacking off", "wank",
    "wanking", "wanker", "ejaculat", "cum", "semen", "sperm", "creampie", "cream pie", "cowgirl", "doggy style",
    "missionary", "69", "sixty nine", "sixtynine", "kamasutra", "kama sutra", "kinky", "bdsm", "bondage", "domination",
    "submission", "submissive", "dominant", "domme", "dom", "sub", "slave", "master", "mistress", "fetish",
    
    # Violence and gore
    "gore", "gory", "blood", "bloody", "violence", "violent", "brutal", "brutality", "torture", "torturing",
    "mutilat", "decapitat", "behead", "beheading", "dismember", "dismemberment", "cannibal", "cannibalism",
    "snuff", "snuff film", "snuff movie", "guro", "gurokawa", "ryona", "vore", "scat", "scatology", "coprophilia",
    
    # Common misspellings and variations
    "pron", "p0rn", "pr0n", "porn0", "p0rn0", "pr0n0", "porn0graphy", "p0rn0graphy", "pr0n0graphy",
    "secks", "s3x", "s3xy", "sexy", "sexe", "sexi", "sexii", "sexiii", "sexiiii", "sexiiiii",
    "fuk", "fuking", "fukin", "fuker", "fuked", "fukkin", "fukking", "fukn", "fukr", "fukw",
    "d1ck", "d1ckhead", "d1ckwad", "d1ckface", "d1ckhead", "d1ckwad", "d1ckface",
    "penis", "dick", "boobs", "vagina", "pussy", "ass", "nude", "token",
    "testicales", "testicle", "testes", "genital", "breast", "butt", "buttock", "backshots",
    # Common bypass attempts
    "p0rn", "s3x", "s3xy", "a$$", "@$$", "b00b", "b00bs", "v4g1n4",
    # Common misspellings
    "t3st1cl3s", "t3st1cl3", "t3st1c13s", "t3st1c1e5", "t3st1c135",
    "t35t1cl35", "t35t1cl3", "t35t1c13s", "t35t1c1e5", "t35t1c135"
]

async def handle_generate(context, prompt: str, model: str = "turbo"):
    """Handle both slash and prefix commands"""
    # Check for banned words (works for both slash and prefix commands)
    prompt_lower = prompt.lower()
    # Split the prompt into words and check each one
    prompt_words = prompt_lower.split()
    
    for word in BANNED_WORDS:
        # Check if the banned word appears as a whole word in the prompt
        if any(word == w or f"{word}s" == w or f"{word}es" == w or f"{word}ed" == w for w in prompt_words):
            print(f"Blocked prompt containing banned word: {word}")
            if hasattr(context, 'response') and not context.response.is_done():
                await context.response.send_message(
                    "❌ This prompt contains content that violates our guidelines.",
                    ephemeral=True
                )
            else:
                await context.send("❌ This prompt contains content that violates our guidelines.")
            return
            
    # Rate limiting
    current_time = time.time()
    user_id = str(getattr(context, 'author', getattr(context, 'user')).id)
    
    # Get or initialize user's generation timestamps
    user_timestamps = [t for t in GENERATION_COUNTER.get(user_id, []) 
                      if current_time - t < RATE_LIMIT_WINDOW]
    
    if len(user_timestamps) >= RATE_LIMIT:
        remaining = int(RATE_LIMIT_WINDOW - (current_time - user_timestamps[0]))
        msg = f"⏱️ Rate limited! Please wait {remaining} seconds before generating another image."
        if hasattr(context, 'response') and not context.response.is_done():
            await context.response.send_message(msg, ephemeral=True)
        else:
            await context.send(msg)
        return
    
    # Update rate limit
    GENERATION_COUNTER[user_id] = user_timestamps + [current_time]
    
    # Show typing indicator
    async with context.typing() if hasattr(context, 'typing') else nullcontext():
        try:
            # Defer for slash commands
            if hasattr(context, 'response') and not context.response.is_done():
                await context.response.defer(thinking=True)
            
            # Generate the image
            image_data = await generate_image(prompt, model)
            
            # Create and send the image
            file = discord.File(io.BytesIO(image_data), filename='generated.png')
            embed = discord.Embed(title=f"🎨 Generated: {prompt[:100]}")
            embed.set_image(url="attachment://generated.png")
            embed.set_footer(text=f"Model: {model} | Pollinations.ai")
            
            # Send response based on context
            if hasattr(context, 'followup'):
                await context.followup.send(embed=embed, file=file)
            else:
                await context.send(embed=embed, file=file)
                
        except Exception as e:
            error_msg = f"⚠️ Error generating image: {str(e)}"
            print(f"Error in generate command: {e}")
            if hasattr(context, 'followup'):
                await context.followup.send(error_msg, ephemeral=True)
            elif hasattr(context, 'response') and not context.response.is_done():
                await context.response.send_message(error_msg, ephemeral=True)
            else:
                await context.send(error_msg)
    
# Create the FastAPI app
app = FastAPI()

@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok"}

def run_web():
    # Try multiple ports starting from the configured one
    base_port = int(os.environ.get("PORT", 10000))
    max_attempts = 5
    for attempt in range(max_attempts):
        port = base_port + attempt
        try:
            print(f"[WEB] Starting web server on port {port}...")
            uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
            break
        except OSError as e:
            if "Address already in use" in str(e) or "Only one usage" in str(e):
                if attempt < max_attempts - 1:
                    print(f"[WEB] Port {port} in use, trying {port + 1}...")
                    continue
            print(f"[WEB] Error starting server on port {port}: {e}")
            break

@bot.tree.command(name='say', description='Make the bot say something in the current channel')
@app_commands.describe(message='The message to send')
@app_commands.checks.has_permissions(manage_messages=True)
async def say_message(interaction: discord.Interaction, message: str):
    """Make the bot say something in the current channel"""
    try:
        # Acknowledge the interaction first
        await interaction.response.send_message("Message sent!", ephemeral=True, delete_after=3)
        
        # Delete the command message if possible
        try:
            if interaction.message:
                await interaction.message.delete()
        except:
            pass  # If deletion fails, continue anyway
            
        # Send the message to the channel
        await interaction.channel.send(message)
        
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I don't have permission to send messages in this channel.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(
            f"❌ Failed to send message: {e}",
            ephemeral=True
        )

@bot.tree.command(name='sayin', description='Make the bot say something in a specific channel')
@app_commands.describe(
    channel='The channel to send the message to',
    message='The message to send'
)
@app_commands.checks.has_permissions(manage_messages=True)
async def say_in_channel(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    """Make the bot say something in a specific channel"""
    try:
        # Check if the bot has permission to send messages in the target channel
        if not channel.permissions_for(interaction.guild.me).send_messages:
            await interaction.response.send_message(
                f"❌ I don't have permission to send messages in {channel.mention}.",
                ephemeral=True
            )
            return
            
        # Acknowledge the interaction first
        await interaction.response.send_message(
            f"Message sent to {channel.mention}!",
            ephemeral=True,
            delete_after=5
        )
        
        # Delete the command message if possible
        try:
            if interaction.message:
                await interaction.message.delete()
        except:
            pass  # If deletion fails, continue anyway
            
        # Send the message to the specified channel
        await channel.send(message)
        
    except Exception as e:
        await interaction.followup.send(
            f"❌ Failed to send message: {e}",
            ephemeral=True
        )

@bot.command(name='schedule')
@commands.has_permissions(manage_messages=True)
async def schedule_message(ctx, when: str, *, message: str):
    """Schedule a message to be sent later
    
    Examples:
    !schedule 15m Hello in 15 minutes
    !schedule 1h30m Reminder in 1 hour and 30 minutes
    !schedule 2d1h5m Big announcement in 2 days, 1 hour, and 5 minutes
    """
    try:
        # Parse time string (e.g., 1h30m, 15m, 2d1h5m)
        time_units = {'d': 86400, 'h': 3600, 'm': 60, 's': 1}
        seconds = 0
        num_str = ''
        
        for char in when.lower():
            if char.isdigit():
                num_str += char
            elif char in time_units:
                if num_str:
                    seconds += int(num_str) * time_units[char]
                    num_str = ''
        
        if seconds <= 0:
            await ctx.send("Please specify a valid time (e.g., 15m, 1h30m, 1d12h)")
            return
        
        # Calculate the target time
        target_time = datetime.now() + timedelta(seconds=seconds)
        
        # Add to scheduled messages
        bot.scheduled_messages.append({
            'channel_id': ctx.channel.id,
            'content': message,
            'time': target_time
        })
        
        await ctx.send(f"✅ Message scheduled for {target_time.strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        await ctx.send(f"❌ Error scheduling message: {e}")

async def send_scheduled_messages():
    """Background task to send scheduled messages"""
    await bot.wait_until_ready()
    
    while not bot.is_closed():
        now = datetime.now()
        
        # Check and send scheduled messages
        for msg in bot.scheduled_messages[:]:
            if now >= msg['time']:
                try:
                    channel = bot.get_channel(msg['channel_id'])
                    if channel:
                        await channel.send(msg['content'])
                    # Remove the sent message from the schedule
                    bot.scheduled_messages.remove(msg)
                except Exception as e:
                    print(f"Error sending scheduled message: {e}")
        
        # Sleep for 1 minute before checking again
        await asyncio.sleep(60)

@bot.event
async def setup_hook():
    # Start the scheduled messages task
    bot.loop.create_task(send_scheduled_messages())

# Create the FastAPI app
app = FastAPI()
@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok"}
def run_web():
    # Try multiple ports starting from the configured one
    base_port = int(os.environ.get("PORT", 10000))
    max_attempts = 5
    for attempt in range(max_attempts):
        port = base_port + attempt
        try:
            print(f"[WEB] Starting web server on port {port}...")
            uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
            break
        except OSError as e:
            if "Address already in use" in str(e) or "Only one usage" in str(e):
                if attempt < max_attempts - 1:
                    print(f"[WEB] Port {port} in use, trying {port + 1}...")
                    continue
            print(f"[WEB] Error starting server on port {port}: {e}")
            break

async def sync_commands():
    """Helper function to sync commands"""
    try:
        # Sync global commands
        synced = await bot.tree.sync()
        
        # Also sync for the specific guild for faster updates during development
        guild = discord.Object(id=1440330105799839856)  # Replace with your guild ID
        bot.tree.copy_global_to(guild=guild)
        synced_guild = await bot.tree.sync(guild=guild)
        
        print(f'[BOT] Synced {len(synced)} global commands')
        print(f'[BOT] Synced {len(synced_guild)} guild commands')
        return True
    except Exception as e:
        print(f'[BOT] Error syncing commands: {e}')
        return False

async def main():
    # 1. Start web server in background thread
    import threading
    threading.Thread(target=run_web, daemon=True).start()
    
    # 2. Get the bot token
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print("❌ Error: DISCORD_BOT_TOKEN environment variable not set")
        exit(1)
    
    # 3. Start the bot
    print("[BOT] Starting bot...")
    try:
        # Start the bot
        async with bot:
            print("[BOT] Bot is starting...")
            await bot.start(token)
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

# Add an event to sync commands when the bot is ready
@bot.event
async def on_ready():
    print(f"[BOT] Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")
    
    try:
        # Always sync global commands
        synced = await bot.tree.sync()
        print(f'[BOT] Synced {len(synced)} global commands')
        
        # Try to sync guild commands if in the specified guild
        guild_id = 1440330105799839856  # Your guild ID
        guild = bot.get_guild(guild_id)
        
        if guild:
            try:
                bot.tree.copy_global_to(guild=discord.Object(id=guild_id))
                synced_guild = await bot.tree.sync(guild=discord.Object(id=guild_id))
                print(f'[BOT] Synced {len(synced_guild)} guild commands for {guild.name}')
            except Exception as e:
                print(f'[BOT] Warning: Could not sync guild commands: {e}')
        else:
            print(f'[BOT] Not in guild with ID {guild_id}, skipping guild command sync')
            
        print("[BOT] Bot is ready!")
        
    except Exception as e:
        print(f'[BOT] Error syncing commands: {e}')
        import traceback
        traceback.print_exc()

# Add signal handling for graceful shutdown
def signal_handler(sig, frame):
    print('\nShutting down gracefully...')
    # Add any cleanup code here if needed
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handlers for clean shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Run the main bot function
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Bot has been shut down")

