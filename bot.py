from telethon import TelegramClient, events
import asyncio
import re
import os
import signal
import sys

# Get credentials from environment variables (more secure)
api_id = int(os.getenv('API_ID', 20328439))
api_hash = os.getenv('API_HASH', '80cfea2e51a960220d14ec3e2317bda6')

# Initialize client with Render-optimized settings
client = TelegramClient(
    session="render_session",
    api_id=api_id,
    api_hash=api_hash,
    connection_retries=10,
    retry_delay=5,
    timeout=60,
    device_model="Render Bot",
    system_version="1.0",
    app_version="1.0"
)

# Target chat ID
target_chat_id = -1003333433940

# Keep track of challenge state
challenge_active = {}

# Graceful shutdown handler
def signal_handler(signum, frame):
    print("🛑 Received shutdown signal...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

@client.on(events.NewMessage(chats=[target_chat_id]))
async def handler(event):
    chat_id = event.chat_id
    
    # Check if someone challenged you (Jitesh)
    if 'has challenged' in event.raw_text and 'Jitesh' in event.raw_text:
        print("🎯 Battle challenge detected!")
        challenge_active[chat_id] = {
            'state': 'waiting_for_ready',
            'message_id': event.id
        }
        # Start processing this challenge
        await process_challenge(event, chat_id)
        return

async def process_challenge(event, chat_id):
    """Process the battle challenge step by step"""
    max_wait_time = 30
    check_interval = 2
    
    if challenge_active[chat_id]['state'] == 'waiting_for_ready':
        print("🔄 Step 1: Looking for Ready button...")
        
        for attempt in range(max_wait_time // check_interval):
            try:
                message = await client.get_messages(chat_id, ids=challenge_active[chat_id]['message_id'])
                
                if message and message.buttons:
                    ready_button_text = find_ready_button(message.buttons)
                    if ready_button_text:
                        print(f"✅ Clicking Ready button: {ready_button_text}")
                        await message.click(text=ready_button_text)
                        challenge_active[chat_id]['state'] = 'in_battle'
                        print("⚔️ Battle started! Waiting for battle buttons...")
                        await asyncio.create_task(monitor_battle_buttons(chat_id))
                        return
                
                print("⏳ Ready button not available yet, waiting...")
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                print(f"❌ Error waiting for Ready button: {e}")
                await asyncio.sleep(check_interval)
        
        print("❌ Timeout waiting for Ready button")
        challenge_active[chat_id] = {}

def find_ready_button(buttons):
    """Find Ready button with different emoji formats"""
    ready_patterns = [
        "Ready ✅", "Ready✅", "Ready", "Ready ✔️", "Ready✔️",
    ]
    
    for row in buttons:
        for button in row:
            button_text = button.text.strip()
            for pattern in ready_patterns:
                if pattern in button_text:
                    return button_text
    return None

async def monitor_battle_buttons(chat_id):
    """Monitor and click battle buttons"""
    print("🎮 Battle monitor started...")
    
    while challenge_active.get(chat_id, {}).get('state') == 'in_battle':
        try:
            async for message in client.iter_messages(chat_id, limit=10):
                if message.buttons:
                    await handle_battle_buttons(message, chat_id)
                    break
            
            await asyncio.sleep(3)
            
        except Exception as e:
            print(f"❌ Error in battle monitor: {e}")
            await asyncio.sleep(3)

async def handle_battle_buttons(message, chat_id):
    """Handle battle buttons with priority: numbers > Double Edge"""
    if not message.buttons:
        return
    
    # Priority 1: Number buttons
    for row in message.buttons:
        for button in row:
            text = button.text.strip()
            clean_text = re.sub(r'[^\d]', '', text)
            
            if clean_text in ["1", "2", "3", "4", "5", "6"]:
                print(f"🔢 Clicking number button: {text}")
                try:
                    await message.click(text=text)
                    print(f"✅ Successfully clicked {text}")
                    await asyncio.sleep(2)
                    return
                except Exception as e:
                    print(f"❌ Failed to click {text}: {e}")
    
    # Priority 2: Double Edge
    double_edge_patterns = [
        "Double Edge", "Double Edge ⚔️", "Double Edge⚔️", 
        "Double-Edge", "Double-Edge ⚔️"
    ]
    
    for row in message.buttons:
        for button in row:
            button_text = button.text.strip()
            for pattern in double_edge_patterns:
                if pattern in button_text:
                    print(f"⚔️ Clicking Double Edge: {button_text}")
                    try:
                        await message.click(text=button_text)
                        print("✅ Successfully clicked Double Edge")
                        await asyncio.sleep(2)
                        return
                    except Exception as e:
                        print(f"❌ Failed to click Double Edge: {e}")

@client.on(events.MessageEdited(chats=[target_chat_id]))
async def edited_handler(event):
    """Handle edited messages"""
    chat_id = event.chat_id
    
    if challenge_active.get(chat_id):
        if (challenge_active[chat_id].get('state') == 'waiting_for_ready' and 
            event.id == challenge_active[chat_id].get('message_id')):
            ready_button_text = find_ready_button(event.buttons)
            if ready_button_text:
                print(f"✅ Clicking Ready button from edited message: {ready_button_text}")
                await event.click(text=ready_button_text)
                challenge_active[chat_id]['state'] = 'in_battle'
                print("⚔️ Battle started! Waiting for battle buttons...")
                await asyncio.create_task(monitor_battle_buttons(chat_id))
        
        elif challenge_active[chat_id].get('state') == 'in_battle' and event.buttons:
            await handle_battle_buttons(event, chat_id)

@client.on(events.NewMessage(pattern='/stop_battle', chats=[target_chat_id]))
async def stop_handler(event):
    """Stop the battle automation with command"""
    chat_id = event.chat_id
    if challenge_active.get(chat_id):
        challenge_active[chat_id] = {}
        print("🛑 Battle automation stopped by command")

@client.on(events.NewMessage(pattern='/status', chats=[target_chat_id]))
async def status_handler(event):
    """Check bot status"""
    await event.reply("🤖 Bot is running and monitoring for challenges!")

async def main():
    """Main function with Render compatibility"""
    print("🚀 Battle Bot Starting on Render...")
    print("📋 Features:")
    print("   • Auto-detect challenges to 'Jitesh'")
    print("   • Click Ready button (handles ✅ emoji with/without space)")
    print("   • Auto-battle with number buttons (1-6)")
    print("   • Fallback to Double Edge if numbers not available")
    print("   • Continuous monitoring during battle")
    print("   • Type /stop_battle to stop automation")
    
    try:
        await client.start()
        print("✅ Connected to Telegram successfully!")
        print("🤖 Bot is now running...")
        
        # Get bot info
        me = await client.get_me()
        print(f"🔗 Logged in as: {me.first_name} (@{me.username})")
        
        # Keep the bot running
        await client.run_until_disconnected()
        
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
