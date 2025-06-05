import os
from flask import Flask, request
import requests
from typing import List, Dict, Optional

from memory import get_chat_history, update_chat_memory, clear_chat_memory
from web import web_search_tool
from browser import browse_website
from utils import parse_response
from llm import query_llm

from config import VERIFY_TOKEN, PAGE_ACCESS_TOKEN

app = Flask(__name__)

system_prompt = """You are a helpful AI assistant in a Facebook Messenger conversation. You have access to powerful tools to find accurate information.

Available Tools:
- Web Search: <web_search>your search query</web_search> - For finding general information
- Website Browser: <browse_url>URL</browse_url> - For reading specific webpage content
- Progress Update: <say_in_middle>message</say_in_middle> - For keeping user informed

CRITICAL RULES:
1. NEVER make statements without using tools to verify information
2. ONE TOOL AT A TIME - Never use multiple tools in one response
3. Always WAIT for tool results before continuing
4. Keep final responses CONCISE and CLEAR
5. Don't repeat yourself or send duplicate messages
6. After using a tool, process its results into a helpful response
(You will be prompted again with the tool results, so dont worry. do one step at a time)

Workflow:
1. When you need information:
   - Tell the user what you're doing with <say_in_middle>
   - Use ONE tool (<web_search> or <browse_url>)
   - Wait for the result
   - Then process that result into a helpful response

2. When responding:
   - Keep it short and clear
   - If you need more info, use another tool
   - Don't repeat yourself
   - Don't make up information

Example correct flow:
User: "Tell me about OpenAI"
Assistant: <say_in_middle>Let me search for information about OpenAI...</say_in_middle>
<web_search>OpenAI company latest information</web_search>
[System provides search results]
Assistant: Based on the search results, OpenAI is... [concise summary]

DO NOT do this:
- Don't use multiple tools at once
- Don't make claims without using tools
- Don't repeat the same search
- Don't give responses without tool results

MAKE SURE:
- The tools are used correctly
- Theres no spelling mistake in the tool tags.
- Responses are clear and concise
"""

def send_message(recipient_id: str, text: str) -> None:
    """Send message to Facebook user"""
    if not text or not text.strip():
        print(f"Warning: Attempted to send empty message to {recipient_id}")
        return
        
    try:
        clean_text = text.strip()
        
        if not clean_text:
            return
            
        url = 'https://graph.facebook.com/v18.0/me/messages'
        params = {'access_token': PAGE_ACCESS_TOKEN}
        payload = {
            'recipient': {'id': recipient_id},
            'message': {'text': clean_text[:2000]}
        }
        response = requests.post(url, params=params, json=payload)
        response.raise_for_status()
        print(f"Sent to {recipient_id}: {clean_text[:100]}...")
        
    except Exception as e:
        print(f"Error sending message to {recipient_id}: {str(e)}")

def execute_tool_call(tool_call: Dict[str, str]) -> Optional[str]:
    """Execute a single tool call and return the result"""
    try:
        if tool_call["tool"] == "web_search":
            query = tool_call.get("query", "").strip()
            if not query:
                return "Error: Search query was empty."
                
            print(f"Executing web search: {query}")
            result = web_search_tool(query)
            if result:
                return f"Search results for '{query}':\n{result}"
            else:
                return f"No search results found for '{query}'"
                
        elif tool_call["tool"] == "browse_url":
            url = tool_call.get("url", "").strip()
            if not url:
                return "Error: No URL provided."
                
            print(f"Browsing website: {url}")
            success, content = browse_website(url)
            if success and content:
                return f"Content from {url}:\n{content}"
            else:
                return f"Could not access content from {url}"
                
    except Exception as e:
        print(f"Tool execution error: {str(e)}")
        return f"Error executing tool: {str(e)}"
    
    return None

