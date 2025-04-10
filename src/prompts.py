def generate_prompt(context, query):
    """
    Generate a prompt for a local LLM using provided context and query.

    Args:
        context (str): The background or sample data.
        query (str): The question or task to be performed.

    Returns:
        str: A formatted prompt string.
    """
    prompt = f"""You are a helpful and knowledgeable assistant specialized in answering questions about documents.

### Context:
{context}

### Instructions:
- Answer the query below using ONLY the information provided in the context above.
- If the context doesn't contain enough information to give a complete answer, say so clearly and explain what's missing.
- If you're unsure about something, express your uncertainty rather than guessing.
- When referencing specific information, indicate which part of the context it came from.
- Keep your response concise and to the point.
- DO NOT make up information that isn't in the context.

### Query:
{query}

### Response:"""
    return prompt 