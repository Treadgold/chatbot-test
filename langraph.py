from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage
from langchain_ollama import OllamaLLM

from pydantic import BaseModel, Field
from typing import Literal

max_iterations = 3

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

# Step 1: Create the OllamaLLM instance with the desired model
llm = OllamaLLM(model="dolphin-mistral-nemo:latest",
                base_url="http://localhost:11434")

quality_score_llm = OllamaLLM(model="dolphin-mistral-nemo:latest",
                base_url="http://localhost:11434")
joke_writer_llm = OllamaLLM(model="dolphin-mistral-nemo:latest",
                base_url="http://localhost:11434")



# Define the state structure
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

# Initialize the graph with the state type
builder = StateGraph(State)

# Node 1: Process Thought with Structured Output
def process_thought(state: State) -> State:
    # Use the LLM to generate a structured thought based on the user's message
    user_message = state['user_messages'][-1].content
    
    # Use LangChain's invoke method with structured output
    thought_response = llm.invoke(
        f"Think about: {user_message}. Return your thoughts as JSON with fields: thought (string) and reasoning (string).",
        config={"format": Thought.model_json_schema()}
    )
    
    # Parse the structured response
    structured_thought = Thought.model_validate_json(thought_response)
    
    return {**state, "thoughts": structured_thought.thought, "structured_thought": structured_thought}

def generate_joke(state: State) -> State:
    user_message = state['user_messages'][-1].content
    thought = state['thoughts']
    current_iteration = state.get('joke_iteration', 0)
    
    # Check if this is a first attempt or improvement iteration
    if current_iteration == 0:
        # First joke generation
        prompt = f"Write a joke related to your thoughts: {thought}. Return your Joke as JSON with fields: joke (string) and num_words (int)."
    else:
        # Improvement iteration
        previous_joke = state['generated_joke']
        quality_feedback = state['quality_score']
        prompt = f"Improve this joke: '{previous_joke.joke}'. The previous score was {quality_feedback.score}/1000. Reason: {quality_feedback.reason}. Write a better joke. Return your improved joke as JSON with fields: joke (string) and num_words (int)."
    
    # Use LangChain's invoke method with structured output
    generated_joke = joke_writer_llm.invoke(
        prompt,
        config={"format": Generated_Joke.model_json_schema()}
    )
    
    # Parse the structured response
    structured_joke = Generated_Joke.model_validate_json(generated_joke)
    
    return {**state, "generated_joke": structured_joke, "joke_iteration": current_iteration + 1}

def score_joke(state: State) -> State:
    joke = state['generated_joke']
    quality_score_response = quality_score_llm.invoke(
        f"Score the joke '{joke.joke}' on a scale of 0 to 1000. Return your score as JSON with fields: score (int) and reason (string).",
        config={"format": Quality_Score.model_json_schema()}
    )
    
    # Parse the structured response
    structured_quality_score = Quality_Score.model_validate_json(quality_score_response)
    
    return {**state, "quality_score": structured_quality_score}

def should_continue_improving_joke(state: State) -> Literal["improve_joke", "end"]:
    """Decide whether to continue improving the joke or end the process"""
    quality_score = state.get('quality_score')
    joke_iteration = state.get('joke_iteration', 0)
    
    # If no quality score yet, something went wrong
    if not quality_score:
        return "end"
    
    # If score is above 800, we're satisfied
    if quality_score.score >= 800:
        return "end"
    
    # If we've reached max iterations, stop trying
    if joke_iteration >= max_iterations:
        return "end"
    
    # Otherwise, continue improving
    return "improve_joke"

def combine_response_with_joke(state: State) -> State:
    """Combine the final response from principles with the generated joke"""
    # Get the final response from principles
    final_response = state['response'][-1] if state['response'] else ""
    
    # Get the joke
    generated_joke = state.get('generated_joke')
    quality_score = state.get('quality_score')
    
    if generated_joke and quality_score:
        # Create a prompt to combine the response with the joke
        combine_prompt = f"""
        You have a response: "{final_response}"
        You also have a joke: "{generated_joke.joke}" (Quality Score: {quality_score.score}/1000)
        
        Please rewrite the response to naturally incorporate the joke. Make it flow well and feel organic.
        Return your combined response as JSON with fields: response (string) and tone (string).
        """
        
        # Use LangChain's invoke method with structured output
        combined_response_result = llm.invoke(
            combine_prompt,
            config={"format": Response.model_json_schema()}
        )
        
        # Parse the structured response
        combined_structured_response = Response.model_validate_json(combined_response_result)
        
        # Add the combined response to the response list
        return {**state, "response": state["response"] + [combined_structured_response.response], "structured_response": combined_structured_response}
    else:
        # If no joke was generated, just return the state as is
        return state

