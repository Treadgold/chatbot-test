import time
from typing import Any, Dict, List, Optional, Union

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
        model: str = "CognitiveComputations/dolphin-mistral-nemo:latest",
        poll_interval: float = 1.0,
        timeout: float = 0,  # No timeout - wait indefinitely
        temperature: Union[float, None] = 0.75,
        num_predict: Union[int, None] = 2048,  # Reduced from 1024 to 512
        top_p: Union[float, None] = 0.9,
        repetition_penalty: Union[float, None] = 1.1,
    ) -> None:
        """Args:
        endpoint: Base URL of the RunPod endpoint *without* a trailing slash, e.g.
                  ``"https://api.runpod.ai/v2/abcd1234"```.
        api_key:  RunPod API key ("Bearer …").
        model: Model name to use (default: "CognitiveComputations/dolphin-mistral-nemo:latest").
        poll_interval: Seconds between status polls (default: 1.0).
        timeout: Max seconds to wait for job completion (default: 120.0).
        temperature: Sampling temperature for text generation (default: 0.75).
        num_predict: Maximum tokens to generate (default: 1024).
        top_p: Top-p sampling parameter (default: 0.9).
        repetition_penalty: Penalty for repeated tokens (default: 1.1).
        """
        if endpoint.endswith("/"):
            endpoint = endpoint[:-1]
        self.endpoint = endpoint
        self.api_key = api_key
        self.model = model
        self.poll_interval = poll_interval
        self.timeout = timeout

        # Generation parameters
        self.temperature = temperature
        self.num_predict = num_predict
        self.top_p = top_p
        self.repetition_penalty = repetition_penalty

    # ---------------------------------------------------------------------
    # Public LLM-like interface
    # ---------------------------------------------------------------------
    def invoke(self, prompt: str, config: Optional[Dict[str, Any]] = None) -> str:
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
        # Build options with the format expected by the serverless endpoint
        options: Dict[str, Any] = {}
        if self.temperature is not None:
            options["temperature"] = self.temperature
        if self.num_predict is not None:
            options["num_predict"] = self.num_predict
        if self.top_p is not None:
            options["top_p"] = self.top_p
        if self.repetition_penalty is not None:
            options["repetition_penalty"] = self.repetition_penalty

        # Format the payload according to the user's specification
        payload = {
            "input": {
                "prompt": prompt,
                "model": self.model,
                "options": options
            }
        }

        response = requests.post(
            f"{self.endpoint}/run",
            json=payload,
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()["id"]

    def _wait_for_completion(self, job_id: str) -> Any:
        """Poll the job until it completes and return the *output* field."""
        status_url = f"{self.endpoint}/status/{job_id}"
        start_time = time.time()
        
        while True:
            # Only check timeout if timeout is greater than 0 (0 means wait indefinitely)
            if self.timeout > 0 and time.time() - start_time > self.timeout:
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
        # For Ollama-based endpoints, the output is typically a dict with a "response" field
        if isinstance(output, dict):
            # Try to extract from common Ollama response patterns
            if "response" in output:
                return output["response"]
            if "text" in output:
                return output["text"]
            if "content" in output:
                return output["content"]
        
        # Handle list output (multiple responses)
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
                # Pattern 3: {"response": ""} (Ollama format)
                response_val = first.get("response")
                if isinstance(response_val, str):
                    return response_val
            # Fallback: stringify first element.
            return str(first)
        
        # Fallback: stringify entire output.
        return str(output)

    # Additional methods to maintain compatibility with LangChain interface
    def __call__(self, prompt: str, **kwargs) -> str:
        """Alternative calling interface for compatibility."""
        return self.invoke(prompt)
    
    def predict(self, text: str) -> str:
        """Another compatibility method."""
        return self.invoke(text)
