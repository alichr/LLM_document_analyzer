document.addEventListener('DOMContentLoaded', function() {
    const questionForm = document.getElementById('question-form');
    if (questionForm) {
        questionForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const query = document.getElementById('query').value;
            if (!query) return;
            
            // Show loading spinner
            document.getElementById('loading').style.display = 'block';
            document.getElementById('answer-container').style.display = 'none';
            
            // Send request
            fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: 'query=' + encodeURIComponent(query)
            })
            .then(response => response.json())
            .then(data => {
                // Hide loading spinner
                document.getElementById('loading').style.display = 'none';
                document.getElementById('answer-container').style.display = 'block';
                
                // Update answer
                document.getElementById('question-text').textContent = data.query;
                document.getElementById('answer-text').textContent = data.answer;
            })
            .catch(error => {
                console.error('Error:', error);
                document.getElementById('loading').style.display = 'none';
                alert('An error occurred while processing your question.');
            });
        });
    }
}); 