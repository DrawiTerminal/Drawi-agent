"""Utility & helper functions."""

import os
from langchain_openai import ChatOpenAI, AzureChatOpenAI  # New import for Azure
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
import base58
import re


def get_message_text(msg: BaseMessage) -> str:
    """Get the text content of a message."""
    content = msg.content
    if isinstance(content, str):
        return content
    elif isinstance(content, dict):
        return content.get("text", "")
    else:
        txts = [c if isinstance(c, str) else (c.get("text") or "") for c in content]
        return "".join(txts).strip()


def load_chat_model(fully_specified_name: str) -> BaseChatModel:
    """Load a chat model from a fully specified name.

    Args:
        fully_specified_name (str): String in the format 'provider/model'.
    """
    provider, model = fully_specified_name.split("/", maxsplit=1)
    if provider.lower() == "azure":
        azure_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION")

        if not (azure_key and azure_endpoint):
            raise ValueError("Azure OpenAI credentials are not set in the environment.")
        return AzureChatOpenAI(
            azure_endpoint=azure_endpoint,
            azure_deployment=deployment_name,
            api_version=api_version,
            api_key=azure_key
        )
    else:
        return ChatOpenAI(
                model="gpt-4o",
                temperature=0,
                max_tokens=None,
                timeout=None,
                max_retries=2)


def extract_solana_addresses(text: str) -> set:
    """
    Extracts potential Solana addresses from text and validates them as base58.
    
    Parameters:
        text (str): The input text to search for Solana addresses.
    
    Returns:
        set: A set of unique, validated Solana addresses.
    """
    pattern = r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b"
    candidates = re.findall(pattern, text)
    valid_addresses = set()
    for candidate in candidates:
        try:
            decoded = base58.b58decode(candidate)
            if len(decoded) == 32:
                valid_addresses.add(candidate)
        except Exception:
            continue
    return valid_addresses
