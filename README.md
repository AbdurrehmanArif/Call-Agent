# Call Agent - AI Voice Assistant

An AI-powered voice call handling system built with FastAPI, OpenAI, and ElevenLabs.

## Features

- **Speech-to-Text**: Transcribe user speech using OpenAI Whisper
- **Intent Detection**: Automatically detect user intent (greeting, support, complaint, etc.)
- **Sentiment Analysis**: Analyze user sentiment in real-time using VADER
- **AI Responses**: Generate contextual responses using OpenAI GPT-4
- **Text-to-Speech**: Convert responses to natural speech using ElevenLabs
- **Dialogue Management**: Maintain conversation context and state
- **Call Logging**: Store all conversations in SQLite database
- **Web Interface**: Professional frontend for making calls and viewing history

## Project Structure

```
call_agent/
├── app.py                 # Main entry point
├── requirements.txt       # Python dependencies
├── .env                   # Environment configuration
├── backend/
│   ├── main.py           # FastAPI application
│   ├── routes/
│   │   └── call_routes.py    # API endpoints
│   ├── services/
│   │   ├── speech_to_text.py   # Whisper STT
│   │   ├── text_to_speech.py   # ElevenLabs TTS
│   │   ├── intent_detector.py  # Intent detection
│   │   ├── sentiment_analyzer.py # Sentiment analysis
│   │   ├── response_generator.py # GPT responses
│   │   └── dialogue_manager.py # Conversation state
│   ├── database/
│   │   └── db.py         # SQLite database
│   ├── utils/
│   │   ├── config.py     # Configuration
│   │   └── audio_utils.py # Audio processing
│   └── prompts/
│       └── system_prompt.txt # AI assistant instructions
└── frontend/
    ├── index.html        # Main HTML page
    ├── css/
    │   └── styles.css    # Styling
    └── js/
        └── app.js        # Frontend logic
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Edit `.env` file with your API keys:

```env
OPENAI_API_KEY=your_openai_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
```

### 3. Run the Application

```bash
python app.py
```

The server will start at `http://localhost:8000`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve frontend |
| `/health` | GET | Health check |
| `/api/calls/start` | POST | Start a new call session |
| `/api/calls/process` | POST | Process audio input |
| `/api/calls/end` | POST | End call and get summary |
| `/api/calls/session/{id}` | GET | Get session info |
| `/api/calls/history/{id}` | GET | Get conversation history |
| `/api/calls/voices` | GET | Get available TTS voices |
| `/api/calls/calls/recent` | GET | Get recent call logs |

## Frontend Features

- **Voice Call Interface**: Start/end calls with visual feedback
- **Live Transcript**: Real-time conversation display
- **Audio Visualizer**: Animated waveform during calls
- **Call Statistics**: Duration, intent, sentiment tracking
- **Call History**: View and search past conversations
- **Settings**: Configure audio, theme, and server options
- **Responsive Design**: Works on desktop and mobile

## Usage

1. Open `http://localhost:8000` in your browser
2. Click "Start Call" to begin a session
3. Allow microphone access when prompted
4. Speak to interact with the AI assistant
5. View live transcript and call statistics
6. Click "End Call" when finished

## API Keys Required

- **OpenAI**: For speech-to-text (Whisper) and response generation (GPT-4)
  - Get at: https://platform.openai.com/api-keys
- **ElevenLabs**: For text-to-speech voice generation
  - Get at: https://elevenlabs.io/app/sign-in

## Technology Stack

- **Backend**: FastAPI, Python
- **AI/ML**: OpenAI API, VADER Sentiment, scikit-learn
- **TTS**: ElevenLabs API
- **STT**: OpenAI Whisper API
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)

## License

MIT
