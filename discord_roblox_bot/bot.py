import discord
from discord.ext import commands
import aiohttp
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# In-memory storage (consider using a database for production)
favorites = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await bot.change_presence(activity=discord.Game(name="!help for commands"))

@bot.command(name='search')
async def search_roblox(ctx, *, query):
    """Search for Roblox items/games"""
    # This is a placeholder - in a real bot, you'd call the Roblox API here
    # For now, we'll just show an example response
    embed = discord.Embed(
        title=f"Search Results for '{query}'",
        description="🔍 Here are some results from Roblox:",
        color=0x00ff00
    )
    
    # Example results (replace with actual API calls)
    embed.add_field(
        name="Top Games",
        value="• [Adopt Me!](https://www.roblox.com/games/920587237/Adopt-Me)"
              "\n• [Brookhaven RP](https://www.roblox.com/games/4924922222/Brookhaven-RP)"
              "\n• [Tower of Hell](https://www.roblox.com/games/1962086868/Tower-of-Hell)",
        inline=False
    )
    
    embed.add_field(
        name="Top Items",
        value="• [Dominus Empyreus](https://www.roblox.com/catalog/4847429/Dominus-Empyreus)"
              "\n• [Korblox Deathspeaker](https://www.roblox.com/catalog/134967972/Korblox-Deathspeaker)",
        inline=False
    )
    
    embed.set_footer(text="Use !favorite [name] to save your favorites!")
    await ctx.send(embed=embed)

@bot.command(name='favorite')
async def add_favorite(ctx, *, item_name):
    """Add an item to your favorites"""
    user_id = str(ctx.author.id)
    if user_id not in favorites:
        favorites[user_id] = []
    
    if len(favorites[user_id]) >= 10:  # Limit to 10 favorites per user
        await ctx.send("❌ You've reached the maximum number of favorites (10). Remove some before adding more!")
        return
    
    if item_name.lower() in [f.lower() for f in favorites[user_id]]:
        await ctx.send("❌ This item is already in your favorites!")
        return
    
    favorites[user_id].append(item_name)
    await ctx.send(f"✅ Added '{item_name}' to your favorites!")

@bot.command(name='myfavorites')
async def show_favorites(ctx):
    """Show your favorite items"""
    user_id = str(ctx.author.id)
    if user_id not in favorites or not favorites[user_id]:
        await ctx.send("You haven't added any favorites yet! Use !favorite [item] to add some.")
        return
    
    fav_list = "\n".join(f"• {item}" for item in favorites[user_id])
    embed = discord.Embed(
        title=f"{ctx.author.name}'s Favorites",
        description=fav_list,
        color=0x3498db
    )
    await ctx.send(embed=embed)

# Run the bot
if __name__ == "__main__":
    TOKEN = os.getenv('DISCORD_TOKEN')
    if not TOKEN:
        print("Error: No Discord token found. Please create a .env file with DISCORD_TOKEN=your_token_here")
    else:
        bot.run(TOKEN)
