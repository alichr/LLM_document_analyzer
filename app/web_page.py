import os
import uuid
import json
from flask import Flask, request, render_template, redirect, url_for, flash, jsonify, session, send_from_directory
from werkzeug.utils import secure_filename
from src import loaders, text_processing, embeddings, vector_store, prompts, llm

app = Flask(__name__, 
           template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'),
           static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'))
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_for_testing')
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32 MB max upload size
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Ensure directories exist with proper permissions
upload_folder = os.path.join(os.getcwd(), 'uploads')
app.config['UPLOAD_FOLDER'] = upload_folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Check write permissions
try:
    test_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'test_write.txt')
    with open(test_file_path, 'w') as f:
        f.write('test')
    os.remove(test_file_path)
    print(f"Upload directory is writable: {app.config['UPLOAD_FOLDER']}")
except Exception as e:
    print(f"WARNING: Upload directory is not writable: {e}")
    # Try to fix permissions
    try:
        import stat
        os.chmod(app.config['UPLOAD_FOLDER'], 
                 stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)
        print("Attempted to fix directory permissions")
    except Exception as e:
        print(f"Could not fix permissions: {e}")

# Ensure directories exist
os.makedirs(app.template_folder, exist_ok=True)
os.makedirs(os.path.join(app.static_folder, 'css'), exist_ok=True)
os.makedirs(os.path.join(app.static_folder, 'js'), exist_ok=True)

# Initialize embeddings and vector store
embedding_model = embeddings.get_embeddings(model="nomic-embed-text")
vs = vector_store.create_vector_store(
    embedding_model, 
    collection_name="pdf_documents",
    persist_directory="./chroma_db"
)

# Track processed files to avoid reprocessing
processed_files = set()

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def process_pdf(file_path, splitting_strategy="hybrid"):
    """Process a PDF file and add it to the vector store."""
    if file_path in processed_files:
        return

    try:
        # Load the document
        docs = loaders.load_pdf(file_path)
        
        # Add filename to metadata
        filename = os.path.basename(file_path)
        for doc in docs:
            doc.metadata['source'] = filename
        
        # Split the document with the selected strategy
        splits = text_processing.split_documents(docs, splitting_strategy=splitting_strategy)
        
        # Normalize chunk lengths for better embeddings
        normalized_splits = text_processing.normalize_chunk_lengths(splits)
        
        # Add documents to the vector store
        vector_store.add_documents_to_store(vs, normalized_splits)
        
        # Mark file as processed
        processed_files.add(file_path)
        
        return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def get_document_metadata(filename):
    """Get document metadata for enhancing prompt capabilities."""
    # This could be enhanced to extract real document structure
    return {
        "filename": filename,
        "processing_strategy": "hybrid",
        "total_chunks": "N/A",  # You could calculate this
    }

def answer_question(query, model="llama3", active_file=None):
    """
    Answer a question based on the uploaded PDFs with enhanced context awareness.
    """
    try:
        # Generate query embedding
        query_embedding = embedding_model.embed_query(query)
        
        # First get all relevant results
        results = vector_store.similarity_search(vs, query_embedding)
        
        # If we have an active file, filter results manually
        if active_file and results:
            filtered_results = [r for r in results if r.metadata.get('source') == active_file]
            
            # Only use the filtered results if we found some, otherwise fall back to all results
            if filtered_results:
                results = filtered_results
        
        if not results:
            return "No relevant information found in the uploaded documents."
        
        # Extract document metadata for advanced prompting
        document_metadata = {}
        if results and "source" in results[0].metadata:
            document_metadata = get_document_metadata(results[0].metadata["source"])
        
        # Format results
        formatted_chunks = []
        for i, result in enumerate(results):
            # Extract metadata
            metadata = result.metadata
            source = metadata.get('source', 'Unknown')
            page_num = metadata.get('page', 'Unknown')
            section_title = metadata.get('section_title', '')
            
            # Format chunk with metadata
            chunk_header = f"[CHUNK {i+1} | Source: {source} | Page: {page_num}"
            if section_title:
                chunk_header += f" | Section: {section_title}"
            chunk_header += "]"
            
            formatted_chunks.append(f"{chunk_header}\n{result.page_content}")
        
        # Join with clear separation
        context = "\n\n" + "\n\n---\n\n".join(formatted_chunks) + "\n\n"
        
        # Generate prompt (use advanced prompt for complex questions)
        if len(query.split()) > 8 or '?' in query or any(word in query.lower() for word in ['explain', 'compare', 'analyze', 'why', 'how']):
            # Likely a complex question - use advanced prompt
            prompt = prompts.generate_advanced_prompt(context, query, document_metadata)
        else:
            # Simple question - use standard prompt
            prompt = prompts.generate_prompt(context, query)
        
        # Generate response
        response = llm.generate_response(model, prompt)
        
        return response
    except Exception as e:
        return f"Error processing your question: {str(e)}"

@app.route('/')
def index():
    """Modern home page with PDF viewer and chat interface."""
    # Get list of uploaded files
    uploaded_files = []
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        if filename.lower().endswith('.pdf'):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            uploaded_files.append({
                'name': filename,
                'processed': file_path in processed_files,
                'size': os.path.getsize(file_path),
                'url': url_for('serve_pdf', filename=filename)
            })
    
    # Get chat history if it exists
    chat_history = session.get('chat_history', [])
    active_document = session.get('active_document', '')
    
    return render_template('modern_index.html', 
                          uploaded_files=uploaded_files, 
                          chat_history=chat_history,
                          active_document=active_document)

