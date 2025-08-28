# Multi-Agent Document Processing System

A high-performance, intelligent document processing system that uses multiple AI agents to extract, analyze, and summarize PDF documents with lightning-fast performance.

## 🚀 Features

- **⚡ Fast Mode**: Instant document processing using lightweight text analysis
- **🤖 AI Mode**: Advanced AI-powered analysis using LLaMA 3 (when enabled)
- **📄 PDF Text Extraction**: Robust PDF parsing with pdfplumber
- **📋 Smart Summarization**: Intelligent text summarization
- **🔍 Field Extraction**: Automatic detection of dates, titles, authors, and key points
- **🎯 Multi-tab Interface**: Clean Streamlit-based user interface
- **📊 Real-time Processing**: Live progress tracking and status updates

## ⚡ Performance

- **Fast Mode**: 2-5 seconds (lightweight analysis)
- **AI Mode**: 2-5 minutes (full LLM processing)
- **Smart Fallback**: Automatically switches to fast mode if AI fails

## 🛠️ Prerequisites

- Python 3.8+
- Ollama with LLaMA 3 model (for AI mode)
- pip (Python package manager)

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install Ollama (Optional - for AI mode)
```bash
# macOS
brew install ollama

# Start Ollama service
brew services start ollama

# Download LLaMA 3 model
ollama pull llama3
```

### 3. Run the Application
```bash
streamlit run app.py
```

### 4. Open in Browser
Navigate to: http://localhost:8501

## 📖 Usage

1. **Upload PDF**: Use the file uploader in the "📤 Upload" tab
2. **Choose Mode**: 
   - ✅ **Fast Mode** (Recommended): Instant results
   - ❌ **AI Mode**: Slower but more accurate
3. **Process**: Click "Extract" to start processing
4. **View Results**: Check the different tabs for:
   - 📝 Raw extracted text
   - 📋 Generated summary
   - 🔑 Extracted key fields

## 🏗️ Architecture

- **`app.py`**: Main Streamlit application with UI
- **`agents.py`**: AI agent definitions and processing logic
- **`logger_config.py`**: Logging configuration
- **`requirements.txt`**: Python dependencies

## 🔧 Configuration

### Fast Mode (Default)
- Uses regex patterns and text analysis
- No external API calls
- Instant processing
- Good for most use cases

### AI Mode
- Requires Ollama + LLaMA 3
- Advanced natural language understanding
- Slower processing
- Higher accuracy for complex documents

## 📁 Project Structure

```
multi-agent-document-processor/
├── app.py                 # Main Streamlit application
├── agents.py             # AI agent implementations
├── logger_config.py      # Logging setup
├── requirements.txt      # Python dependencies
├── .gitignore           # Git ignore rules
├── README.md            # Project documentation
├── logs/                # Application logs
└── pdf/                 # Sample PDF documents
```

## 🚀 Performance Tips

1. **Use Fast Mode** for quick document analysis
2. **Enable AI Mode** only when you need advanced analysis
3. **Keep Ollama running** if using AI features
4. **Monitor logs** for debugging and optimization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🆘 Support

If you encounter any issues:
1. Check the logs in the `logs/` directory
2. Ensure all dependencies are installed
3. Verify Ollama is running (if using AI mode)
4. Check the browser console for errors

---

**Built with ❤️ using Streamlit, LangChain, and CrewAI** 