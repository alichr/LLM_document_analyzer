import ollama

def generate_response(model, prompt):
    """
    Generate a response from an LLM.
    
    Args:
        model (str): Name of the model to use
        prompt (str): The prompt to send to the model
        
    Returns:
        str: The model's response
    """
    response = ollama.generate(model=model, prompt=prompt)
    return response.response 