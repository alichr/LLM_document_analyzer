# PDF Analysis and Question Answering System

This project is a PDF analysis tool that allows users to upload PDF documents and ask questions about their content. It uses a combination of document processing, embeddings, and a language model to provide accurate answers based on the document's content.

## Features

- **PDF Upload**: Upload PDF files through a web interface.
- **Document Processing**: Automatically processes and splits documents into manageable chunks.
- **Embeddings**: Generates embeddings for document chunks and stores them in a vector database.
- **Question Answering**: Allows users to ask questions about the uploaded documents and receive answers based on the content.
- **Web Interface**: User-friendly web interface built with Flask and Bootstrap.
- **Multiple Splitting Strategies**: Choose between recursive, semantic, or hybrid document splitting approaches.
- **Vector Search**: Efficiently finds the most relevant document sections for each query.

## Project Structure 


project/
├── app/
│ ├── web_page.py # Flask web application
│ ├── static/ # Static assets (CSS, JS)
│ └── templates/
│ └── index.html # HTML template for the web interface
├── src/
│ ├── init.py # Package initialization
│ ├── main.py # Main analysis logic
│ ├── context_builder.py # Context building for LLM prompts
│ ├── loaders.py # PDF loading utilities
│ ├── text_processing.py # Document splitting utilities
│ ├── embeddings.py # Embedding model functionality
│ ├── vector_store.py # Vector database functionality
│ ├── prompts.py # Prompt generation functionality
│ └── llm.py # Language model interface
├── uploads/ # Directory for uploaded PDF files
├── chroma_db/ # Vector database storage
├── requirements.txt # Project dependencies
├── README.md # This documentation file
└── run.py # Command-line script for PDF analysis

## How It Works

1. **Document Loading**: PDFs are loaded and parsed using LangChain's PyPDFLoader.
2. **Text Splitting**: Documents are split into chunks using one of three strategies:
   - **Recursive**: Standard text splitting based on character count
   - **Semantic**: Splits based on section boundaries and headers
   - **Hybrid**: Combines both approaches for optimal results
3. **Embedding Generation**: Creates vector embeddings for each document chunk using Ollama.
4. **Vector Storage**: Stores embeddings in a Chroma vector database for efficient retrieval.
5. **Query Processing**: When a question is asked:
   - Converts the query to an embedding
   - Performs similarity search to find relevant document chunks
   - Builds a context from the most relevant chunks
   - Generates a prompt that combines the context and query
   - Sends the prompt to a language model
   - Returns the model's response

## Requirements

- Python 3.7+
- Flask 2.0+
- LangChain
- Ollama
- Chroma DB
- PyPDF2
- Werkzeug

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/pdf-analysis-system.git
   cd pdf-analysis-system
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Ollama** (if not already installed):
   Follow the instructions at [https://ollama.com/download](https://ollama.com/download)

4. **Download Required Models** for Ollama:
   ```bash
   ollama pull llama3
   ollama pull nomic-embed-text
   ```

## Usage

### Web Interface

1. **Start the Web Server**:
   ```bash
   python app/web_page.py
   ```

2. **Access the Interface**:
   Open your web browser and navigate to `http://127.0.0.1:5000/`

3. **Upload a PDF**:
   - Click "Choose File" to select a PDF
   - Select a splitting strategy (hybrid recommended for most documents)
   - Click "Upload & Process"

4. **Ask Questions**:
   - Type your question in the text area
   - Click "Ask"
   - View the response in the answer section

### Command Line

For batch processing or programmatic use:

```python
from src import main

# Analyze a PDF and get an answer
response = main.analyze_pdf(
    pdf_path="path/to/your/document.pdf",
    query="What is the main topic of this document?",
    model="llama3",
    embedding_model="nomic-embed-text"
)
print(response)
```

## Advanced Configuration

### Customizing Splitting Parameters

You can adjust document splitting parameters in `text_processing.py`:

```python
# Adjust chunk size and overlap
splits = text_processing.split_documents(
    docs, 
    chunk_size=800,  # Default is 1000
    chunk_overlap=100,  # Default is 200
    splitting_strategy="hybrid"
)
```

### Using Different LLM Models

The system supports any model available in Ollama:

```python
# Use a different model
response = main.analyze_pdf(
    pdf_path="document.pdf",
    query="What is this about?",
    model="vicuna:7b-16k-q5_K_M",  # Change to any available Ollama model
    embedding_model="nomic-embed-text"
)
```

## Troubleshooting

### Common Issues

- **PDF Loading Failures**: Ensure your PDFs are not password-protected and are valid PDF files.
- **Out of Memory Errors**: Try reducing the chunk size in text processing.
- **Slow Processing**: Large PDFs may take time to process. Consider using a smaller chunk size or using the semantic splitting strategy.

### Model Issues

If you encounter problems with the language model:

1. Check that Ollama is running: `ollama ps`
2. Ensure the models are downloaded: `ollama list`
3. For embedding issues, try: `ollama pull nomic-embed-text --force`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [LangChain](https://python.langchain.com/) for document processing and vector store capabilities
- [Ollama](https://ollama.com/) for local LLM hosting
- [Chroma](https://www.trychroma.com/) for vector database functionality
- [Flask](https://flask.palletsprojects.com/) for the web framework

