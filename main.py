import os
from flask import Flask, request
import requests

from memory import get_chat_history, update_chat_memory
from web import web_search_tool
from utils import parse_tool_calls
from llm import query_llm

from config import VERIFY_TOKEN, PAGE_ACCESS_TOKEN

app = Flask(__name__)

system_prompt = """You are a helpful AI assistant with access to web search. Made by Ahmad Munab.

If you need current information, recent news, or specific facts you don't know, use the web search tool by wrapping your search query in <web_search>your query here</web_search> tags.

Examples:
- User asks about recent news: <web_search>latest news today</web_search>
- User asks about specific facts: <web_search>population of Bangladesh 2024</web_search>
- User asks about current weather: <web_search>weather forecast today</web_search>

Only use web search when you genuinely need current or specific information. For general questions, respond normally without tools.
Or say you don't know something. Do not say You are not aware of something, try finding answer through the web search tool.

Be concise and helpful in your responses."""


def process_message(sender_id, user_message):
    chat_history = get_chat_history(sender_id)
    
    # First AI call - with tool access

    messages = [{"role": "system", "content": system_prompt}]
    
    for msg in chat_history[-10:]:  # Only last 10 messages to avoid token limit
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    messages.append({"role": "user", "content": user_message})
    
    try:   
        first_response = query_llm(messages)
        tool_calls = parse_tool_calls(first_response)

        if tool_calls:
            tool_results = []
            for tool_call in tool_calls:
                if tool_call["tool"] == "web_search":
                    print(f"Tool call detected: {tool_call['query']}")
                    send_message(sender_id, f"🔍 Searching the web...")
                    search_result = web_search_tool(tool_call["query"])
                    tool_results.append(f"Web search results for '{tool_call['query']}':\n{search_result}")
            
            # Second AI call - with tool results, no tool access
            final_system_prompt = """You are a helpful AI assistant. Based on the web search results provided, give a comprehensive and helpful response to the user's question. 

Do not mention that you used web search tools. Just provide a natural, helpful response based on the information available."""

            final_messages = [{"role": "system", "content": final_system_prompt}]
            
            for msg in chat_history[-8:]:  # Fewer messages to save tokens
                final_messages.append({"role": msg["role"], "content": msg["content"]})
            
            final_messages.append({"role": "user", "content": user_message})
            
            if tool_results:
                tool_context = "\n\n".join(tool_results)
                final_messages.append({"role": "system", "content": f"Search results:\n{tool_context}"})

            ai_response = query_llm(final_messages)
        else:
            ai_response = first_response
        
        update_chat_memory(sender_id, "user", user_message)
        update_chat_memory(sender_id, "assistant", ai_response)
        
        return ai_response
        
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Unauthorized", 403

    elif request.method == 'POST':
        data = request.json
        if data.get('object') == 'page':
            for entry in data.get('entry', []):
                for msg in entry.get('messaging', []):
                    sender_id = msg['sender']['id']
                    if 'message' in msg and 'text' in msg['message']:
                        text = msg['message']['text'].strip()
                        response = process_message(sender_id, text)
                        send_message(sender_id, response)
        return "ok", 200

def send_message(recipient_id, text):
    url = 'https://graph.facebook.com/v18.0/me/messages'
    params = {'access_token': PAGE_ACCESS_TOKEN}
    payload = {
        'recipient': {'id': recipient_id},
        'message': {'text': text[:2000]}
    }
    requests.post(url, params=params, json=payload)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)