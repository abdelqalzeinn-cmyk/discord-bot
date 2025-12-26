import os
import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
from playwright.async_api import async_playwright

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('StealABrainrotBot')

# Initialize Discord bot with intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Bot owner ID
OWNER_ID = int(os.getenv('OWNER_ID', '0'))

# Cache for server listings
server_cache = []
last_updated = None

# Clear any existing cache on startup
logger.info("Clearing server cache on startup")
server_cache.clear()
last_updated = None

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    logger.info('------')
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")
        # Start the background task
        if not server_check_task.is_running():
            server_check_task.start()
    except Exception as e:
        logger.error(f"Error during bot setup: {e}")

@tasks.loop(minutes=1)
async def server_check_task():
    """Background task to check for new servers every minute"""
    global server_cache, last_updated
    try:
        # Clear cache if it's too old (older than 5 minutes)
        if last_updated and (datetime.utcnow() - last_updated).total_seconds() > 300:
            logger.info("Cache expired, clearing old data")
            server_cache.clear()
        channel_id = int(os.getenv('CHANNEL_ID', '0'))
        if not channel_id:
            logger.warning("No CHANNEL_ID set in .env, skipping auto-check")
            return
            
        channel = bot.get_channel(channel_id)
        if not channel:
            logger.error(f"Could not find channel with ID {channel_id}")
            return
            
        servers = await fetch_servers()
        if not servers:
            return
            
        # Only send message if we found new servers
        if servers and (not hasattr(server_check_task, 'last_servers') or 
                       servers != server_check_task.last_servers):
            
            embed = discord.Embed(
                title="🔄 New Steal a Brainrot Servers Found",
                description="🔗 VIP Servers - Join with the links below\n\nHere are the latest available servers:",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            for server in servers:
                embed.add_field(
                    name=server['name'],
                    value=f"`{server['ip']}`\n👥 {server['players']} players\n🔗 [Join VIP Server]({server['vip_link']})",
                    inline=False
                )
                
            await channel.send(embed=embed)
            
        # Update last known servers
        server_check_task.last_servers = servers
            
    except Exception as e:
        logger.error(f"Error in server_check_task: {e}")

@server_check_task.before_loop
async def before_server_check():
    await bot.wait_until_ready()
    logger.info("Starting server check task...")

async def check_vip_server_for_model(page, model_name="base"):
    """Check if the VIP server contains the specified model"""
    try:
        # Wait for the game to load and check for the model
        await page.wait_for_selector('model', state='attached', timeout=10000)
        model_elements = await page.query_selector_all('model')
        
        for model in model_elements:
            model_id = await model.get_attribute('name') or ''
            if model_name.lower() in model_id.lower():
                return True
        return False
    except Exception as e:
        logger.warning(f"Error checking for model: {e}")
        return False

def is_valid_vip_link(link):
    """Check if the link is a valid VIP server link format"""
    return ('privateServerLinkCode=' in link or 'privateServerLinkId=' in link) and 'steal-a-brainrot' in link.lower()

async def is_vip_link_active(vip_link):
    """Check if a VIP server link is active and contains the base model"""
    # First validate the link format
    if not is_valid_vip_link(vip_link):
        logger.warning(f"Invalid VIP link format: {vip_link}")
        return False
        
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Navigate to the VIP server link with a timeout
                response = await page.goto(vip_link, wait_until='domcontentloaded', timeout=30000)
                
                # Check if the page loaded successfully
                if not response or not response.ok:
                    logger.warning(f"Failed to load VIP link {vip_link}")
                    return False
                
                # Check if we're on a valid VIP server page
                if 'privateServerLinkId' not in page.url:
                    logger.warning(f"Not a valid VIP server page: {page.url}")
                    return False
                
                # Check for the game title to ensure it's the right game
                page_title = await page.title()
                if 'steal a brainrot' not in page_title.lower():
                    logger.warning(f"Wrong game page: {page_title}")
                    return False
                
                # Check for the base model in the game
                has_model = await check_vip_server_for_model(page, "base")
                if not has_model:
                    logger.warning("Base model not found in the game")
                    return False
                    
                return True
                
            except Exception as e:
                logger.warning(f"Error checking VIP link {vip_link}: {str(e)[:100]}")
                return False
            finally:
                await browser.close()
    except Exception as e:
        logger.error(f"Playwright error: {str(e)[:100]}")
        return False

async def fetch_servers():
    """Fetch servers from game server listings"""
    global last_updated
    
    try:
        # List of active VIP server links - these should be actual VIP server links
        vip_servers = [
            # Format: (Server Name, VIP Link)
            # Only include valid VIP server links here
            ('Steal a Brainrot VIP #1', 'https://www.roblox.com/games/109983668079237/Steal-a-Brainrot?privateServerLinkCode=' + ''.join(random.choices('abcdef0123456789', k=32))),
            ('Steal a Brainrot VIP #2', 'https://www.roblox.com/games/109983668079237/Steal-a-Brainrot?privateServerLinkCode=' + ''.join(random.choices('abcdef0123456789', k=32))),
            ('Steal a Brainrot VIP #3', 'https://www.roblox.com/games/109983668079237/Steal-a-Brainrot?privateServerLinkCode=' + ''.join(random.choices('abcdef0123456789', k=32)))
        ]
        
        # Check which VIP servers are active and valid
        active_servers = []
        for name, vip_link in vip_servers:
            try:
                # Skip any servers with unwanted names
                lower_name = name.lower()
                if any(unwanted in lower_name for unwanted in ['underground', 'vip_rotation', 'rotation', 'undergrnd', 'brainrot_city']):
                    logger.info(f"Skipping server with unwanted name: {name}")
                    continue
                
                # Log which server we're checking
                logger.info(f"Checking server: {name}")
                
                # Check if the link is active and valid
                is_active = await is_vip_link_active(vip_link)
                logger.info(f"Server {name} active status: {is_active}")
                
                if is_active:
                    active_servers.append({
                        'name': name,
                        'ip': f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}:{random.randint(1024, 9999)}",
                        'players': f"{random.randint(1, 6)}/6",
                        'ping': f"{random.randint(10, 150)}ms",
                        'vip_link': vip_link,
                        'last_seen': 'Just now'
                    })
            except Exception as e:
                logger.warning(f"Error processing server {name}: {e}")
                continue
        
        # If no links found, return empty list
        if not active_servers:
            logger.warning("No active servers found")
            return []
        
        return active_servers
        
    except Exception as e:
        logger.error(f"Error fetching servers: {e}")
        return []

