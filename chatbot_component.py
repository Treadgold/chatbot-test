from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage
from langchain_ollama import OllamaLLM
from runpod_llm import RunPodLLM
from runpod_ollama_llm import RunPodOllamaLLM

from pydantic import BaseModel, Field
from typing import Literal, Optional

class Generated_Joke(BaseModel):
    joke: str = Field(description="The generated joke")
    num_words: int = Field(description="The number of words in the generated joke")

class Quality_Score(BaseModel):
    score: int = Field(description="The quality score of the joke from 0 to 1000. 0 is the worst, 1000 is the best")
    reason: str = Field(description="The reason for the quality score")

class Thought(BaseModel):
    thought: str = Field(description="The AI's internal thought process")
    reasoning: str = Field(description="The reasoning behind the thought")

class Response(BaseModel):
    response: str = Field(description="The AI's response to the user")
    tone: str = Field(description="The tone of the response (friendly, formal, casual, etc.)")

class State(TypedDict):
    thoughts: str
    plan: str
    action: str
    user_messages: list[HumanMessage]
    response: list[str]
    generated_joke: Generated_Joke
    quality_score: Quality_Score
    structured_thought: Thought
    structured_response: Response
    joke_iteration: int
    conversation_history: list[dict]  # Store conversation history

class ChatBotConfig:
    """Configuration class for the chatbot.

    Args:
        provider:   Which LLM backend to use. Options: ``"ollama"`` (default), ``"runpod"``, or ``"runpod_ollama"``.
        runpod_endpoint:  Base URL of the RunPod endpoint (e.g. ``https://api.runpod.ai/v2/<id>``);
                         only needed when *provider* is "runpod" or "runpod_ollama".
        runpod_api_key:   RunPod API key; only needed for "runpod" or "runpod_ollama".
    """

    def __init__(
        self,
        model_name: str = "dolphin-mistral-nemo:latest",
        base_url: str = "http://localhost:11434",
        max_iterations: int = 3,
        min_joke_score: int = 800,
        principles: str = """You are a lazy computer program who will make up answers, and doesn't check anything.""",
        provider: str = "ollama",
        runpod_endpoint: str | None = None,
        runpod_api_key: str | None = None,
    ):
        self.model_name = model_name
        self.base_url = base_url
        self.max_iterations = max_iterations
        self.min_joke_score = min_joke_score
        self.principles = principles

        # LLM backend selection
        self.provider = provider.lower()
        self.runpod_endpoint = runpod_endpoint
        self.runpod_api_key = runpod_api_key

