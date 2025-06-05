import os, json
from datetime import datetime
from typing import List, Dict, Any
from config import MEMORY_FILE, MAX_MEMORY

def load_memory() -> Dict[str, List[Dict[str, Any]]]:
    """Load chat memory from file"""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error loading memory file: {str(e)}")
            return {}
    return {}

def save_memory(memory: Dict[str, List[Dict[str, Any]]]) -> None:
    """Save chat memory to file"""
    try:
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(memory, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving memory: {str(e)}")

def update_chat_memory(sender_id: str, role: str, content: str, tool_info: Dict = None) -> None:
    """
    Update chat memory for a specific sender
    
    :param sender_id: The unique identifier for the sender
    :param role: One of 'user' or 'assistant'
    :param content: The message content
    :param tool_info: Optional dictionary containing tool call information
    """
    try:
        memory = load_memory()
        if sender_id not in memory:
            memory[sender_id] = []
        
        # Add new message
        entry = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add tool information if provided
        if tool_info:
            entry["tool_info"] = tool_info
            entry["type"] = "tool_output"
        else:
            entry["type"] = "message"
        
        memory[sender_id].append(entry)
        
        # Keep only last MAX_MEMORY messages, but ensure we keep tool context pairs together
        if len(memory[sender_id]) > MAX_MEMORY:
            # Keep tool outputs with their corresponding messages
            filtered_memory = []
            tool_context = []
            
            for msg in memory[sender_id][-MAX_MEMORY*2:]:  # Look at more messages to ensure context
                if msg["role"] == "tool":
                    tool_context.append(msg)
                else:
                    if tool_context:  # Add accumulated tool context before the message
                        filtered_memory.extend(tool_context)
                        tool_context = []
                    filtered_memory.append(msg)
            
            # Add any remaining tool context
            if tool_context:
                filtered_memory.extend(tool_context)
                
            # Trim to MAX_MEMORY while keeping tool contexts
            memory[sender_id] = filtered_memory[-MAX_MEMORY:]
        
        save_memory(memory)
    except Exception as e:
        print(f"Error updating chat memory: {str(e)}")

def get_chat_history(sender_id: str) -> List[Dict[str, Any]]:
    """
    Get chat history for a specific sender
    
    :param sender_id: The unique identifier for the sender
    :return: List of chat messages with role and content
    """
    try:
        memory = load_memory()
        return memory.get(sender_id, [])
    except Exception as e:
        print(f"Error getting chat history: {str(e)}")
        return []