from telethon import TelegramClient, events
import asyncio
import re

# Replace with your values from https://my.telegram.org
api_id = 20328439
api_hash = '80cfea2e51a960220d14ec3e2317bda6'

# Session file (saved locally after first login)
client = TelegramClient("my_session", api_id, api_hash)

# Target chat ID
target_chat_id = -1003333433940

# Keep track of challenge state
challenge_active = {}

@client.on(events.NewMessage(chats=[target_chat_id]))
async def handler(event):
    chat_id = event.chat_id
    
    # Check if someone challenged you (Jitesh)
    if 'has challenged' in event.raw_text:
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
    max_wait_time = 30  # Maximum seconds to wait for buttons
    check_interval = 2  # Check every 2 seconds
    
    if challenge_active[chat_id]['state'] == 'waiting_for_ready':
        print("🔄 Step 1: Looking for Ready button...")
        
        # Wait for Ready button to appear
        for attempt in range(max_wait_time // check_interval):
            try:
                # Get the latest version of the message
                message = await client.get_messages(chat_id, ids=challenge_active[chat_id]['message_id'])
                
                if message and message.buttons:
                    # Look for Ready button with different formats
                    ready_button_text = find_ready_button(message.buttons)
                    if ready_button_text:
                        print(f"✅ Clicking Ready button: {ready_button_text}")
                        await message.click(text=ready_button_text)
                        challenge_active[chat_id]['state'] = 'in_battle'
                        print("⚔️ Battle started! Waiting for battle buttons...")
                        # Start monitoring battle buttons
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
        "Ready ✅",      # With space and tick
        "Ready✅",       # Without space
        "Ready",         # Just text
        "Ready ✔️",      # With different tick
        "Ready✔️",       # Without space different tick
    ]
    
    for row in buttons:
        for button in row:
            button_text = button.text.strip()
            # Check if button text matches any ready pattern
            for pattern in ready_patterns:
                if pattern in button_text:
                    return button_text
    
    return None

async def monitor_battle_buttons(chat_id):
    """Monitor and click battle buttons (numbers or Double Edge)"""
    print("🎮 Battle monitor started...")
    
    while challenge_active.get(chat_id, {}).get('state') == 'in_battle':
        try:
            # Get recent messages to find battle messages with buttons
            async for message in client.iter_messages(chat_id, limit=10):
                if message.buttons:
                    await handle_battle_buttons(message, chat_id)
                    break
            
            await asyncio.sleep(3)  # Check every 3 seconds
            
        except Exception as e:
            print(f"❌ Error in battle monitor: {e}")
            await asyncio.sleep(3)

async def handle_battle_buttons(message, chat_id):
    """Handle battle buttons with priority: numbers > Double Edge"""
    if not message.buttons:
        return
    
    # Priority 1: Look for number buttons (1,2,3,4,5,6)
    for row in message.buttons:
        for button in row:
            text = button.text.strip()
            
            # Clean text for comparison (remove emojis/spaces)
            clean_text = re.sub(r'[^\d]', '', text)  # Keep only numbers
            
            if clean_text in ["1", "2", "3", "4", "5", "6"]:
                print(f"🔢 Clicking number button: {text}")
                try:
                    await message.click(text=text)
                    print(f"✅ Successfully clicked {text}")
                    await asyncio.sleep(2)  # Wait after clicking
                    return
                except Exception as e:
                    print(f"❌ Failed to click {text}: {e}")
    
    # Priority 2: Look for Double Edge button (handle different formats)
    double_edge_patterns = [
        "Double Edge",
        "Double Edge ⚔️",
        "Double Edge⚔️",
        "Double-Edge",
        "Double-Edge ⚔️"
    ]
    
    for row in message.buttons:
        for button in row:
            button_text = button.text.strip()
            
            # Check if button text matches any Double Edge pattern
            for pattern in double_edge_patterns:
                if pattern in button_text:
                    print(f"⚔️ Clicking Double Edge: {button_text}")
                    try:
                        await message.click(text=button_text)
                        print("✅ Successfully clicked Double Edge")
                        await asyncio.sleep(2)  # Wait after clicking
                        return
                    except Exception as e:
                        print(f"❌ Failed to click Double Edge: {e}")

@client.on(events.MessageEdited(chats=[target_chat_id]))
async def edited_handler(event):
    """Handle edited messages (important for battle updates)"""
    chat_id = event.chat_id
    
    if challenge_active.get(chat_id):
        # If we're waiting for ready and this is our challenge message
        if (challenge_active[chat_id].get('state') == 'waiting_for_ready' and 
            event.id == challenge_active[chat_id].get('message_id')):
            ready_button_text = find_ready_button(event.buttons)
            if ready_button_text:
                print(f"✅ Clicking Ready button from edited message: {ready_button_text}")
                await event.click(text=ready_button_text)
                challenge_active[chat_id]['state'] = 'in_battle'
                print("⚔️ Battle started! Waiting for battle buttons...")
                await asyncio.create_task(monitor_battle_buttons(chat_id))
        
        # If we're in battle and this message has buttons, handle them
        elif challenge_active[chat_id].get('state') == 'in_battle' and event.buttons:
            await handle_battle_buttons(event, chat_id)

@client.on(events.NewMessage(pattern='/stop_battle', chats=[target_chat_id]))
async def stop_handler(event):
    """Stop the battle automation with command"""
    chat_id = event.chat_id
    if challenge_active.get(chat_id):
        challenge_active[chat_id] = {}
        print("🛑 Battle automation stopped by command")

print("🚀 Battle Bot Started!")
print("📋 Features:")
print("   • Auto-detect challenges to 'Jitesh'")
print("   • Click Ready button (handles ✅ emoji with/without space)")
print("   • Auto-battle with number buttons (1-6)")
print("   • Fallback to Double Edge if numbers not available")
print("   • Continuous monitoring during battle")
print("   • Type /stop_battle to stop automation")

client.start()
client.run_until_disconnected()