@app.route('/pdf/<filename>')
def serve_pdf(filename):
    """Serve a PDF file for viewing."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], 
                              secure_filename(filename))

@app.route('/upload', methods=['POST'])
def upload_file():
    """Enhanced endpoint for file upload with AJAX support."""
    if 'file' not in request.files:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'No file part'})
        flash('No file part')
        return redirect(url_for('index'))
    
    file = request.files['file']
    splitting_strategy = request.form.get('splitting_strategy', 'section')
    
    if file.filename == '':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'No selected file'})
        flash('No selected file')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        # Secure the filename and save the file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Process the file with the selected splitting strategy
        success = process_pdf(file_path, splitting_strategy)
        
        # Set as active document
        session['active_document'] = filename
        
        # AJAX response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': success,
                'filename': filename,
                'message': f'Successfully processed {filename}' if success else f'Error processing {filename}',
                'url': url_for('serve_pdf', filename=filename)
            })
            
        # Regular form submission response
        if success:
            flash(f'Successfully uploaded and processed {filename}')
        else:
            flash(f'Uploaded {filename}, but there was an error processing it')
        
        return redirect(url_for('index'))
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'error': 'Invalid file type. Please upload a PDF.'})
    
    flash('Invalid file type. Please upload a PDF.')
    return redirect(url_for('index'))

@app.route('/set_active_document', methods=['POST'])
def set_active_document():
    """Set the currently active document for the chat interface."""
    filename = request.form.get('filename', '')
    
    if filename and secure_filename(filename) in os.listdir(app.config['UPLOAD_FOLDER']):
        session['active_document'] = filename
        return jsonify({'success': True, 'active_document': filename})
    else:
        return jsonify({'success': False, 'error': 'Invalid document'})

@app.route('/ask', methods=['POST'])
def ask_question():
    """Enhanced endpoint for asking questions with chat history support."""
    query = request.form.get('query', '')
    active_document = request.form.get('active_document', session.get('active_document', ''))
    
    if not query:
        return jsonify({'error': 'No question provided'})
    
    if not processed_files:
        return jsonify({'error': 'No documents have been processed yet. Please upload and process a PDF first.'})
    
    # Get chat history or initialize if not exists
    chat_history = session.get('chat_history', [])
    
    # Fix datetime usage - import properly
    import datetime
    current_time = datetime.datetime.now().strftime('%H:%M')
    
    # Add user message to history
    chat_history.append({
        'role': 'user',
        'content': query,
        'timestamp': current_time
    })
    
    # Generate answer considering active document
    answer = answer_question(query, active_file=active_document if active_document else None)
    
    # Add assistant response to history
    chat_history.append({
        'role': 'assistant',
        'content': answer,
        'timestamp': current_time
    })
    
    # Update session
    session['chat_history'] = chat_history
    session['last_query'] = query
    session['last_response'] = answer
    
    return jsonify({
        'query': query,
        'answer': answer,
        'chat_history': chat_history
    })

@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    """Clear the chat history."""
    session.pop('chat_history', None)
    session.pop('last_query', None)
    session.pop('last_response', None)
    
    return jsonify({'success': True, 'message': 'Chat history cleared'})

@app.route('/debug/upload', methods=['GET'])
def debug_upload():
    """Diagnostic endpoint for upload functionality."""
    upload_dir = app.config['UPLOAD_FOLDER']
    is_dir = os.path.isdir(upload_dir)
    is_writable = os.access(upload_dir, os.W_OK)
    
    files = []
    if is_dir:
        try:
            files = os.listdir(upload_dir)
        except Exception as e:
            files = [f"Error listing files: {str(e)}"]
    
    debug_info = {
        'upload_dir': upload_dir,
        'is_directory': is_dir,
        'is_writable': is_writable,
        'current_working_dir': os.getcwd(),
        'files_in_upload_dir': files,
        'config': {k: str(v) for k, v in app.config.items() if k in ['UPLOAD_FOLDER', 'MAX_CONTENT_LENGTH', 'ALLOWED_EXTENSIONS']}
    }
    
    return jsonify(debug_info)

@app.route('/test_model', methods=['GET'])
def test_model():
    """Test if the model is working properly."""
    try:
        # Simple test query
        response = llm.generate_response("llama3", "Hello, can you provide a short test response?")
        return jsonify({
            'success': True,
            'response': response,
            'message': 'Model is working correctly'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Error testing model'
        })

@app.route('/debug/search', methods=['GET'])
def debug_search():
    """Debug endpoint to test search functionality."""
    query = request.args.get('query', 'test')
    
    try:
        # Generate query embedding
        query_embedding = embedding_model.embed_query(query)
        
        # Get all search results
        results = vector_store.similarity_search(vs, query_embedding)
        
        # Format results for display
        formatted_results = []
        for i, result in enumerate(results):
            formatted_results.append({
                'index': i,
                'content': result.page_content[:100] + '...',  # First 100 chars
                'metadata': result.metadata
            })
        
        return jsonify({
            'success': True,
            'query': query,
            'results_count': len(results),
            'results': formatted_results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Error testing search functionality'
        })

def import_datetime():
    """Import datetime module (helper for timestamp generation)."""
    import datetime
    return datetime.datetime  # Return datetime class, not the module

if __name__ == '__main__':
    app.run(debug=True)

