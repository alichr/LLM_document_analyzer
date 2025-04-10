from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
import re

def split_documents(docs, chunk_size=1000, chunk_overlap=200, splitting_strategy="recursive"):
    """
    Split documents into chunks for processing with enhanced options.
    
    Args:
        docs (list): List of document objects
        chunk_size (int): Size of each chunk
        chunk_overlap (int): Overlap between chunks
        splitting_strategy (str): Strategy to use for splitting ('recursive', 'semantic', 'hybrid', 'paragraph', 'section')
        
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
            
    if splitting_strategy == "section":
        # Section-based splitting that preserves document structure with sections and subsections
        from langchain_core.documents import Document
        
        # Define section patterns
        section_patterns = [
            # Headers with numbers (e.g., "1. Introduction", "1.2 Background")
            r'^(\d+\.(?:\d+\.?)*)\s+([^\n]+)$',
            # Headers with Roman numerals (e.g., "I. Introduction", "IV.2 Methods")
            r'^([IVXivx]+\.(?:\d+\.?)*)\s+([^\n]+)$',
            # Headers with alphabetic identifiers (e.g., "A. Methods", "B.2 Results")
            r'^([A-Za-z]\.(?:\d+\.?)*)\s+([^\n]+)$',
            # Headers without numbers (e.g., "Introduction", "Materials and Methods")
            r'^(Abstract|Introduction|Methods|Materials and Methods|Results|Discussion|Conclusion|References|Acknowledgments|Appendix)(\s*\n)',
            # Markdown-style headers
            r'^(#{1,6})\s+([^\n]+)$'
        ]
        
        split_docs = []
        
        for doc in docs:
            text = doc.page_content
            lines = text.split('\n')
            sections = []
            current_section = {"title": "", "content": [], "level": 0}
            
            # Process line by line to identify sections and their content
            for line in lines:
                is_section_header = False
                section_level = 0
                
                # Check if line matches any section pattern
                for pattern in section_patterns:
                    match = re.match(pattern, line, re.MULTILINE)
                    if match:
                        is_section_header = True
                        # Determine section level based on pattern
                        if '#' in pattern:
                            # Markdown headers
                            section_level = len(match.group(1))
                        elif r'\d+\.' in pattern:
                            # Numbered headers - count dots to determine level
                            section_level = match.group(1).count('.') + 1
                        else:
                            # Main section headers
                            section_level = 1
                        break
                
                if is_section_header:
                    # Save previous section if it has content
                    if current_section["content"]:
                        sections.append(current_section)
                    
                    # Start new section
                    current_section = {
                        "title": line,
                        "content": [],
                        "level": section_level
                    }
                else:
                    # Add line to current section
                    current_section["content"].append(line)
            
            # Add the last section
            if current_section["content"]:
                sections.append(current_section)
            
            # First pass: Organize sections into their hierarchical structure
            # This is critical for maintaining document context
            organized_sections = []
            for section in sections:
                section_text = section["title"] + "\n" + "\n".join(section["content"])
                section_metadata = doc.metadata.copy()
                section_metadata["section_title"] = section["title"].strip()
                section_metadata["section_level"] = section["level"]
                
                organized_sections.append({
                    "text": section_text,
                    "metadata": section_metadata,
                    "level": section["level"]
                })
            
            # Second pass: Apply chunking with proper overlap
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
                add_start_index=True,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            
            # Process each section
            for section in organized_sections:
                # Always ensure the title is preserved at the start of chunks
                title = section["text"].split("\n")[0]
                content = "\n".join(section["text"].split("\n")[1:])
                
                # If section fits within chunk_size, keep it as is
                if len(section["text"]) <= chunk_size:
                    split_docs.append(Document(
                        page_content=section["text"],
                        metadata=section["metadata"]
                    ))
                else:
                    # Split content into chunks with overlap
                    content_chunks = []
                    
                    # First create dummy document with content for splitting
                    dummy_doc = Document(page_content=content, metadata={})
                    content_splits = text_splitter.split_documents([dummy_doc])
                    
                    # Now add the title to the first chunk and process all chunks
                    for i, chunk in enumerate(content_splits):
                        chunk_content = chunk.page_content
                        
                        # Add title to the first chunk
                        if i == 0:
                            chunk_content = title + "\n\n" + chunk_content
                        # For subsequent chunks, add title with "continued" marker
                        else:
                            # Include overlap from previous chunk
                            chunk_content = title + " (continued)\n\n" + chunk_content
                        
                        # Add to final documents
                        split_docs.append(Document(
                            page_content=chunk_content,
                            metadata=section["metadata"]
                        ))
            
            return split_docs
    
    elif splitting_strategy == "recursive":
        # Standard recursive splitting - good for most documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, 
            chunk_overlap=chunk_overlap,
            length_function=len,
            add_start_index=True,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        return text_splitter.split_documents(docs)
        
    elif splitting_strategy == "paragraph":
        # Update paragraph strategy to properly implement chunk_overlap
        from langchain_core.documents import Document
        split_docs = []
        
        for doc in docs:
            # Pre-process the document to identify paragraphs
            paragraphs = doc.page_content.split("\n\n")
            processed_paragraphs = []
            
            # Filter out empty paragraphs
            for para in paragraphs:
                if len(para.strip()) > 0:
                    processed_paragraphs.append(para)
            
            # Initialize a text splitter that respects paragraph boundaries
            # but properly implements chunk_size and chunk_overlap
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
                add_start_index=True,
                separators=["\n", ". ", " ", ""]
            )
            
            # First approach: Try to keep paragraphs intact when possible
            current_chunk = ""
            current_metadata = doc.metadata.copy()
            
            for para in processed_paragraphs:
                # If adding this paragraph would exceed chunk_size, finalize current chunk
                if current_chunk and len(current_chunk) + len(para) + 2 > chunk_size:
                    split_docs.append(Document(
                        page_content=current_chunk,
                        metadata=current_metadata
                    ))
                    
                    # Start new chunk with overlap from previous content
                    if chunk_overlap > 0:
                        # Get the last portion of the previous chunk for overlap
                        overlap_text = current_chunk[-chunk_overlap:] if len(current_chunk) > chunk_overlap else current_chunk
                        current_chunk = overlap_text + "\n\n" + para
                    else:
                        current_chunk = para
                else:
                    # Add paragraph to current chunk
                    if current_chunk:
                        current_chunk += "\n\n" + para
                    else:
                        current_chunk = para
            
            # Don't forget the last chunk
            if current_chunk:
                split_docs.append(Document(
                    page_content=current_chunk,
                    metadata=current_metadata
                ))
            
            # Second pass: split any chunks that are still too large
            final_chunks = []
            for doc in split_docs:
                if len(doc.page_content) <= chunk_size:
                    final_chunks.append(doc)
                else:
                    # Force split chunks that are too large
                    final_chunks.extend(text_splitter.split_documents([doc]))
            
            return final_chunks
    
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