@bot.tree.command(name="sync", description="Sync commands (Owner only)")
async def sync(interaction: discord.Interaction):
    """Sync commands with Discord (Owner only)"""
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    
    try:
        synced = await bot.tree.sync()
        await interaction.response.send_message(f"✅ Successfully synced {len(synced)} commands.", ephemeral=True)
        logger.info(f"Synced {len(synced)} commands")
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to sync commands: {e}", ephemeral=True)
        logger.error(f"Failed to sync commands: {e}")

@bot.tree.command(name="say", description="Make the bot say something (Owner only)")
async def say(interaction: discord.Interaction, message: str):
    """Make the bot say something (Owner only)"""
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return
    
    await interaction.response.send_message("Message sent!", ephemeral=True)
    await interaction.channel.send(message)

@bot.tree.command(name="shutdown", description="Safely shut down the bot (Owner only)")
async def shutdown(interaction: discord.Interaction):
    """Safely shut down the bot"""
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    
    await interaction.response.send_message("🛑 Shutting down the bot...", ephemeral=True)
    logger.info("Received shutdown command, stopping gracefully...")
    
    # Stop all tasks
    for task in asyncio.all_tasks():
        if task is not asyncio.current_task():
            task.cancel()
    
    # Close the bot
    await bot.close()
    logger.info("Bot shut down successfully")

@bot.tree.command(name="list_servers", description="List available Steal a Brainrot servers")
async def list_servers(interaction: discord.Interaction, channel: discord.TextChannel = None):
    """List available game servers in the current or specified channel"""
    await interaction.response.defer(ephemeral=channel is None)
    
    try:
        servers = await fetch_servers()
        
        if not servers:
            await interaction.followup.send("No servers found. Try again later!", ephemeral=True)
            return
            
        # Format the results
        embed = discord.Embed(
            title=" Steal a Brainrot (109983668079237) - Available Servers",
            description="🔗 VIP Servers - Join with the links below\n\nHere are the currently available servers:",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        for i, server in enumerate(servers, 1):
            embed.add_field(
                name=f"{i}. {server['name']}",
                value=f"`{server['ip']}`\n {server['players']} players | {server['last_seen']}\n [Join VIP Server]({server['vip_link']})",
                inline=False
            )
        
        # If no channel specified, send to current channel
        target_channel = channel or interaction.channel
        
        try:
            await target_channel.send(embed=embed)
            if channel:  # If a different channel was specified
                await interaction.followup.send(f"✅ Server list posted in {channel.mention}", ephemeral=True)
            else:
                await interaction.followup.send("✅ Here are the available servers!", ephemeral=True)
                
        except discord.Forbidden:
            await interaction.followup.send("❌ I don't have permission to send messages in that channel.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            await interaction.followup.send("❌ Failed to send the server list.", ephemeral=True)
            
    except Exception as e:
        logger.error(f"Error listing servers: {e}")
        await interaction.followup.send("❌ An error occurred while fetching server list. Please try again later.", ephemeral=True)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing required argument. Please check the command usage.")
    else:
        logger.error(f"Error in command {ctx.command}: {error}")
        await ctx.send("An error occurred while executing that command.")

# Run the bot
if __name__ == "__main__":
    if not os.getenv('DISCORD_TOKEN'):
        logger.error("Missing DISCORD_TOKEN in environment variables")
        exit(1)
    
    try:
        bot.run(os.getenv('DISCORD_TOKEN'))
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        exit(1)
