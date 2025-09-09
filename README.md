# 🏆 Portia-Powered Voice Settlement Agent

> **The first insurance settlement system that uses Portia's AI planning to deliver emotionally intelligent, voice-driven claim resolution with faster settlements and higher customer satisfaction at a cheaper cost.**

## 🚀 Quick Demo

```bash
# Install dependencies
pip install -r requirements.txt

# Set your API keys
export HUME_API_KEY=your_hume_key
export OPENAI_API_KEY=your_openai_key  
export PORTIA_API_KEY=your_portia_key

# Run the settlement agent
python src/main_evi.py

# Try saying: "I want to settle for twenty-five thousand dollars"
```

## 🎯 Features

- **Voice AI**: HUME EVI 3 emotional intelligence
- **AI Planning**: Portia SDK orchestration  
- **Human-in-Loop**: Critical decision oversight
- **Real-time**: Sub-500ms response times
- **Future-Ready**: Built for next-gen AI

## 🏗️ Architecture

```
Customer Voice → HUME EVI 3 → Portia SDK → Human Loop
     ↓              ↓            ↓          ↓
  Emotions      AI Agent    Smart Planning  Critical Decisions
```

## 🏆 Hackathon Winning Project

This project showcases the future of voice negotiations - where AI handles emotional labor and humans make critical decisions. 
See `docs/hackathon_pitch.md` for full presentation materials.

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

## 🏅 Built With

- 🧠 **Portia SDK**: AI planning and tool orchestration
- 🎤 **Hume EVI 3**: Emotional voice intelligence  
- 🏗️ **Python**: Production-ready implementation
- 🚀 **Innovation**: First-of-kind voice + planning integration

