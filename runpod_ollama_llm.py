import time
import requests
from typing import Any, Dict, Optional


class RunPodOllamaLLM:
    """A wrapper that makes RunPod Ollama Serverless work with the existing OllamaLLM interface."""
    
    def __init__(
        self,
        endpoint: str,
        api_key: str,
        model: str = "dolphin-mistral-nemo:latest",
        poll_interval: float = 1.0,
        timeout: float = 300.0,  # 5 minutes for model download + generation
    ):
        """Initialize the RunPod Ollama LLM wrapper.
        
        Args:
            endpoint: RunPod serverless endpoint URL (e.g., "https://api.runpod.ai/v2/abc123")
            api_key: RunPod API key
            model: Ollama model name to use
            poll_interval: Seconds between status checks
            timeout: Maximum time to wait for completion
        """
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.poll_interval = poll_interval
        self.timeout = timeout
    
    def invoke(self, prompt: str, config: Optional[Dict[str, Any]] = None) -> str:
        """Generate a response using the RunPod Ollama serverless endpoint.
        
        This method provides the same interface as OllamaLLM.invoke()
        """
        try:
            # Prepare the payload for RunPod serverless
            payload = {
                "input": {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 500,  # Reasonable default
                    }
                }
            }
            
            # Submit job to RunPod
            job_id = self._submit_job(payload)
            
            # Wait for completion and get result
            result = self._wait_for_completion(job_id)
            
            # Extract the response text
            if isinstance(result, dict) and "response" in result:
                return result["response"]
            else:
                return str(result)
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _submit_job(self, payload: Dict[str, Any]) -> str:
        """Submit a job to RunPod serverless and return the job ID."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        response = requests.post(
            f"{self.endpoint}/run",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        response.raise_for_status()
        data = response.json()
        
        job_id = data.get("id")
        if not job_id:
            raise RuntimeError(f"No job ID returned: {data}")
        
        return job_id
    
    def _wait_for_completion(self, job_id: str) -> Any:
        """Poll for job completion and return the result."""
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        start_time = time.time()
        
        while time.time() - start_time < self.timeout:
            response = requests.get(
                f"{self.endpoint}/status/{job_id}",
                headers=headers,
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            status = data.get("status")
            
            if status == "COMPLETED":
                return data.get("output")
            elif status in ["FAILED", "CANCELLED", "TIMED_OUT"]:
                error_msg = data.get("error", f"Job {status.lower()}")
                raise RuntimeError(f"Job failed: {error_msg}")
            
            # Still running, wait before next check
            time.sleep(self.poll_interval)
        
        raise TimeoutError(f"Job {job_id} timed out after {self.timeout} seconds") 