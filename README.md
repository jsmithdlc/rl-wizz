# :stars: Reinforcement Learning Whizz

[//]: # (Change python version if necessary)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-360/)

This is an interactive web application that brings reinforcement learning education to life through natural conversation. Powered by LLMs, this virtual mentor guides you through RL concepts, quizzes your understanding, and helps you build intuition—all within a friendly interface. Features:

:speech_balloon: **Conversational tutor**: ask anything about RL through a chat interface.

:books: **User-enhanced knowledge base**: provide additional documents and information to interact with during conversations with the tutor.

:pushpin: **Personalized learning**: quiz yourself about RL topics. The tutor will remember previous questions and challenge you to stay at your sharpest.

## Development

This project uses [uv](https://docs.astral.sh/uv/) as a package manager.

You need to install pdf-analysis and tesseract to enable adding pdf documents to your tutor vector store:

macOS

```bash
brew install poppler tesseract
```

Linux

```bash
apt install poppler tesseract
```

Start the streamlit app for debugging by running:

```bash
uv run streamlit --log_level debug run src/app.py
```






## TODO

- [ ] Implement interface for experiment debugging
