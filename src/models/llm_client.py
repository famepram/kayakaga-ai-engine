from openai import OpenAI
from dotenv import load_dotenv
import os
import httpx

load_dotenv()


class LLMClient:
    """Wrapper untuk OpenRouter API menggunakan OpenAI SDK"""

    def __init__(self, api_key: str = None, model: str = None, base_url: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = model or os.getenv("MODEL", "anthropic/claude-3.5-sonnet:beta")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY tidak ditemukan")

        # Create HTTP client dengan SSL verification disabled
        http_client = httpx.Client(verify=False)

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            http_client=http_client
        )

    def chat(self, messages: list[dict], tools: list[dict] = None) -> dict:
        """
        Kirim chat completion request ke OpenRouter

        Args:
            messages: List of message dicts with role and content
            tools: Optional list of tool definitions for function calling

        Returns:
            Response dict dengan message, tool_calls, dll
        """
        kwargs = {
            "model": self.model,
            "messages": messages
        }

        if tools:
            kwargs["tools"] = tools

        response = self.client.chat.completions.create(**kwargs)

        return {
            "content": response.choices[0].message.content,
            "tool_calls": response.choices[0].message.tool_calls,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }