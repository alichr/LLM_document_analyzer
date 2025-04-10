def generate_prompt(context, query):
    """
    Generate a prompt for a local LLM using provided context and query.
    Designed for direct, concise answers without unnecessary information.

    Args:
        context (str): The background or sample data.
        query (str): The question or task to be performed.

    Returns:
        str: A formatted prompt string.
    """
    prompt = f"""You are a document assistant that provides direct, concise answers.

### Context:
{context}

### Instructions:
- Answer the query below using ONLY the information in the context.
- Provide DIRECT answers without explanations unless specifically requested.
- Keep responses brief and focused on exactly what was asked.
- Do not include background information or reasoning steps.
- Do not introduce yourself or add conclusions/summaries.
- If the information isn't in the context, simply state that briefly.

### Query:
{query}

### Response:"""
    return prompt

def generate_advanced_prompt(context, query, document_metadata=None):
    """
    Generate an advanced prompt for complex questions that still requires
    direct, concise answers.

    Args:
        context (str): The background or sample data.
        query (str): The question or task to be performed.
        document_metadata (dict, optional): Additional metadata about document structure.

    Returns:
        str: A formatted prompt string.
    """
    metadata_section = ""
    if document_metadata:
        metadata_items = []
        for key, value in document_metadata.items():
            metadata_items.append(f"- {key}: {value}")
        metadata_section = "### Document Metadata:\n" + "\n".join(metadata_items) + "\n\n"
    
    prompt = f"""You are a document assistant that provides direct, concise answers.

{metadata_section}### Document Context:
{context}

### Instructions:
- Answer the query directly and concisely.
- Focus only on the exact information requested.
- Do not include explanations, reasoning, or your thought process.
- Omit introductions, conclusions, and summaries.
- Provide only facts from the document that directly answer the question.
- For complex questions, organize your response clearly but still be concise.
- If the information isn't in the context, simply state that briefly.

### Query:
{query}

### Direct Response:"""
    return prompt 