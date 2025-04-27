# AI News Aggregator 🤖📰

A powerful AI-powered news aggregator that collects, analyzes, and summarizes the latest artificial intelligence news from multiple sources. The system uses advanced language models and semantic search to provide relevant news updates and interactive chat capabilities.

## Features 🌟

- **Multi-Source News Collection**:
  - smol.ai (Primary source)
  - TechCrunch AI coverage
  - HuggingFace blog posts
  - Intelligent source prioritization

- **Advanced Search & Retrieval**:
  - Semantic search using embeddings
  - Source-aware relevance ranking
  - Multi-language support (English & Arabic)
  - Cosine similarity matching

- **Interactive Chat Interface**:
  - Natural language queries
  - Context-aware responses
  - Article citations and references
  - Error handling in multiple languages

- **Daily News Summaries**:
  - Categorized bullet-point summaries
  - Source diversity enforcement
  - Priority-based article selection
  - Comprehensive coverage across topics

## Setup 🛠️

### Prerequisites

```bash
# Required Python version
Python 3.8+

# Required system dependencies
- SQLite3
- Python virtual environment
```

### Installation

1. Clone the repository:
```bash
git clone (chat with AI news)[https://github.com/h9-tec/Ai_news_Chat]
cd ai_news_aggregator
```

2. Create and activate virtual environment:
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Create .env file
GROQ_API_KEY=your_groq_api_key
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama3.2:latest
GROQ_MODEL=llama-3.3-70b-versatile
```

5. Pull the Ollama model:
```bash
# Make sure Ollama is running first
ollama pull llama3.2:latest
```

## Usage 💡

### Scraping News Sources

Before starting the application, you need to scrape the latest news:

```bash
# Scrape all configured news sources
python -m aggregator.cli --scrape

# You can also scrape specific sources:
python -m aggregator.cli --scrape --source smolai
python -m aggregator.cli --scrape --source techcrunch
python -m aggregator.cli --scrape --source huggingface
```

### Starting the Application

```bash
python -m aggregator.cli --serve
```

The web interface will be available at `http://localhost:7860`

### Using the Chat Interface

1. Select your preferred LLM backend (Ollama or Groq)
2. Enter your question in the chat input
3. Get relevant news articles and summaries
4. Use natural language queries in English or Arabic

### Daily Summaries

1. Navigate to the "Daily Summary" tab
2. Click "Generate Today's Summary"
3. Get a structured summary of today's AI news

## Architecture 🏗️

### Components

1. **Scrapers**:
   - `SmolAISpider`: Primary news source
   - `TechCrunchAISpider`: Tech news coverage
   - `HuggingFaceSpider`: AI research updates

2. **Database**:
   - SQLite with WAL journaling
   - Efficient indexing for date and source
   - Embedding storage for semantic search

3. **Retrieval System**:
   - Semantic search using embeddings
   - Source prioritization
   - Relevance scoring
   - Diversity enforcement

4. **LLM Integration**:
   - Dual backend support (Ollama/Groq)
   - Context-aware prompting
   - Structured response generation

### Data Flow

```mermaid
graph LR
    A[Web Scrapers] --> B[SQLite DB]
    B --> C[Embedding Index]
    C --> D[Retrieval System]
    D --> E[LLM Processing]
    E --> F[Web Interface]
```

## Configuration ⚙️

### LLM Settings

- **Ollama**:
  - Default URL: `http://localhost:11434/api/generate`
  - Default model: `llama3.2:latest`

- **Groq**:
  - Model: `llama-3.3-70b-versatile`
  - Requires API key

### Search Parameters

```python
MAX_CONTEXT_ARTICLES = 5  # Maximum articles per query
SIM_THRESHOLD = 0.15      # Minimum similarity score
EMBED_DIM = 384          # Embedding dimensions
```

### Source Priorities

1. smol.ai (Priority: 3)
2. TechCrunch (Priority: 2)
3. HuggingFace (Priority: 1)

## Development 🔧

### Adding New Sources

1. Create a new spider in `aggregator/scrape/`
2. Implement the BaseNewsSpider interface
3. Add source priority in retrieval.py
4. Update the source diversity settings

### Customizing Prompts

Modify templates in `aggregator/prompts.py`:
- `CHAT_TMPL`: Chat response format
- `SUMMARY_TMPL`: Daily summary format

## Troubleshooting 🔍

### Common Issues

1. **Port Conflicts**:
   - Default port: 7860
   - Auto-kills existing process
   - Falls back to available port

2. **LLM Errors**:
   - Check API keys
   - Verify model availability
   - Check network connectivity

3. **Empty Results**:
   - Verify database population
   - Check similarity threshold
   - Validate source priorities

## Contributing 🤝

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License 📄

[Your License Here]

## Acknowledgments 🙏

- HuggingFace for embeddings model
- Gradio for web interface
- smol.ai, TechCrunch, and HuggingFace for news sources 
