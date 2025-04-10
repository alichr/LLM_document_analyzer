from src import loaders, text_processing, embeddings, vector_store, prompts, llm, context_builder

def analyze_pdf(pdf_path, query, model="llama3", embedding_model="llama3"):
    """
    Analyze a PDF document and answer a query about it.
    
    Args:
        pdf_path (str): Path to the PDF file
        query (str): Question to ask about the document
        model (str): LLM model to use for generation
        embedding_model (str): Model to use for embeddings
        
    Returns:
        str: The answer to the query
    """
    # Load the document
    docs = loaders.load_pdf(pdf_path)
    
    # Split the document with an appropriate strategy
    splits = text_processing.split_documents(docs, splitting_strategy="section", chunk_size=1000, chunk_overlap=20)
    
    # Optionally normalize chunk lengths for better embeddings
    normalized_splits = text_processing.normalize_chunk_lengths(splits)
    
    # Create embeddings
    embed_model = embeddings.get_embeddings(model=embedding_model)
    
    # Create vector store
    vs = vector_store.create_vector_store(embed_model)
    
    # Add documents to the vector store
    vector_store.add_documents_to_store(vs, normalized_splits)
    
    # Generate query embedding
    query_embedding = embed_model.embed_query(query)
    
    # Search for relevant documents
    results = vector_store.similarity_search(vs, query_embedding, k=10)
    
    # Build context using the dedicated module
    context = context_builder.build_context(results)
    
    # Generate prompt
    prompt = prompts.generate_advanced_prompt(context, query)
    
    # Generate response
    response = llm.generate_response(model, prompt)
    
    return response

if __name__ == "__main__":
    # Example usage
    file_path = "pdf_files/paper.pdf"
    query = "explain the paper in detail with proper math ifor latex format"
    response = analyze_pdf(file_path, query)
    print(response) 