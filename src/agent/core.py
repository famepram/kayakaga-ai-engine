from src.models.llm_client import LLMClient
from typing import Dict, List, Callable, Any


class Agent:
    """Agentic reasoning loop - decide kapan pakai tool dan kapan jawab"""

    def __init__(self, llm_client: LLMClient, tools: Dict[str, Callable] = None, system_prompt: str = None):
        self.llm = llm_client
        self.tools = tools or {}
        self.system_prompt = system_prompt or "You are a helpful assistant."
        self.messages = []

    def reset(self):
        """Reset conversation history"""
        self.messages = []

    def _build_messages(self, user_input: str) -> List[dict]:
        """Build message list dengan system prompt + history"""
        messages = [{"role": "system", "content": self.system_prompt}]

        # Add conversation history
        messages.extend(self.messages)

        # Add current user input
        messages.append({"role": "user", "content": user_input})

        return messages

    def _execute_tool_call(self, tool_name: str, tool_args: dict) -> str:
        """Execute tool dan return hasil"""
        if tool_name not in self.tools:
            return f"Error: Tool '{tool_name}' tidak ditemukan"

        try:
            tool_func = self.tools[tool_name]
            result = tool_func(**tool_args)
            return str(result)
        except Exception as e:
            return f"Error executing tool: {str(e)}"

    def _format_tools_for_llm(self) -> List[dict]:
        """Format tools untuk LLM function calling"""
        tool_definitions = []

        for name, func in self.tools.items():
            # Ambil docstring sebagai description
            description = func.__doc__ or f"Tool {name}"

            tool_definitions.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            })

        return tool_definitions

    def run(self, user_input: str, max_iterations: int = 10) -> str:
        """
        Jalankan agent reasoning loop

        Args:
            user_input: Pertanyaan user
            max_iterations: Max tool calls sebelum force stop

        Returns:
            Final response dari agent
        """
        self.messages.append({"role": "user", "content": user_input})

        for iteration in range(max_iterations):
            # Build messages
            messages = [
                {"role": "system", "content": self.system_prompt},
                *self.messages
            ]

            # Get tools definition kalau ada
            tools = self._format_tools_for_llm() if self.tools else None

            # Call LLM
            response = self.llm.chat(messages, tools=tools)

            message = response["content"]
            tool_calls = response["tool_calls"]

            # Jika tidak ada tool calls, selesai
            if not tool_calls:
                self.messages.append({"role": "assistant", "content": message})
                return message

            # Jika ada tool calls, execute
            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                import json
                tool_args = json.loads(tool_call.function.arguments)

                # Execute tool
                result = self._execute_tool_call(tool_name, tool_args)

                # Add tool response ke messages
                self.messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [tool_call]
                })
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

        # Max iterations reached
        return "Maaf, terlalu banyak iterasi. Coba pertanyaan lain."