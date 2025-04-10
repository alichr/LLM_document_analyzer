def build_context(results):
    """
    Build a structured context from search results for use in prompts.
    
    Args:
        results (list): List of document objects from vector store search
        
    Returns:
        str: Formatted context string with metadata and clear separation
    """
    formatted_chunks = []
    for i, result in enumerate(results):
        # Extract metadata if available
        metadata = result.metadata
        page_num = metadata.get('page', 'Unknown')
        start_idx = metadata.get('start_index', 'Unknown')
        
        # Format chunk with metadata and index
        chunk_header = f"[CHUNK {i+1} | Page: {page_num} | Index: {start_idx}]"
        formatted_chunks.append(f"{chunk_header}\n{result.page_content}")
    
    # Join with clear separation between chunks
    context = "\n\n" + "\n\n---\n\n".join(formatted_chunks) + "\n\n"
    
    return context 