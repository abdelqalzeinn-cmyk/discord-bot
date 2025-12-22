from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import openai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure OpenAI API
openai.api_key = os.getenv('OPENAI_API_KEY')

# Store conversation history
conversation_history = []

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Add user message to conversation history
        conversation_history.append({"role": "user", "content": user_message})
        
        # Get response from OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=conversation_history
        )
        
        # Extract the assistant's reply
        assistant_reply = response.choices[0].message['content']
        
        # Add assistant's reply to conversation history
        conversation_history.append({"role": "assistant", "content": assistant_reply})
        
        return jsonify({
            'reply': assistant_reply
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
