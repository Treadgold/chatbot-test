import time
from typing import Any, Dict, List, Optional

import requests


class RunPodLLM:
    """A minimal wrapper around a RunPod endpoint that mimics LangChain's LLM invoke interface.

    The class sends a prompt to the `/run` endpoint, polls the `/status/{id}` endpoint
    until the job is completed, then extracts and returns the generated text.
    """

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        poll_interval: float = 1.0,
        timeout: float = 120.0,  # Increased from 60 to 120 seconds
        temperature: float | None = 0.7,
        max_tokens: int | None = 512,
        top_p: float | None = 0.9,
        repetition_penalty: float | None = 1.1,
    ) -> None:
        """Args:
        endpoint: Base URL of the RunPod endpoint *without* a trailing slash, e.g.
                  ``"https://api.runpod.ai/v2/abcd1234"```.
        api_key:  RunPod API key ("Bearer …").
        poll_interval: Seconds between status polls (default: 1.0).
        timeout: Max seconds to wait for job completion (default: 60.0).
        temperature: Sampling temperature for text generation (default: 0.7).
        max_tokens: Maximum tokens to generate (default: 512).
        top_p: Top-p sampling parameter (default: 0.9).
        repetition_penalty: Penalty for repeated tokens (default: 1.1).
        """
        if endpoint.endswith("/"):
            endpoint = endpoint[:-1]
        self.endpoint = endpoint
        self.api_key = api_key
        self.poll_interval = poll_interval
        self.timeout = timeout

        # Improved generation parameters
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.repetition_penalty = repetition_penalty

    # ---------------------------------------------------------------------
    # Public LLM-like interface
    # ---------------------------------------------------------------------
    def invoke(self, prompt: str, config: Optional[Dict[str, Any]] | None = None) -> str:
        """Synchronously generate a completion for *prompt*.

        The *config* argument is accepted for API compatibility but is currently
        ignored (the caller usually passes ``{"format": …}``).
        """
        job_id = self._submit_job(prompt)
        output = self._wait_for_completion(job_id)
        return self._extract_text(output)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def _submit_job(self, prompt: str) -> str:
        """Submit the prompt and return the RunPod job ID."""
        # Build sampling parameters with improved defaults
        sampling_params: Dict[str, Any] = {}
        if self.temperature is not None:
            sampling_params["temperature"] = self.temperature
        if self.max_tokens is not None:
            sampling_params["max_tokens"] = self.max_tokens
        if self.top_p is not None:
            sampling_params["top_p"] = self.top_p
        if self.repetition_penalty is not None:
            sampling_params["repetition_penalty"] = self.repetition_penalty
        
        # Add stop sequences to prevent runaway generation
        sampling_params["stop"] = ["\n\nUser:", "\n\nHuman:", "\n\nAssistant:", "</s>", "<|im_end|>"]

        # Format prompt properly for better vLLM inference
        formatted_prompt = self._format_prompt(prompt)
        
        payload = {
            "input": {
                "prompt": formatted_prompt,
                "sampling_params": sampling_params
            }
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        response = requests.post(
            f"{self.endpoint}/run",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        return response.json()["id"]
    
    def _format_prompt(self, prompt: str) -> str:
        """Format the prompt for better vLLM inference.
        
        This model seems to work better with very simple, direct roleplay instructions.
        We'll completely rewrite complex prompts into simple character instructions.
        """
        # If the prompt already looks like it has chat formatting, use as-is
        if any(marker in prompt.lower() for marker in ["[inst]", "<s>", "system:", "user:", "assistant:"]):
            return prompt
        
        # For any prompt mentioning Scottish madman, create a simple roleplay instruction
        if "scottish" in prompt.lower() and "madman" in prompt.lower():
            # Try to extract the actual user message
            user_message = "Hello there!"  # default
            
            # Look for various patterns to extract the user's actual message
            if "user message:" in prompt.lower():
                parts = prompt.split("User message:")
                if len(parts) > 1:
                    msg_part = parts[1].strip()
                    # Get the first sentence/phrase
                    user_message = msg_part.split('.')[0].split('!')[0].split('?')[0].strip()
            elif "hello" in prompt.lower():
                user_message = "Hello there!"
            elif "think about:" in prompt.lower():
                parts = prompt.split("Think about:")
                if len(parts) > 1:
                    msg_part = parts[1].strip()
                    user_message = msg_part.split('.')[0].split('!')[0].split('?')[0].strip()
            
            # Create a simple, direct roleplay instruction
            formatted = f"""Roleplay as an angry Scottish man trapped inside a computer. You are short-tempered and swear frequently. A user says: "{user_message}". Reply in character with 1-2 short sentences. Be grumpy and Scottish."""
            return formatted
        
        # For everything else, return as-is
        return prompt

    def _wait_for_completion(self, job_id: str) -> Any:
        """Poll the job until it completes and return the *output* field."""
        status_url = f"{self.endpoint}/status/{job_id}"
        start_time = time.time()
        
        while True:
            if time.time() - start_time > self.timeout:
                raise TimeoutError(f"RunPod job {job_id} timed out after {self.timeout} seconds")
                
            resp = requests.get(status_url, headers=self._headers(), timeout=30)
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status")
            
            if status == "COMPLETED":
                return data.get("output")
            if status in {"FAILED", "CANCELLED", "ERROR"}:
                raise RuntimeError(f"RunPod job {job_id} failed: {data}")
            # Otherwise, keep waiting (statuses: IN_QUEUE, IN_PROGRESS, STARTED)
            time.sleep(self.poll_interval)

    def _extract_text(self, output: Any) -> str:
        """Best-effort extraction of generated text from RunPod *output*."""
        # The exact shape depends on the model container. Common patterns are
        # shown below and handled heuristically.
        if isinstance(output, list) and output:
            first = output[0]
            if isinstance(first, dict):
                # Pattern 1: {"choices": [{"tokens": ["word", ]}]}
                choices = first.get("choices")
                if choices and isinstance(choices, list):
                    tokens = choices[0].get("tokens")
                    if tokens and isinstance(tokens, list):
                        return "".join(tokens)
                    text = choices[0].get("text")
                    if isinstance(text, str):
                        return text
                # Pattern 2: {"text": ""}
                text_val = first.get("text")
                if isinstance(text_val, str):
                    return text_val
            # Fallback: stringify first element.
            return str(first)
        # Fallback: stringify entire output.
        return str(output)
