def parse_response(response_text):
    """Parse AI response for tool calls, say messages, and task completion"""
    result = {
        "tools": [],
        "say_message": None,
        "task_finished": None,
        "continue_task": True
    }
    
    # Extract say_in_middle message first
    if "<say_in_middle>" in response_text and "</say_in_middle>" in response_text:
        start = response_text.find("<say_in_middle>") + len("<say_in_middle>")
        end = response_text.find("</say_in_middle>")
        if start < end:
            result["say_message"] = response_text[start:end].strip()
            # Remove the processed tag for cleaner tool parsing
            response_text = response_text[:start-len("<say_in_middle>")] + response_text[end+len("</say_in_middle>"):]
    
    # Parse web search tool calls
    while "<web_search>" in response_text and "</web_search>" in response_text:
        start = response_text.find("<web_search>") + len("<web_search>")
        end = response_text.find("</web_search>")
        if start < end:
            query = response_text[start:end].strip()
            result["tools"].append({"tool": "web_search", "query": query})
            # Remove the processed tag
            response_text = response_text[:start-len("<web_search>")] + response_text[end+len("</web_search>"):]

    # Parse browse url tool calls
    while "<browse_url>" in response_text and "</browse_url>" in response_text:
        start = response_text.find("<browse_url>") + len("<browse_url>")
        end = response_text.find("</browse_url>")
        if start < end:
            url = response_text[start:end].strip()
            result["tools"].append({"tool": "browse_url", "url": url})
            # Remove the processed tag
            response_text = response_text[:start-len("<browse_url>")] + response_text[end+len("</browse_url>"):]
    
    # Clean remaining text
    remaining_text = response_text.strip()
    
    # If there are no tools and no progress message, this is a final response
    if not result["tools"] and not result["say_message"] and remaining_text:
        result["task_finished"] = remaining_text
        result["continue_task"] = False
    # If there are tools but also remaining text, keep it for the next iteration
    elif result["tools"] and remaining_text:
        result["task_finished"] = remaining_text
        result["continue_task"] = True

    return result

def parse_tool_calls(response_text):
    """Parse tool calls from AI response"""
    return parse_response(response_text)["tools"]