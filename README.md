# 🎙️ Insurance Settlement Negotiator Voice Agent

> **An AI-powered voice agent that handles insurance claim settlements through intelligent conversation, emotional analysis, and human-in-the-loop oversight for optimal outcomes.**

## 🚀 Getting Started

```bash
# Clone the repository
git clone https://github.com/Nachi-Kulkarni/Insurance_Settlement_Negotiator_Voice-Agent_with_humanintheloop.git
cd Insurance_Settlement_Negotiator_Voice-Agent_with_humanintheloop

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env file with your API keys

# Run the settlement agent
python src/main_evi.py

# Example interaction: "I want to settle my claim for $25,000"
```

## 🎯 Key Features

- **Emotional Intelligence**: Advanced voice analysis using Hume AI for emotional context
- **Intelligent Conversation**: Natural language processing for settlement negotiations
- **Human Oversight**: Human-in-the-loop workflow for critical decisions
- **Real-time Processing**: Sub-500ms response times for seamless interaction
- **Comprehensive Testing**: Full test suite for reliability and accuracy

## 🏗️ System Architecture

```
Customer Voice → Hume AI EVI → Settlement Engine → Human Review
     ↓              ↓               ↓              ↓
  Emotions      AI Processing    Smart Analysis   Final Approval
```

## 💡 Technical Implementation

This system demonstrates advanced integration of voice AI, natural language processing, and automated decision-making with human oversight for complex financial negotiations.

## 🚀 Project Structure

```
portia-final/
├── src/
│   ├── main_evi.py                    # Main entry point
│   ├── voice_interface_simplified.py  # Voice interface
│   ├── evi_tool_handler.py           # Tool execution logic
│   ├── portia_tools.py               # Insurance tools
│   ├── portia_settlement_agent.py    # Settlement agent logic
│   ├── settlement_review_workflow.py # Dashboard integration
│   ├── human_intervention_handler.py # Human-in-the-loop workflow
│   ├── webhook_handler.py            # API webhook handling
│   └── config.py                     # Configuration management
├── tests/                            # Test suite
└── requirements.txt                  # Dependencies
```

## 🛠️ Technologies Used

- **Python**: Core application development
- **Hume AI EVI**: Emotional voice intelligence and conversation handling
- **OpenAI GPT**: Natural language processing and decision making
- **Portia SDK**: AI agent orchestration and tool management
- **WebSocket**: Real-time voice communication
- **Pytest**: Comprehensive testing framework

## 📋 Prerequisites

- Python 3.9+
- API keys for Hume AI, OpenAI, and Portia
- Microphone access for voice input
- Internet connection for API calls

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/test_tool_calling.py
pytest tests/test_config.py
```

