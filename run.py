from src import main

if __name__ == "__main__":
    # Example usage
    file_path = "pdf_files/2306.13549v4.pdf"
    query = "who are the authors of the paper?"
    response = main.analyze_pdf(file_path, query)
    print(response) 