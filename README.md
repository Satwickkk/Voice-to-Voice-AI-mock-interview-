# AI Voice-to-Voice Mock Interview System

An intelligent Python-based mock interview system that conducts real-time voice conversations with AI, analyzes tone and confidence, and provides comprehensive feedback.

#Interface
<img width="1909" height="901" alt="image" src="https://github.com/user-attachments/assets/2aebaa6e-868c-4fa4-aa20-95f8e5a8c8ea" />

## 🎯 Features

- **Real-Time Voice Interview**: Speak naturally with an AI interviewer
- **Speech-to-Text**: Accurate transcription using OpenAI Whisper
- **Text-to-Speech**: Natural AI voice responses
- **Tone & Confidence Analysis**: Analyze pitch, tempo, speaking rate, and confidence
- **AI-Powered Questions**: Contextual follow-up questions using Google Gemini
- **Comprehensive Feedback**: Detailed scoring and improvement suggestions
- **PDF Reports**: Export interview results and analysis

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Microphone access
- OpenAI API key
- Google Gemini API key

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd VtoV-interview
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Run the application:
```bash
streamlit run app.py
```

## 📁 Project Structure

```
VtoV-interview/
├── app.py                 # Main Streamlit application
├── interview_engine.py    # Core interview logic
├── audio_processor.py     # Audio handling and analysis
├── speech_analyzer.py     # Tone and confidence analysis
├── ai_interface.py        # AI API integrations
├── report_generator.py    # PDF report generation
├── utils.py              # Utility functions
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 🔧 Configuration

Create a `.env` file with your API keys:

```env
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_gemini_api_key_here
```

## 🎤 Usage

1. **Start Interview**: Click "Start Interview" to begin
2. **Answer Questions**: Speak naturally when prompted
3. **Listen to AI**: AI will ask follow-up questions based on your responses
4. **Get Feedback**: Receive real-time tone and confidence analysis
5. **View Report**: Download comprehensive PDF report at the end

## 📊 Analysis Features

- **Tone Analysis**: Pitch, tempo, speaking rate
- **Confidence Scoring**: Based on clarity, fluency, and hesitation
- **Energy Detection**: Voice energy and pause analysis
- **AI Evaluation**: Relevance and quality assessment
- **Overall Scoring**: 0-100 score with detailed breakdown

## 🛠️ Technical Stack

- **Frontend**: Streamlit
- **Speech Recognition**: OpenAI Whisper
- **Text-to-Speech**: gTTS, pyttsx3
- **AI Logic**: Google Gemini
- **Audio Analysis**: librosa, pyAudioAnalysis, webrtcvad
- **Report Generation**: ReportLab

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions, please open an issue on GitHub.