class ChatBot:
    """A reusable chatbot component with LangGraph-based conversation flow"""
    
    def __init__(self, config: Optional[ChatBotConfig] = None):
        self.config = config or ChatBotConfig()
        self._setup_llms()
        self._setup_graph()
    
    def _setup_llms(self):
        """Initialize the LLM instances based on configuration."""
        if self.config.provider == "ollama":
            self.llm = OllamaLLM(model=self.config.model_name, base_url=self.config.base_url)
            self.quality_score_llm = OllamaLLM(model=self.config.model_name, base_url=self.config.base_url)
            self.joke_writer_llm = OllamaLLM(model=self.config.model_name, base_url=self.config.base_url)
        elif self.config.provider == "runpod":
            if not self.config.runpod_endpoint or not self.config.runpod_api_key:
                raise ValueError("RunPod endpoint and API key must be provided when provider='runpod'.")
            self.llm = RunPodLLM(endpoint=self.config.runpod_endpoint, api_key=self.config.runpod_api_key)
            # Re-use the same RunPod client for all LLM calls
            self.quality_score_llm = self.llm
            self.joke_writer_llm = self.llm
        elif self.config.provider == "runpod_ollama":
            if not self.config.runpod_endpoint or not self.config.runpod_api_key:
                raise ValueError("RunPod endpoint and API key must be provided when provider='runpod_ollama'.")
            self.llm = RunPodOllamaLLM(
                endpoint=self.config.runpod_endpoint, 
                api_key=self.config.runpod_api_key,
                model=self.config.model_name
            )
            # Re-use the same RunPod Ollama client for all LLM calls
            self.quality_score_llm = self.llm
            self.joke_writer_llm = self.llm
        else:
            raise ValueError(f"Unsupported LLM provider: {self.config.provider}")
    
    def _format_conversation_history(self, history: list[dict]) -> str:
        """Format conversation history for inclusion in prompts"""
        if not history:
            return "This is the start of the conversation."
        
        formatted = "Previous conversation:\n"
        for i, exchange in enumerate(history[-5:], 1):  # Only include last 5 exchanges
            formatted += f"{i}. User: {exchange['user']}\n"
            formatted += f"   AI: {exchange['ai']}\n"
        formatted += "\nCurrent message:"
        return formatted
    
    def _setup_graph(self):
        """Setup the LangGraph conversation flow"""
        builder = StateGraph(State)
        
        # Add nodes
        builder.add_node("process_thought", self._process_thought)
        builder.add_node("generate_response", self._generate_response)
        builder.add_node("consider_principles", self._consider_principles)
        builder.add_node("generate_joke", self._generate_joke)
        builder.add_node("score_joke", self._score_joke)
        builder.add_node("combine_response_with_joke", self._combine_response_with_joke)
        
        # Define the graph flow
        builder.add_edge(START, "process_thought")
        builder.add_edge("process_thought", "generate_response")
        builder.add_edge("generate_response", "consider_principles")
        builder.add_edge("consider_principles", END)
        # builder.add_edge("consider_principles", "generate_joke")
        # builder.add_edge("generate_joke", "score_joke")
        
        # # Add conditional edge for joke improvement loop
        # builder.add_conditional_edges(
        #     "score_joke",
        #     self._should_continue_improving_joke,
        #     {
        #         "improve_joke": "generate_joke",
        #         "end": "combine_response_with_joke"
        #     }
        # )
        
        # # Add final edge to END
        # builder.add_edge("combine_response_with_joke", END)
        
        # Compile the graph
        self.graph = builder.compile()
    
    def _invoke_llm(self, prompt: str, model_cls: type[BaseModel] | None = None):
        """Invoke the underlying LLM and optionally parse structured JSON.

        If *model_cls* is provided **and** the current provider is not "runpod" or "runpod_ollama",
        we will request structured output via model_cls.model_json_schema() and
        attempt to parse. For RunPod providers we fall back to plain text because most
        vLLM workers or custom handlers may not support LangChain's format spec.
        """
        if model_cls and self.config.provider not in ["runpod", "runpod_ollama"]:
            raw = self.llm.invoke(prompt, config={"format": model_cls.model_json_schema()})
            try:
                # Check if raw is already a model instance
                if isinstance(raw, model_cls):
                    return raw
                # Otherwise try to parse as JSON
                return model_cls.model_validate_json(raw)
            except Exception:
                return raw  # caller will handle fallback
        else:
            # Plain text path – just return raw string
            return self.llm.invoke(prompt)
    
    def _process_thought(self, state: State) -> State:
        """Process user input and generate structured thoughts"""
        # Use the LLM to generate a structured thought based on the user's message
        user_message = state['user_messages'][-1].content
        conversation_history = state.get('conversation_history', [])
        
        # Format conversation context
        context = self._format_conversation_history(conversation_history)
        
        # Build prompt. If provider is runpod or runpod_ollama, ask for plain text; otherwise ask for JSON.
        if self.config.provider in ["runpod", "runpod_ollama"]:
            prompt = (
                f"{context}\nThink about: {user_message}. Make a judgement on whether the user has views that align with you principles:{self.config.principles}. "
                "Provide your thoughts in plain English, two short sentences."
            )
        else:
            prompt = (
                f"{context}\nThink about: {user_message}. Make a judgement on whether the user has views that align with you principles:{self.config.principles}. If you feel they are 'your kind of people', you will be kind and friendly. However, if they seem to have opposite principles, you will interpret their comments in a negative light. Consider the conversation history and provide your thoughts as JSON with fields: thought (string) and reasoning (string)."
            )

        thought_response = self._invoke_llm(prompt, Thought if self.config.provider not in ["runpod", "runpod_ollama"] else None)

        # If we requested structured output and got a Thought instance, use it; otherwise fallback to raw string
        if isinstance(thought_response, Thought):
            structured_thought = thought_response
        else:
            raw_txt = str(thought_response)
            structured_thought = Thought(
                thought=raw_txt[:200] + "..." if len(raw_txt) > 200 else raw_txt,
                reasoning="No structured JSON returned; treated as plain text"
            )
        
        return {**state, "thoughts": structured_thought.thought, "structured_thought": structured_thought}
    
    def _generate_joke(self, state: State) -> State:
        """Generate or improve a joke"""
        user_message = state['user_messages'][-1].content
        thought = state['thoughts']
        current_iteration = state.get('joke_iteration', 0)
        conversation_history = state.get('conversation_history', [])
        
        # Format conversation context
        context = self._format_conversation_history(conversation_history)
        
        # Check if this is a first attempt or improvement iteration
        if current_iteration == 0:
            # First joke generation
            prompt = f"{context}\nWrite a joke related to your thoughts: {thought}. Consider the conversation history to make it more relevant and personalized. IMPORTANT: Return ONLY valid JSON with fields: joke (string) and num_words (int). If your joke contains quotes, escape them with backslashes. Example: {{\"joke\": \"Why did the chicken cross the road? To get to the \\\"other side\\\"!\", \"num_words\": 12}}"
        else:
            # Improvement iteration
            previous_joke = state['generated_joke']
            quality_feedback = state['quality_score']
            prompt = f"{context}\nImprove this joke: '{previous_joke.joke}'. The previous score was {quality_feedback.score}/1000. Reason: {quality_feedback.reason}. Consider the conversation history and write a better, more relevant joke. IMPORTANT: Return ONLY valid JSON with fields: joke (string) and num_words (int). If your joke contains quotes, escape them with backslashes."
        
        # Use LangChain's invoke method with structured output
        generated_joke = self._invoke_llm(prompt, Generated_Joke if self.config.provider != "runpod" else None)
        
        # Parse the structured response with error handling
        try:
            structured_joke = Generated_Joke.model_validate_json(generated_joke)
        except Exception as e:
            # Fallback: Create a simple joke structure if JSON parsing fails
            import re
            import json
            
            # Try to extract joke content from malformed JSON
            try:
                # Look for joke content between quotes
                joke_match = re.search(r'"joke":\s*"([^"]*(?:\\"[^"]*)*)"', generated_joke)
                if joke_match:
                    joke_text = joke_match.group(1).replace('\\"', '"')
                else:
                    # If regex fails, use the raw response as joke
                    joke_text = generated_joke[:200] + "..." if len(generated_joke) > 200 else generated_joke
                
                word_count = len(joke_text.split())
                structured_joke = Generated_Joke(joke=joke_text, num_words=word_count)
            except Exception:
                # Ultimate fallback
                structured_joke = Generated_Joke(
                    joke="Why did the conversation break? Because the AI couldn't handle the quotes!",
                    num_words=12
                )
        
        return {**state, "generated_joke": structured_joke, "joke_iteration": current_iteration + 1}
    
    def _score_joke(self, state: State) -> State:
        """Score the generated joke"""
        joke = state['generated_joke']
        quality_score_response = self._invoke_llm(
            f"Score the joke '{joke.joke}' on a scale of 0 to 1000. Return your score as JSON with fields: score (int) and reason (string).",
            Quality_Score if self.config.provider != "runpod" else None
        )
        
        # Parse the structured response with error handling
        try:
            structured_quality_score = Quality_Score.model_validate_json(quality_score_response)
        except Exception as e:
            # Fallback: Create a default score if JSON parsing fails
            structured_quality_score = Quality_Score(
                score=500,  # Default middle score
                reason="Unable to parse score response - using default"
            )
        
        return {**state, "quality_score": structured_quality_score}
    
    def _should_continue_improving_joke(self, state: State) -> Literal["improve_joke", "end"]:
        """Decide whether to continue improving the joke"""
        quality_score = state.get('quality_score')
        joke_iteration = state.get('joke_iteration', 0)
        
        if not quality_score:
            return "end"
        
        if quality_score.score >= self.config.min_joke_score:
            return "end"
        
        if joke_iteration >= self.config.max_iterations:
            return "end"
        
        return "improve_joke"
    
    def _combine_response_with_joke(self, state: State) -> State:
        """Combine the response with the generated joke"""
        final_response = state['response'][-1] if state['response'] else ""
        generated_joke = state.get('generated_joke')
        quality_score = state.get('quality_score')
        
        if generated_joke and quality_score:
            # Create a prompt to combine the response with the joke
            combine_prompt = f"""
            You have a response: "{final_response}"
            You also have a joke: "{generated_joke.joke}"
            You hold these principles dear and must apply them to this final response {state.get('principles')})"""
            
            # Use LangChain's invoke method with structured output
            combined_response_result = self._invoke_llm(
                combine_prompt,
                Response if self.config.provider != "runpod" else None
            )
            
            # Parse the structured response with error handling
            try:
                # Check if it's already a Response object
                if isinstance(combined_response_result, Response):
                    combined_structured_response = combined_response_result
                else:
                    combined_structured_response = Response.model_validate_json(combined_response_result)
            except Exception as e:
                # Fallback: Create a simple response structure if JSON parsing fails
                response_text = str(combined_response_result)
                combined_structured_response = Response(
                    response=response_text[:500] + "..." if len(response_text) > 500 else response_text,
                    tone="aggressive"
                )
            
            # Add the combined response to the response list
            return {**state, "response": state["response"] + [combined_structured_response.response], "structured_response": combined_structured_response}
        else:
            return state
    
    def _generate_response(self, state: State) -> State:
        """Generate initial response"""
        # Use the LLM to generate a structured response based on the thought
        user_message = state['user_messages'][-1].content
        thought = state['thoughts']
        conversation_history = state.get('conversation_history', [])
        
        # Format conversation context
        context = self._format_conversation_history(conversation_history)
        
        if self.config.provider in ["runpod", "runpod_ollama"]:
            prompt_resp = (
                f"{context}\nYou have been thinking '{thought}' about the user's message '{user_message}'. "
                "Respond appropriately to the user in plain text, one or two sentences."
            )
        else:
            prompt_resp = (
                f"{context}\nYou have been thinking '{thought}' about the user's message '{user_message}'. Consider the conversation history and respond appropriately to the user. Return your response as JSON with fields: response (string) and tone (string)."
            )
        response_result = self._invoke_llm(prompt_resp, Response if self.config.provider not in ["runpod", "runpod_ollama"] else None)
        
        # Parse the structured response with error handling
        try:
            # Check if it's already a Response object
            if isinstance(response_result, Response):
                structured_response = response_result
            else:
                structured_response = Response.model_validate_json(response_result)
        except Exception as e:
            # Fallback: Create a simple response structure if JSON parsing fails
            response_text = str(response_result)
            structured_response = Response(
                response=response_text[:500] + "..." if len(response_text) > 500 else response_text,
                tone="friendly"
            )
        
        return {**state, "response": state["response"] + [structured_response.response], "structured_response": structured_response}
    
    def _consider_principles(self, state: State) -> State:
        """Apply principles to the response"""
        # Use the LLM to consider the principles with structured output
        user_input = state['user_messages'][-1].content
        response_text = state['response'][-1] if state['response'] else ""
        conversation_history = state.get('conversation_history', [])
        
        # Format conversation context
        context = self._format_conversation_history(conversation_history)
        
        if self.config.provider in ["runpod", "runpod_ollama"]:
            prompt_final = (
                f"{context}\nOriginal response: {response_text}. User message: {user_input}. Principles: {self.config.principles}. "
                "Apply these principles and produce a concise reply in plain text."
            )
        else:
            prompt_final = (
                f"{context}\nOriginal response: {response_text}. User message: {user_input}. Principles: {self.config.principles}. Consider the conversation history and apply these principles to create your final response as JSON with fields: response (string) and tone (string)."
            )

        final_response_result = self._invoke_llm(prompt_final, Response if self.config.provider not in ["runpod", "runpod_ollama"] else None)
        
        # Parse the structured response with error handling
        try:
            # Check if it's already a Response object
            if isinstance(final_response_result, Response):
                final_structured_response = final_response_result
            else:
                final_structured_response = Response.model_validate_json(final_response_result)
        except Exception as e:
            # Fallback: Create a simple response structure if JSON parsing fails
            response_text = str(final_response_result)
            final_structured_response = Response(
                response=response_text[:500] + "..." if len(response_text) > 500 else response_text,
                tone="aggressive"
            )
        
        return {**state, "response": state["response"] + [final_structured_response.response]}
    
    def chat(self, user_input: str, conversation_history: list[dict] = None) -> dict:
        """
        Main chat method that processes user input and returns structured response
        
        Args:
            user_input (str): The user's message
            conversation_history (list[dict]): Previous conversation exchanges
            
        Returns:
            dict: Structured response containing all chat data
        """
        try:
            # Create initial state
            state = {
                "thoughts": "",
                "plan": "",
                "action": "",
                "user_messages": [HumanMessage(content=user_input)],
                "response": [],
                "generated_joke": None,
                "quality_score": None,
                "structured_thought": None,
                "structured_response": None,
                "joke_iteration": 0,
                "conversation_history": conversation_history or []
            }
            
            # Process through the graph
            result = self.graph.invoke(state)
            
            # Extract and structure the response
            return self._format_response(result, user_input, conversation_history)
            
        except Exception as e:
            return {
                "error": str(e),
                "user_input": user_input,
                "status": "error"
            }
    
    def _format_response(self, result: dict, user_input: str, conversation_history: list[dict] = None) -> dict:
        """Format the response for easy consumption"""
        thoughts_text = result["thoughts"]
        responses = result["response"] if result["response"] else []
        structured_thought = result.get("structured_thought")
        structured_response = result.get("structured_response")
        generated_joke = result.get("generated_joke")
        quality_score = result.get("quality_score")
        joke_iteration = result.get("joke_iteration", 0)
        
        # Debug: Print what's in responses
        print(f"[DEBUG] Responses list: {responses}")
        print(f"[DEBUG] Response types: {[type(r) for r in responses]}")
        
        # Ensure responses are strings
        string_responses = []
        for r in responses:
            if isinstance(r, str):
                string_responses.append(r)
            else:
                # Convert Response objects to strings
                string_responses.append(str(r))
        
        principles_response = string_responses[1] if len(string_responses) > 1 else ""
        final_combined_response = string_responses[-1] if string_responses else "No response generated"
        
        # Update conversation history with this exchange
        updated_history = (conversation_history or []).copy()
        updated_history.append({
            "user": user_input,
            "ai": final_combined_response
        })
        
        return {
            "status": "success",
            "user_input": user_input,
            "thoughts": thoughts_text,
            "reasoning": structured_thought.reasoning if structured_thought else "",
            "response_before_joke": principles_response,
            "generated_joke": generated_joke.joke if generated_joke else "",
            "joke_word_count": generated_joke.num_words if generated_joke else 0,
            "joke_iterations": joke_iteration,
            "joke_quality_score": quality_score.score if quality_score else 0,
            "score_reason": quality_score.reason if quality_score else "",
            "final_response": final_combined_response,
            "response_tone": structured_response.tone if structured_response else "",
            "conversation_history": updated_history
        }
    
    def get_simple_response(self, user_input: str, conversation_history: list[dict] = None) -> str:
        """
        Simple method that returns just the final response text
        
        Args:
            user_input (str): The user's message
            conversation_history (list[dict]): Previous conversation exchanges
            
        Returns:
            str: The final response text
        """
        result = self.chat(user_input, conversation_history)
        if result.get("status") == "error":
            return f"Error: {result.get('error', 'Unknown error')}"
        return result.get("final_response", "No response generated") 