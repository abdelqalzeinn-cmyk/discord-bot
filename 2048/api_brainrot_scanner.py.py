import requests
import time
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
GAME_ID = "YOUR_GAME_ID"  # Replace with the actual game ID
DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK_URL')
SCAN_INTERVAL = 60  # seconds

def get_servers():
    """Fetch list of active servers"""
    url = f"https://games.roblox.com/v1/games/{GAME_ID}/servers/Public?limit=100"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get('data', [])
    except Exception as e:
        print(f"Error fetching servers: {e}")
    return []

def check_for_brainrots(server):
    """Check if server has any brainrots"""
    # This is where we'd check server data for brainrots
    # For now, we'll simulate finding some
    return ["Los Candies", "Bisonte Giuppitere"]  # Example matches

def send_discord_notification(server, brainrots):
    """Send notification to Discord"""
    if not DISCORD_WEBHOOK:
        print("No Discord webhook configured")
        return
        
    message = {
        "content": f"🚨 Found brainrots in server {server['id']}!",
        "embeds": [{
            "title": "Brainrots Found!",
            "description": "\n".join(f"- {name}" for name in brainrots),
            "color": 0x00ff00,
            "fields": [
                {"name": "Server ID", "value": server['id'], "inline": True},
                {"name": "Players", "value": f"{server.get('playing', 0)}/{server.get('maxPlayers', 0)}", "inline": True}
            ]
        }]
    }
    
    try:
        requests.post(DISCORD_WEBHOOK, json=message)
    except Exception as e:
        print(f"Error sending Discord notification: {e}")

def main():
    print("Starting brainrot scanner...")
    print(f"Scanning game: {GAME_ID}")
    print(f"Discord notifications: {'Enabled' if DISCORD_WEBHOOK else 'Disabled'}")
    
    while True:
        try:
            servers = get_servers()
            print(f"\nFound {len(servers)} servers. Scanning...")
            
            for server in servers:
                brainrots = check_for_brainrots(server)
                if brainrots:
                    print(f"Found brainrots in server {server['id']}: {', '.join(brainrots)}")
                    if DISCORD_WEBHOOK:
                        send_discord_notification(server, brainrots)
            
            print(f"Scan complete. Next scan in {SCAN_INTERVAL} seconds...")
            time.sleep(SCAN_INTERVAL)
            
        except KeyboardInterrupt:
            print("\nStopping scanner...")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(30)  # Wait before retrying

if __name__ == "__main__":
    main()