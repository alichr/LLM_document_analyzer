from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
import re

def split_documents(docs, chunk_size=1000, chunk_overlap=200, splitting_strategy="recursive"):
    """
    Split documents into chunks for processing with enhanced options.
    
    Args:
        docs (list): List of document objects
        chunk_size (int): Size of each chunk
        chunk_overlap (int): Overlap between chunks
        splitting_strategy (str): Strategy to use for splitting ('recursive', 'semantic', or 'hybrid')
        
    Returns:
        list: List of split document chunks
    """
    # Preserve original metadata
    for doc in docs:
        if not hasattr(doc, 'metadata') or doc.metadata is None:
            doc.metadata = {}
        # Ensure page numbers are included in metadata
        if 'page' not in doc.metadata and hasattr(doc, 'page'):
            doc.metadata['page'] = doc.page
            
    if splitting_strategy == "recursive":
        # Standard recursive splitting - good for most documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, 
            chunk_overlap=chunk_overlap,
            length_function=len,
            add_start_index=True,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        return text_splitter.split_documents(docs)
        
    elif splitting_strategy == "semantic":
        # Try to split on semantic boundaries like headers
        # This is better for structured documents like academic papers
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
            ("####", "Header 4"),
            ("Abstract", "Abstract"),
            ("Introduction", "Introduction"),
            ("Conclusion", "Conclusion"),
            ("References", "References")
        ]
        
        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        split_docs = []
        
        for doc in docs:
            # Convert section titles to markdown headers for splitting
            text = doc.page_content
            text = re.sub(r'^(Abstract|Introduction|Methodology|Results|Discussion|Conclusion|References)(\s*\n)', r'# \1\2', text, flags=re.MULTILINE)
            
            # Get markdown splits
            md_splits = markdown_splitter.split_text(text)
            
            # Create documents from splits with metadata
            for split in md_splits:
                split_metadata = doc.metadata.copy()
                # Add section info to metadata
                for header_key in split.metadata:
                    split_metadata[f"section_{header_key}"] = split.metadata[header_key]
                
                # Create new document
                from langchain_core.documents import Document
                new_doc = Document(page_content=split.page_content, metadata=split_metadata)
                split_docs.append(new_doc)
        
        # Apply regular splitting as well but with smaller chunks since we already did semantic splitting
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size // 2,  # Smaller chunks since we've already split semantically
            chunk_overlap=chunk_overlap,
            add_start_index=True
        )
        return text_splitter.split_documents(split_docs)
        
    elif splitting_strategy == "hybrid":
        # First split by semantic boundaries, then by size
        # Start with semantic splitting
        semantic_docs = split_documents(docs, chunk_size, chunk_overlap, "semantic")
        
        # Then apply size-based splitting
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            add_start_index=True
        )
        return text_splitter.split_documents(semantic_docs)
        
    else:
        # Default to recursive splitting if an unknown strategy is specified
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, 
            chunk_overlap=chunk_overlap,
            add_start_index=True
        )
        return text_splitter.split_documents(docs)

def normalize_chunk_lengths(chunks, target_length=800):
    """
    Normalize chunk lengths to improve embedding quality.
    Very short or very long chunks can lead to poor embeddings.
    
    Args:
        chunks (list): List of document chunks
        target_length (int): Target character count for chunks
        
    Returns:
        list: List of normalized document chunks
    """
    normalized_chunks = []
    buffer = ""
    buffer_metadata = None
    
    for chunk in chunks:
        # If we have no buffer, start with this chunk
        if not buffer:
            buffer = chunk.page_content
            buffer_metadata = chunk.metadata
            continue
            
        # If adding this chunk would get us closer to target length, add it
        if len(buffer) < target_length and len(buffer) + len(chunk.page_content) <= target_length * 1.5:
            buffer += "\n\n" + chunk.page_content
            # Merge metadata, keeping the earlier page number
            if 'page' in chunk.metadata and 'page' in buffer_metadata:
                buffer_metadata = {**chunk.metadata, 'page': buffer_metadata['page']}
            else:
                buffer_metadata = {**buffer_metadata, **chunk.metadata}
        else:
            # Buffer is full or adding would make it too long
            from langchain_core.documents import Document
            normalized_chunks.append(Document(page_content=buffer, metadata=buffer_metadata))
            buffer = chunk.page_content
            buffer_metadata = chunk.metadata
    
    # Don't forget the last buffer
    if buffer:
        from langchain_core.documents import Document
        normalized_chunks.append(Document(page_content=buffer, metadata=buffer_metadata))
    
    return normalized_chunks 