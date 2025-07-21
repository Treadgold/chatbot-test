# Chatbot with RunPod Ollama Serverless

A LangGraph-based chatbot that can run locally with Ollama or on RunPod serverless infrastructure.

## Features

- **Local Ollama Support**: Run with local Ollama installation
- **RunPod Serverless**: Deploy Ollama in Docker containers on RunPod for serverless inference
- **LangGraph Integration**: Complex conversation flows with thoughts, principles, and personality
- **Web Interface**: Flask-based chat interface with async processing
- **Stripe Integration**: Payment processing capabilities
- **Smart Chat Archiving**: Every conversation automatically saved as readable text files with analytics

## 🏗️ Architecture Overview

Our chatbot is built with a modular, async-first architecture that separates concerns and enables scalable processing:

### 🔄 Async Chat Processing

The web interface uses **background threading** to handle chat requests asynchronously, preventing the main Flask thread from blocking during AI processing:

```python
# web_chat.py lines 607-673
@app.route('/chat-async', methods=['POST'])
def chat_async():
    """Start an async chat request and return job ID immediately"""
    # Generate unique job ID and start background thread
    job_id = str(uuid.uuid4())
    
    def process_chat():
        try:
            response = chatbot.chat(user_input, conversation_history)
            chat_jobs[job_id]['status'] = 'completed'
            chat_jobs[job_id]['result'] = response
        except Exception as e:
            chat_jobs[job_id]['status'] = 'failed'
    
    # Start background thread
    thread = threading.Thread(target=process_chat)
    thread.daemon = True
    thread.start()
    
    return jsonify({'job_id': job_id, 'status': 'processing'})
```

This design allows:
- **Immediate response** to users (no waiting for AI processing)
- **Non-blocking UI** - users can continue browsing while AI thinks
- **Scalable processing** - multiple requests can be processed simultaneously
- **Status polling** - frontend can check progress via `/chat-status/<job_id>`

### 🧠 LangGraph Component Structure

The core chatbot logic is encapsulated in a reusable `ChatBot` class that uses LangGraph for complex conversation flows:

```python
# chatbot_component.py lines 75-100
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
        elif self.config.provider == "runpod_ollama":
            self.llm = RunPodOllamaLLM(
                endpoint=self.config.runpod_endpoint,
                api_key=self.config.runpod_api_key,
                model=self.config.model_name
            )
```

The LangGraph workflow includes:
- **Thought processing** - AI reflects on user input
- **Principle consideration** - Applies personality and guidelines  
- **Response generation** - Creates structured, contextual responses
- **Conversation history** - Maintains context across exchanges

## 🗂️ How Our Chat Archiving Works (The Fun Part!)

Ever wondered where all those conversations go? We've built a clever system that turns every chat into a searchable, analyzable text file! Here's how it works:

### 📁 Where Your Chats Live

All conversations are stored in the `chat_archive/` directory as human-readable JSON files. Each file tells a story:

```
chat_archive/
├── 20250721_1009_001_d942d9bf.json    # July 21, 2025 at 10:09 AM, 1 message
├── 20250721_1134_002_d942d9bf.json    # Same day at 11:34 AM, 2 messages  
├── archive_summary.json               # The master analytics file
└── README.md                         # This very documentation!
```

### 🏷️ Our Clever Naming System

We don't just slap random names on files! Each filename is a mini-database:

```python
# web_chat.py lines 135-139
def generate_chat_filename(session_id, created_at, message_count):
    """Generate filename with metadata: YYYYMMDD_HHMM_count_sessionid.json"""
    timestamp = created_at.strftime('%Y%m%d_%H%M')
    short_session = session_id.split('-')[0]  # Use first part of UUID
    return f"{timestamp}_{message_count:03d}_{short_session}.json"
```

So `20250721_1134_002_d942d9bf.json` means:
- **Date**: July 21, 2025
- **Time**: 11:34 AM  
- **Messages**: 2 exchanges
- **Session**: User session starting with `d942d9bf`

### 💾 How We Save Every Word

Every time you send a message, our system springs into action:

```python
# web_chat.py lines 141-210
def save_conversation_to_archive(session_id, conversation_history):
    """Save conversation history to archive with metadata filename"""
    if not CHAT_LOGGING_ENABLED or not conversation_history:
        return
    
    # Create chat data with all the juicy details
    chat_data = {
        'session_id': session_id,
        'created_at': now.isoformat(),
        'last_updated': now.isoformat(),
        'message_count': len(conversation_history),
        'conversation_history': conversation_history,
        'metadata': {
            'total_user_chars': sum(len(exchange['user']) for exchange in conversation_history),
            'total_ai_chars': sum(len(exchange['ai']) for exchange in conversation_history),
            'avg_user_length': sum(len(exchange['user']) for exchange in conversation_history) / len(conversation_history),
            'avg_ai_length': sum(len(exchange['ai']) for exchange in conversation_history) / len(conversation_history),
        }
    }
```

### 📊 The Master Analytics File

We keep a running tally of everything in `archive_summary.json`:

```json
{
  "last_updated": "2025-07-21T11:57:05.809626",
  "total_conversations": 7,
  "total_messages": 14,
  "total_user_chars": 670,
  "total_ai_chars": 6333,
  "conversations_by_date": {"2025-07-21": 7},
  "messages_by_date": {"2025-07-21": 14},
  "conversations_by_hour": {"11": 4, "10": 1, "8": 1, "9": 1},
  "avg_messages_per_conversation": 2.0,
  "avg_user_chars_per_conversation": 95.7,
  "avg_ai_chars_per_conversation": 904.7
}
```

### 🔍 How We Track Conversations

