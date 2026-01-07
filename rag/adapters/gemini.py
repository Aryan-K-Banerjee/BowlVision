"""
Gemini LLM Adapter
Provides interface for Google Gemini API calls.
"""

import os
from typing import Optional
from google import genai
from google.genai import types


# Configure API key from environment
API_KEY = os.environ.get('GEMINI_API_KEY', '')


def configure(api_key: Optional[str] = None):
    """
    Configure the Gemini API with the provided key.
    
    Args:
        api_key: Optional API key. Uses environment variable if not provided.
    """
    global API_KEY
    key = api_key or API_KEY
    if not key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    API_KEY = key


def chat_completion(messages: list, model: str = "gemini-2.0-flash") -> str:
    """
    Send a chat completion request to Gemini.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        model: The Gemini model to use
        
    Returns:
        The assistant's response text
    """
    if not API_KEY:
        raise ValueError("Gemini API not configured. Call configure() first or set GEMINI_API_KEY.")
    
    # Create client
    client = genai.Client(api_key=API_KEY)
    
    # Combine system messages with first user message
    system_content = ""
    conversation_parts = []
    
    for msg in messages:
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        
        if role == 'system':
            # Gemini doesn't have explicit system messages, prepend to first user message
            system_content += content + "\n\n"
        elif role == 'user':
            if system_content:
                content = system_content + content
                system_content = ""
            conversation_parts.append(types.Content(
                role="user",
                parts=[types.Part.from_text(text=content)]
            ))
        elif role == 'assistant':
            conversation_parts.append(types.Content(
                role="model",
                parts=[types.Part.from_text(text=content)]
            ))
    
    # Generate response
    response = client.models.generate_content(
        model=model,
        contents=conversation_parts,
        config=types.GenerateContentConfig(
            temperature=0.7,
            top_p=0.9,
            max_output_tokens=2048,
        )
    )
    
    return response.text


def is_configured() -> bool:
    """Check if the API is properly configured."""
    return bool(API_KEY)
