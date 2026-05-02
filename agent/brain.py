"""
Finai Agent Brain
Core agentic loop implementing ReAct pattern for Finai personal finance advisor
"""

import json
import os
from typing import Dict, List, Optional
from openai import OpenAI
from dotenv import load_dotenv
import httpx

from .prompts import build_system_prompt, _load_user_context
from .tools import TOOL_DEFINITIONS, TOOL_HANDLERS

load_dotenv()


class FinaiAgent:
    """
    Finai Agent - Personal Finance Advisor AI
    Implements ReAct pattern: Thought → Action → Observation → Answer
    """

    def __init__(self, model: str = None, base_url: str = None, api_key: str = None):
        """Initialize Finai Agent with LLM client"""
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

        # Load user context
        self.user_context = _load_user_context()
        self.system_prompt = build_system_prompt(self.user_context)

        # Conversation history
        self.conversation_history = []

    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []
        print("💬 Conversation history cleared")

    def _execute_tool(self, tool_name: str, tool_input: Dict) -> str:
        """
        Execute tool dan return hasil sebagai string

        Args:
            tool_name: Nama tool yang akan diexecute
            tool_input: Parameter untuk tool

        Returns:
            String result dari tool execution
        """
        if tool_name not in TOOL_HANDLERS:
            return json.dumps({
                "error": f"Tool '{tool_name}' tidak ditemukan",
                "available_tools": list(TOOL_HANDLERS.keys())
            }, ensure_ascii=False)

        try:
            # Call tool handler
            tool_func = TOOL_HANDLERS[tool_name]
            result = tool_func(**tool_input)

            # Return as JSON string
            return json.dumps(result, ensure_ascii=False, default=str)

        except Exception as e:
            return json.dumps({
                "error": f"Tool execution failed: {str(e)}",
                "tool_name": tool_name,
                "input": tool_input
            }, ensure_ascii=False)

    def _print_tool_call(self, tool_name: str, tool_input: Dict):
        """Print tool call ke console untuk debugging"""
        input_str = json.dumps(tool_input, ensure_ascii=False)
        if len(input_str) > 100:
            input_str = input_str[:100] + "..."

        print(f"  🔧 [TOOL] {tool_name}({input_str})")

    def _print_tool_result(self, result: str):
        """Print tool result ke console untuk debugging"""
        result_json = json.loads(result)
        if "error" in result_json:
            print(f"  ❌ [ERROR] {result_json.get('error', 'Unknown error')}")
        else:
            # Print summary based on tool result
            if "transactions" in result_json:
                count = result_json.get("count", 0)
                total_out = result_json.get("total_out", 0)
                print(f"  ✅ [RESULT] {count} transaksi, total: Rp {total_out:,.0f}")
            elif "accounts" in result_json:
                count = result_json.get("account_count", 0)
                total = result_json.get("total_balance", 0)
                print(f"  ✅ [RESULT] {count} akun, total: Rp {total:,.0f}")
            elif "future_value" in result_json:
                future_val = result_json.get("future_value", 0)
                profit = result_json.get("profit", 0)
                print(f"  ✅ [RESULT] Future value: Rp {future_val:,.0f}, profit: Rp {profit:,.0f}")
            elif "goals" in result_json:
                count = result_json.get("total_goals", 0)
                completed = result_json.get("completed_goals", 0)
                print(f"  ✅ [RESULT] {count}/{completed} goals completed")
            elif "suggested_category" in result_json:
                category = result_json.get("suggested_category", "unknown")
                confidence = result_json.get("confidence_level", "Low")
                print(f"  ✅ [RESULT] Category: {category} ({confidence} confidence)")
            else:
                print(f"  ✅ [RESULT] Success")

    def run(self, user_message: str, verbose: bool = True) -> str:
        """
        Jalankan agent reasoning loop

        Args:
            user_message: Pesan dari user
            verbose: Print tool calls ke console

        Returns:
            Final response dari agent
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Agentic loop
        max_iterations = 10
        for iteration in range(max_iterations):
            try:
                # Build messages for LLM
                messages = [
                    {"role": "system", "content": self.system_prompt},
                    *self.conversation_history
                ]

                # Call LLM with tools
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=TOOL_DEFINITIONS,
                    temperature=0.7,
                    max_tokens=2000
                )

                # Get assistant message
                assistant_message = response.choices[0].message
                content = assistant_message.content
                tool_calls = assistant_message.tool_calls

                # Check if agent finished
                if not tool_calls:
                    # Agent selesai, return final answer
                    if content:
                        self.conversation_history.append({
                            "role": "assistant",
                            "content": content
                        })
                        return content
                    else:
                        return "Maaf, saya tidak dapat memberikan respons."

                # Agent wants to use tools
                if tool_calls:
                    # Add assistant message with tool calls to history
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": content or None,
                        "tool_calls": tool_calls
                    })

                    # Execute all tool calls
                    tool_results = []
                    for tool_call in tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)

                        # Print tool call if verbose
                        if verbose:
                            self._print_tool_call(tool_name, tool_args)

                        # Execute tool
                        result = self._execute_tool(tool_name, tool_args)

                        # Print result if verbose
                        if verbose:
                            self._print_tool_result(result)

                        # Add tool result to message history
                        tool_results.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result
                        })

                    # Add tool results to conversation history
                    self.conversation_history.extend(tool_results)

                    # Loop continues - agent processes tool results

            except Exception as e:
                error_msg = f"Error dalam agentic loop: {str(e)}"
                if verbose:
                    print(f"  ❌ {error_msg}")
                return f"Maaf, terjadi error: {error_msg}"

        # Max iterations reached
        return "Maaf, saya memerlukan terlalu banyak langkah untuk menjawab pertanyaan ini. Coba pertanyaan lain yang lebih spesifik."

    def run_with_thinking(self, user_message: str) -> str:
        """
        Jalankan agent dengan menampilkan proses berpikir
        """
        print(f"\n🤖 Finai sedang berpikir...")
        print("=" * 50)

        result = self.run(user_message, verbose=True)

        print("=" * 50)
        return result


# For testing
if __name__ == "__main__":
    try:
        agent = FinaiAgent()
        print("✅ Finai Agent initialized")
        print(f"📝 Model: {agent.model}")
        print(f"👤 User: {agent.user_context.get('profile', {}).get('name', 'Unknown')}")

        # Test simple question
        test_message = "Halo, saya mau tanya tentang keuangan saya"
        print(f"\n👤 User: {test_message}")
        response = agent.run_with_thinking(test_message)
        print(f"\n🤖 Finai: {response}\n")

    except Exception as e:
        print(f"❌ Error: {e}")