# Node 2: Generate Response with Structured Output
def generate_response(state: State) -> State:
    # Use the LLM to generate a structured response based on the thought
    user_message = state['user_messages'][-1].content
    thought = state['thoughts']
    
    # Use LangChain's invoke method with structured output
    response_result = llm.invoke(
        f"You have been thinking {thought} about the user's message {user_message}. Now respond to the user. Return your response as JSON with fields: response (string) and tone (string).",
        config={"format": Response.model_json_schema()}
    )
    
    # Parse the structured response
    structured_response = Response.model_validate_json(response_result)
    
    return {**state, "response": state["response"] + [structured_response.response], "structured_response": structured_response}

def consider_principles(state: State) -> State:
    # Use the LLM to consider the principles with structured output
    user_input = state['user_messages'][-1].content
    response_text = state['response'][-1] if state['response'] else ""
    principles = "You are strongly Right wing and watch Fox news and support Donald Trump. You try to can't help yourself from turning every conversation into something about politics."
    
    # Use structured output for the final response
    final_response_result = llm.invoke(
        f"Original response: {response_text}. User message: {user_input}. Principles: {principles}. Return your final response as JSON with fields: response (string) and tone (string).",
        config={"format": Response.model_json_schema()}
    )
    
    # Parse the structured response
    final_structured_response = Response.model_validate_json(final_response_result)
    
    return {**state, "response": state["response"] + [final_structured_response.response]}

# Add nodes to the graph
builder.add_node("process_thought", process_thought)
builder.add_node("generate_response", generate_response)
builder.add_node("consider_principles", consider_principles)
builder.add_node("generate_joke", generate_joke)
builder.add_node("score_joke", score_joke)
builder.add_node("combine_response_with_joke", combine_response_with_joke)

# Define the graph flow
builder.add_edge(START, "process_thought")
builder.add_edge("process_thought", "generate_response")
builder.add_edge("generate_response", "consider_principles")
builder.add_edge("consider_principles", "generate_joke")
builder.add_edge("generate_joke", "score_joke")

# Add conditional edge for joke improvement loop
builder.add_conditional_edges(
    "score_joke",
    should_continue_improving_joke,
    {
        "improve_joke": "generate_joke",
        "end": "combine_response_with_joke"
    }
)

# Add final edge to END
builder.add_edge("combine_response_with_joke", END)

# Compile the graph
graph = builder.compile()
user_input = HumanMessage(content="")

# Example user input
while user_input.content != "exit": 

    user_input = input("Hi, let's chat!: ")
    user_input = HumanMessage(content=user_input)

    # Invoke the graph with the initial state
    state = {
        "thoughts": "",
        "plan": "",
        "action": "",
        "user_messages": [user_input],
        "response": [],
        "generated_joke": None,
        "quality_score": None,
        "structured_thought": None,
        "structured_response": None,
        "joke_iteration": 0
    }

    result = graph.invoke(state)

    # Extract the structured data
    thoughts_text = result["thoughts"]
    responses = result["response"] if result["response"] else []
    structured_thought = result.get("structured_thought")
    structured_response = result.get("structured_response")
    generated_joke = result.get("generated_joke")
    quality_score = result.get("quality_score")
    joke_iteration = result.get("joke_iteration", 0)

    # Determine which responses we have
    principles_response = responses[1] if len(responses) > 1 else ""
    final_combined_response = responses[-1] if responses else "No response generated"

    # Print the result in a more readable format
    print("\n==================== Chatbot Output ====================")
    print("User Input:", user_input.content)
    print("--------------------------------------------------------")
    print("Thoughts:", thoughts_text)
    if structured_thought:
        print("Reasoning:", structured_thought.reasoning)
    print("--------------------------------------------------------")
    if principles_response:
        print("Response (Before Joke):", principles_response)
    print("--------------------------------------------------------")
    if generated_joke:
        print("Generated Joke:", generated_joke.joke)
        print("Joke Word Count:", generated_joke.num_words)
        print("Joke Iterations:", joke_iteration)
    if quality_score:
        print("Joke Quality Score:", f"{quality_score.score}/1000")
        print("Score Reason:", quality_score.reason)
    print("--------------------------------------------------------")
    print("Final Combined Response:", final_combined_response)
    if structured_response:
        print("Response Tone:", structured_response.tone)
    print("========================================================\n")
