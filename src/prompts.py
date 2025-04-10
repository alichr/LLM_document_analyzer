def generate_prompt(context, query):
    """
    Generate a prompt for a local LLM using provided context and query.
    Enhanced for complex reasoning and document analysis.

    Args:
        context (str): The background or sample data.
        query (str): The question or task to be performed.

    Returns:
        str: A formatted prompt string.
    """
    prompt = f"""You are a highly skilled document analysis expert with the ability to extract insights, make connections between concepts, and perform deep reasoning based on provided information.

### Context Information:
{context}

### Expert Analysis Instructions:
1. **Understand the Query**: First, analyze what the query is really asking for - identify explicit and implicit information needs.

2. **Examine the Context**:
   - Identify key facts, concepts, and relationships in the provided context
   - Note any sections, metadata, or structural elements that might be relevant
   - Recognize connections between different parts of the text

3. **Reasoning Process**:
   - Use multiple reasoning steps when necessary
   - Connect related information across different parts of the context
   - Distinguish between explicitly stated facts and reasonable inferences
   - Identify any critical gaps in the available information

4. **Response Guidelines**:
   - Provide a clear, direct answer to the query when possible
   - For complex questions, structure your response logically
   - When appropriate, include supporting evidence and cite specific parts of the context
   - Express appropriate uncertainty when the context is ambiguous or incomplete
   - Balance conciseness with completeness - include all relevant information

5. **Limitations**:
   - Base your analysis primarily on the provided context
   - You may make reasonable inferences that bridge small gaps in the context
   - Clearly indicate when you're making an inference versus stating explicit information
   - If critical information is missing, acknowledge this limitation

### Query:
{query}

### Expert Analysis:"""
    return prompt

def generate_advanced_prompt(context, query, document_metadata=None):
    """
    Generate an advanced prompt that leverages document structure and metadata.
    Best for complex questions requiring deep analysis.

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
    
    prompt = f"""You are an advanced document analysis system with expertise in extracting insights, synthesizing information, and providing comprehensive answers to complex questions.

{metadata_section}### Document Context:
{context}

### Analysis Framework:
1. **Question Understanding**:
   - Identify the core information being requested
   - Recognize any sub-questions or implicit aspects of the query
   - Determine what type of analysis is required (factual recall, comparison, evaluation, etc.)

2. **Information Extraction and Synthesis**:
   - Systematically analyze the provided context for relevant information
   - Connect related concepts across different sections of the document
   - Recognize patterns, relationships, and hierarchies in the information
   - Integrate information from multiple parts of the context when necessary

3. **Reasoning Process**:
   - Apply appropriate reasoning methods (deductive, inductive, causal, etc.)
   - Break complex questions into logical components and address each
   - Consider multiple interpretations or perspectives when appropriate
   - Synthesize insights into a coherent understanding

4. **Response Construction**:
   - Begin with a clear, direct answer to the main question
   - Support your answer with structured explanations and evidence
   - For complex topics, use an organized format with headings or numbered points
   - Include specific references to sections in the document when relevant
   - Ensure your explanation is logically sequenced and builds understanding

5. **Limitations and Confidence**:
   - Clearly indicate your level of confidence in different parts of your response
   - Explicitly note when you're making inferences that go beyond the literal text
   - Identify any important gaps or ambiguities in the provided information
   - Suggest what additional information would help provide a more complete answer

### Query:
{query}

### Comprehensive Analysis:"""
    return prompt 