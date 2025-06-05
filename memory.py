import os, json
from datetime import datetime
from config import MEMORY_FILE, MAX_MEMORY

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_memory(memory):
    with open(MEMORY_FILE, 'w') as f:
        json.dump(memory, f, indent=2)

def update_chat_memory(sender_id, role, content):
    memory = load_memory()
    if sender_id not in memory:
        memory[sender_id] = []
    
    memory[sender_id].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })
    
    # Keep only last MAX_MEMORY messages
    if len(memory[sender_id]) > MAX_MEMORY:
        memory[sender_id] = memory[sender_id][-MAX_MEMORY:]
    
    save_memory(memory)

def get_chat_history(sender_id):
    memory = load_memory()
    return memory.get(sender_id, [])