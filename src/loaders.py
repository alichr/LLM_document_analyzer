from langchain_community.document_loaders import PyPDFLoader

def load_pdf(file_path):
    """
    Load a PDF file and return its documents.
    
    Args:
        file_path (str): Path to the PDF file
        
    Returns:
        list: List of document objects
    """
    loader = PyPDFLoader(file_path)
    return loader.load() 