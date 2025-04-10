from langchain_chroma import Chroma

def create_vector_store(embedding_function, collection_name="example_collection", persist_directory="./chroma_langchain_db"):
    """
    Create and return a vector store.
    
    Args:
        embedding_function: Function to generate embeddings
        collection_name (str): Name of the collection
        persist_directory (str): Directory to save the database
        
    Returns:
        Chroma: A vector store object
    """
    return Chroma(
        collection_name=collection_name,
        embedding_function=embedding_function,
        persist_directory=persist_directory
    )

def add_documents_to_store(vector_store, documents):
    """
    Add documents to the vector store.
    
    Args:
        vector_store: The vector store object
        documents (list): List of documents to add
        
    Returns:
        list: IDs of the added documents
    """
    return vector_store.add_documents(documents=documents)

def similarity_search(vector_store, embedding, k=5):
    """
    Search for similar documents in the vector store.
    
    Args:
        vector_store: The vector store object
        embedding: The query embedding
        k (int): Number of results to return
        
    Returns:
        list: List of similar documents
    """
    return vector_store.similarity_search_by_vector(embedding, k=k) 