def process_message(sender_id: str, user_message: str) -> None:
    """Process user message with iterative responses"""
    try:
        print(f"Processing message from {sender_id}: {user_message}")
        
        if user_message == "/reset":
            clear_chat_memory(sender_id)
            send_message(sender_id, "Chat memory has been reset.")
            return

        # Get chat history
        chat_history = get_chat_history(sender_id)
        
        # Build conversation context
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent chat history including tool results for better context
        recent_history = chat_history[-8:] if chat_history else []
        for msg in recent_history:
            if msg.get("content") and msg.get("role") in ["user", "assistant"]:
                # Don't include progress messages in context
                if msg.get("type") != "message" or "Let me" not in msg["content"]:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        # Save user message to memory
        update_chat_memory(sender_id, "user", user_message)
        
        # Start iterative conversation
        max_iterations = 8  # Prevent infinite loops
        iteration = 0
        last_progress_message = None
        last_tool_result = None
        has_used_tool = False
        
        while iteration < max_iterations:
            iteration += 1
            print(f"Iteration {iteration}")
            
            # Get AI response
            ai_response = query_llm(messages)
            if not ai_response:
                send_message(sender_id, "I'm having trouble responding right now. Could you try again?")
                return
            
            print(f"AI Response: {ai_response}")
            
            # Parse response for tools and say_in_middle
            parsed = parse_response(ai_response)
            
            # Handle progress message (only if different from last one)
            if parsed.get("say_message") and parsed["say_message"] != last_progress_message:
                last_progress_message = parsed["say_message"]
                send_message(sender_id, parsed["say_message"])
                update_chat_memory(sender_id, "assistant", parsed["say_message"])
            
            # Execute tool calls one at a time
            if parsed.get("tools"):
                has_used_tool = True
                tool_call = parsed["tools"][0]  # Take only the first tool call
                tool_result = execute_tool_call(tool_call)
                
                if tool_result:
                    print(f"Tool result: {tool_result[:200]}...")
                    last_tool_result = tool_result
                    # Add tool result to conversation context
                    messages.append({"role": "assistant", "content": tool_result})
                    # Save tool result to memory
                    update_chat_memory(sender_id, "assistant", tool_result, tool_info={
                        "tool": tool_call["tool"],
                        "query": tool_call.get("query", tool_call.get("url", ""))
                    })
                    # Continue loop to process the tool result
                    continue
            
            # If we have a final response and no pending tool results, send it
            if parsed.get("task_finished"):
                final_response = parsed["task_finished"].strip()
                if final_response:
                    # Don't send duplicate responses
                    if final_response != last_progress_message:
                        # If we've used a tool, make sure we have processed its results
                        if not (has_used_tool and not last_tool_result):
                            send_message(sender_id, final_response)
                            update_chat_memory(sender_id, "assistant", final_response)
                            return
            
            # If we have a tool result but no final response yet, continue
            if last_tool_result:
                continue
            
            # If no tools used and no final response, try next iteration
            if not has_used_tool and not parsed.get("task_finished"):
                continue
        
        # If we hit max iterations, send a wrap-up message
        print("Hit max iterations, wrapping up")
        wrap_up_msg = "I've gathered some information but let me wrap this up. How else can I help you?"
        send_message(sender_id, wrap_up_msg)
        update_chat_memory(sender_id, "assistant", wrap_up_msg)
        
    except Exception as e:
        print(f"Error in process_message: {str(e)}")
        error_msg = "I'm sorry, I encountered an error. Could you try asking that again?"
        send_message(sender_id, error_msg)
        try:
            update_chat_memory(sender_id, "assistant", error_msg)
        except:
            pass

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # Webhook verification
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Unauthorized", 403

    elif request.method == 'POST':
        try:
            data = request.json
            if not data:
                return "No data received", 400
                
            if data.get('object') == 'page':
                for entry in data.get('entry', []):
                    for messaging_event in entry.get('messaging', []):
                        sender_id = messaging_event.get('sender', {}).get('id')
                        
                        if not sender_id:
                            continue
                            
                        # Handle text messages
                        if 'message' in messaging_event:
                            message = messaging_event.get('message', {})
                            text = message.get('text', '').strip()
                            
                            if not text:
                                continue
                            
                            print(f"Received message from {sender_id}: {text}")
                            process_message(sender_id, text)
                            
            return "ok", 200
            
        except Exception as e:
            print(f"Webhook error: {str(e)}")
            return "Error processing webhook", 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Bot is running"}, 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting bot on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)