We're smart about tracking! If you continue a conversation, we update the existing file instead of creating duplicates:

```python
# web_chat.py lines 168-200
# Find existing file for this exact session ID
for file_path in Path(CHAT_ARCHIVE_DIR).glob("*.json"):
    if file_path.name == 'archive_summary.json':
        continue
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_data = json.load(f)
        if file_data.get('session_id') == session_id:
            # Update existing file - preserve original creation time
            filepath = existing_file
            chat_data['created_at'] = existing_data['created_at']
            app.logger.info(f"Updating existing conversation file: {filepath.name}")
```

### 📈 Your Analytics Dashboard

Want to see all this data in action? Visit `/admin/analytics` in your web app! You'll see:

- **Real-time stats**: Total conversations, messages, characters
- **Time-based charts**: When people chat most
- **Conversation browser**: Click any chat to read the full conversation
- **Auto-refresh**: Updates every 5 minutes

The analytics page (`templates/analytics.html`) shows beautiful charts and lets you browse through every conversation like a detective going through case files!

### 🔧 Behind the Scenes

Our archiving system runs automatically:

1. **Every message** triggers `save_conversation_to_archive()` 
2. **Every save** updates the master `archive_summary.json`
3. **Every update** refreshes the analytics dashboard
4. **Every file** is human-readable JSON you can open in any text editor

### 🛡️ Privacy & Security

- Files are stored locally on your server
- No external services see your conversations
- You control the data completely
- Files can be easily backed up or deleted

### 🎯 What This Means for You

- **Never lose a conversation** - everything is automatically saved
- **Track usage patterns** - see when your bot is most popular
- **Debug issues** - read exactly what users said and how the AI responded
- **Improve your bot** - analyze conversation quality and length
- **Backup easily** - just copy the `chat_archive/` folder

Pretty cool, right? Your chatbot is basically keeping a diary of every conversation! 📝

## Quick Start (Local)

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Ollama**:
   
   **macOS/Linux:**
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```
   
   **Windows:**
   Download from [https://ollama.ai/download](https://ollama.ai/download) and run the installer.
   
   **Docker:**
   ```bash
   docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
   ```

3. Start Ollama locally:
   ```bash
   ollama serve
   ollama pull dolphin-mistral-nemo:latest
   ```

4. Run the web interface:
   ```bash
   python web_chat.py
   ```

5. Open http://localhost:5000

## Complete Deployment Guide

### Step 1: Build and Push Docker Image for RunPod Backend

```bash
# Build the Ollama serverless image
docker build -f Dockerfile.ollama -t yourusername/runpod-ollama:latest .

# Push to Docker Hub
docker push yourusername/runpod-ollama:latest
```

### Step 2: Create RunPod Serverless Endpoint

1. Go to [RunPod Console](https://www.runpod.io/) → **Serverless**
2. Click **New Endpoint**
3. Configure the endpoint:
   - **Docker Image**: `yourusername/runpod-ollama:latest`
   - **Container Disk**: 20GB (minimum for most models)
   - **GPU Type**: Select based on your model (RTX 4090 recommended for 7B-13B models)
   - **Max Execution Time**: 600 seconds (10 minutes)
   - **Idle Timeout**: 5 seconds
   - **Workers Min**: 0, **Workers Max**: 1-3
4. Click **Create Endpoint**
5. **Copy the Endpoint ID** from the URL (e.g., `vsgzvmdz6x1bei`)

### Step 3: Configure Environment Variables

Create or update your `.env` file:

```bash
# RunPod Configuration
RUNPOD_ENDPOINT=https://api.runpod.ai/v2/YOUR_ENDPOINT_ID
RUNPOD_API_KEY=your_runpod_api_key

# Flask Configuration  
FLASK_SECRET_KEY=your-secret-key-here
FLASK_ENV=production
```

### Step 4: Install Dependencies and Start Web Application

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start the web application with uvicorn (recommended for production)
uvicorn asgi:application --host 0.0.0.0 --port 8000

# Alternative: Start with Flask development server
python web_chat.py
```

### Step 5: Access Your Chat Application

Open your browser and navigate to:
- **Local**: http://localhost:8000
- **Production**: http://your-server-ip:8000

## Configuration Options

### RunPod Backend Configuration

Update `web_chat.py` if needed:

```python
# web_chat.py lines 411-454
cfg = ChatBotConfig(
    provider="runpod",  # Using RunPod serverless endpoint
    model_name="CognitiveComputations/dolphin-mistral-nemo:latest",
    runpod_endpoint=os.getenv('RUNPOD_ENDPOINT', 
                            "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID"),
    runpod_api_key=os.getenv('RUNPOD_API_KEY'),
    max_iterations=3,
    timeout=0  # No timeout - wait indefinitely
)
```

## Files

- `chatbot_component.py` - Main chatbot logic with LangGraph
- `web_chat.py` - Flask web interface with async processing
- `Dockerfile.ollama` - Docker image for RunPod serverless
- `ollama_handler.py` - RunPod serverless handler
- `runpod_ollama_llm.py` - Client wrapper for RunPod Ollama
- `build_and_deploy.md` - Detailed deployment instructions

## Configuration

The chatbot supports three providers:

1. **"ollama"** - Local Ollama installation
2. **"runpod"** - RunPod vLLM endpoints (basic)
3. **"runpod_ollama"** - RunPod Ollama serverless (recommended)

## Benefits of RunPod Ollama

- ✅ **Identical behavior** to local Ollama
- ✅ **Serverless scaling** - pay only when used
- ✅ **Any Ollama model** - supports full model library
- ✅ **Reliable inference** - proven Ollama engine
- ✅ **Auto-scaling** - handles multiple requests

## License

MIT License 