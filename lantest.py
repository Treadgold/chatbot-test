from langchain_core.messages import HumanMessage
from langchain_community.chat_models import ChatOllama

# Step 1: Create the Ollama chat model instance
llm = ChatOllama(model="llama3.2:latest")

# Step 2: Create a message object (LangChain uses structured messages)
message = HumanMessage(content="Explain the difference between RAM and SSD.")

# Step 3: Send the message to the model and get the response
response = llm.invoke([message])

# Step 4: Print the model's response
print(response.content)