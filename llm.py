from config import GROQ_API_KEY
from groq import Groq

groq_client = Groq(api_key=GROQ_API_KEY)

def query_llm(messages, model="meta-llama/llama-4-maverick-17b-128e-instruct", temperature=0.7, max_tokens=1024, top_p=1) -> str:
    """
    Query the LLM with the provided messages and parameters.
    
    :param messages: List of message dictionaries with 'role' and 'content'.
    :param model: The model to use for the query.
    :param temperature: Sampling temperature for response generation.
    :param max_tokens: Maximum number of tokens in the response.
    :param top_p: Top-p sampling parameter.
    :return: The content of the LLM's response.
    """
    chat_completion = groq_client.chat.completions.create(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p
    )
    
    return (chat_completion.choices[0].message.content or "").strip()