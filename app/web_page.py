import os
import uuid
from flask import Flask, request, render_template, redirect, url_for, flash, jsonify, session
from werkzeug.utils import secure_filename
from src import loaders, text_processing, embeddings, vector_store, prompts, llm

app = Flask(__name__, 
           template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_for_testing')
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Ensure templates directory exists
os.makedirs(app.template_folder, exist_ok=True)

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

def answer_question(query, model="llama3"):
    """
    Answer a question based on the uploaded PDFs.
    """
    try:
        # Generate query embedding
        query_embedding = embedding_model.embed_query(query)
        
        # Search for relevant documents
        results = vector_store.similarity_search(vs, query_embedding)
        
        if not results:
            return "No relevant information found in the uploaded documents."
        
        # Format results
        formatted_chunks = []
        for i, result in enumerate(results):
            # Extract metadata
            metadata = result.metadata
            source = metadata.get('source', 'Unknown')
            page_num = metadata.get('page', 'Unknown')
            
            # Format chunk with metadata
            chunk_header = f"[CHUNK {i+1} | Source: {source} | Page: {page_num}]"
            formatted_chunks.append(f"{chunk_header}\n{result.page_content}")
        
        # Join with clear separation
        context = "\n\n" + "\n\n---\n\n".join(formatted_chunks) + "\n\n"
        
        # Generate prompt
        prompt = prompts.generate_prompt(context, query)
        
        # Generate response
        response = llm.generate_response(model, prompt)
        
        return response
    except Exception as e:
        return f"Error processing your question: {str(e)}"

@app.route('/')
def index():
    """Home page with file upload and question form."""
    # Get list of uploaded files
    uploaded_files = []
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        if filename.lower().endswith('.pdf'):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            uploaded_files.append({
                'name': filename,
                'processed': file_path in processed_files,
                'size': os.path.getsize(file_path)
            })
    
    return render_template('index.html', uploaded_files=uploaded_files)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Endpoint for file upload."""
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']
    splitting_strategy = request.form.get('splitting_strategy', 'hybrid')
    
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        # Secure the filename and save the file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Process the file with the selected splitting strategy
        success = process_pdf(file_path, splitting_strategy)
        
        if success:
            flash(f'Successfully uploaded and processed {filename} using {splitting_strategy} strategy')
        else:
            flash(f'Uploaded {filename}, but there was an error processing it')
        
        return redirect(url_for('index'))
    
    flash('Invalid file type. Please upload a PDF.')
    return redirect(url_for('index'))

@app.route('/process/<filename>')
def process_file(filename):
    """Process an existing file."""
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
    
    if not os.path.exists(file_path):
        flash(f'File not found: {filename}')
        return redirect(url_for('index'))
    
    success = process_pdf(file_path)
    
    if success:
        flash(f'Successfully processed {filename}')
    else:
        flash(f'Error processing {filename}')
    
    return redirect(url_for('index'))

@app.route('/ask', methods=['POST'])
def ask_question():
    """Endpoint for asking questions."""
    query = request.form.get('query', '')
    
    if not query:
        return jsonify({'error': 'No question provided'})
    
    if not processed_files:
        return jsonify({'error': 'No documents have been processed yet. Please upload and process a PDF first.'})
    
    answer = answer_question(query)
    
    # Store the last query and response in session
    session['last_query'] = query
    session['last_response'] = answer
    
    return jsonify({
        'query': query,
        'answer': answer
    })

if __name__ == '__main__':
    app.run(debug=True)
