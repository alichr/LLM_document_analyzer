from langchain_ollama import OllamaEmbeddings

def get_embeddings(model="nomic-embed-text"):
    """
    Create and return an embeddings object.
    
    Args:
        model (str): Name of the model to use
        
    Returns:
        OllamaEmbeddings: An embeddings object
    """
    return OllamaEmbeddings(model=model) 