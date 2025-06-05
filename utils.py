def parse_tool_calls(response_text):
    """Parse tool calls from AI response"""
    tools_used = []
    
    # Look for web search tool calls
    if "<web_search>" in response_text and "</web_search>" in response_text:
        start = response_text.find("<web_search>") + len("<web_search>")
        end = response_text.find("</web_search>")
        if start < end:
            query = response_text[start:end].strip()
            tools_used.append({"tool": "web_search", "query": query})
    
    return tools_used