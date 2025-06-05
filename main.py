import os
import requests
from flask import Flask, request
from groq import Groq
from urllib.parse import quote
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY") 
print("VERIFY_TOKEN:", VERIFY_TOKEN)
print("PAGE_ACCESS_TOKEN:", PAGE_ACCESS_TOKEN)
print("GROQ_API_KEY:", GROQ_API_KEY)

groq_client = Groq(api_key=GROQ_API_KEY)

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
                        handle_command(sender_id, text)
        return "ok", 200

def handle_command(sender_id, text):
    if text.lower().startswith("ai "):
        prompt = text[3:].strip()
        reply = ask_ai(prompt)
        send_message(sender_id, reply)
    elif text.lower().startswith("web "):
        query = text[4:].strip()
        reply = do_web_search(query)
        send_message(sender_id, reply)
    else:
        send_message(sender_id, "Unrecognized command. Use:\nai <your question>\nweb <your search>")

def ask_ai(prompt):
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            tools=None,
            tool_choice="none",
            temperature=0.33,
            max_tokens=1024,
            top_p=1,
            stop=None,
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        return f"AI error: {str(e)}"

def do_web_search(query):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        search_url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
        res = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        results = soup.select(".result__snippet")

        if not results:
            return "No results found."

        lines = [f"🔍 **{query}**"]
        for result in results[:3]:
            snippet = result.get_text(strip=True)
            if snippet:
                lines.append(f"- {snippet}")

        return "\n".join(lines)
    except Exception as e:
        return f"Web error: {str(e)}"

def send_message(recipient_id, text):
    url = 'https://graph.facebook.com/v18.0/me/messages'
    params = {'access_token': PAGE_ACCESS_TOKEN}
    print("Sending message to:", recipient_id, "Text:", text)
    payload = {
        'recipient': {'id': recipient_id},
        'message': {'text': text[:2000]} 
    }
    requests.post(url, params=params, json=payload)

if __name__ == '__main__':
    app.run(port=5000, debug=True)
