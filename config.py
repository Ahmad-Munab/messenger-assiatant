import os
from dotenv import load_dotenv

load_dotenv()

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
MEMORY_FILE = "chat_memory.json"
MAX_MEMORY = 15