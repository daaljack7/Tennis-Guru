import os
import sys
import chromadb
from dotenv import load_dotenv
from together import Together
from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS

load_dotenv()

# Force unbuffered output for logging
sys.stdout = sys.stderr

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

client = Together(api_key=os.getenv("TOGETHER_API_KEY"))

# Connect to the same database we built in ingest.py
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_collection(name="pdf_knowledge")

SYSTEM_PROMPT = """You are a tennis mental performance coach.

You also know "The Inner Game of Tennis" by Timothy Gallwey. Key concepts you can reference when relevant:
- Self 1: The conscious, critical mind that overthinks and judges
- Self 2: The body's natural ability that performs best when trusted
- Quieting Self 1 and trusting Self 2 leads to peak performance

Use your natural coaching style. When Inner Game concepts fit, weave them in - but don't force them.

RULES:
- If asked about something unrelated to tennis, say "I can only help with tennis-related questions."
- Don't end responses with questions like "Does that make sense?" or "What do you think?" - give your advice and let the player respond when they're ready. Only ask a question if you genuinely need more information to help them.
- When the player thanks you or shows appreciation, give a brief encouraging recap of what you discussed and ask "Is there anything else I can help with?"
- When the player indicates they're done (says no, nothing else, that's all, etc.), close warmly with something like "Happy I could help! Let me know how it goes. You got this!"
"""

# Store conversations per session
conversations = {}

def get_bot_response(question, session_id):
    # Get or create conversation for this session
    if session_id not in conversations:
        conversations[session_id] = {
            'history': [],
            'self_concepts_explained': False
        }

    conv = conversations[session_id]

    try:
        # 1. Turn the question into a vector
        q_res = client.embeddings.create(
            model="togethercomputer/m2-bert-80M-32k-retrieval",
            input=question
        )
        q_vector = q_res.data[0].embedding

        # 2. Find the top 5 matching chunks from The Inner Game of Tennis
        results = collection.query(query_embeddings=[q_vector], n_results=5)
        context = "\n\n---\n\n".join(results['documents'][0])
    except Exception as e:
        print(f"[ERROR] RAG failed: {e}")
        context = ""

    # 3. Add user message to history
    conv['history'].append({"role": "user", "content": question})

    # 4. Build messages with system prompt, context, and conversation history
    system_content = f"{SYSTEM_PROMPT}\n\n--- REFERENCE MATERIAL (use if relevant) ---\n{context}\n---"

    # Add instruction to explain Self 1/Self 2 if not yet explained
    if not conv['self_concepts_explained']:
        system_content += "\n\nNote: If you mention Self 1 or Self 2, briefly explain what they mean since this player may not know."

    messages = [
        {"role": "system", "content": system_content}
    ] + conv['history']

    # 5. Get response from fine-tuned model
    tokens = 400 if not conv['self_concepts_explained'] else 300
    try:
        response = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            messages=messages,
            max_tokens=tokens
        )
        assistant_message = response.choices[0].message.content
    except Exception as e:
        print(f"[ERROR] Model call failed: {e}")
        assistant_message = "I'm sorry, I'm having trouble right now. Please try again."

    # Trim incomplete sentences if response was cut off
    if assistant_message and assistant_message[-1] not in '.!?':
        last_period = assistant_message.rfind('.')
        last_exclaim = assistant_message.rfind('!')
        last_question = assistant_message.rfind('?')
        last_end = max(last_period, last_exclaim, last_question)
        if last_end > 0:
            assistant_message = assistant_message[:last_end + 1]

    # Mark Self 1/Self 2 as explained after first response
    if not conv['self_concepts_explained']:
        conv['self_concepts_explained'] = True

    # Add assistant response to history
    conv['history'].append({"role": "assistant", "content": assistant_message})

    # Keep only last 10 exchanges to avoid token limits
    if len(conv['history']) > 20:
        conv['history'] = conv['history'][-20:]

    return assistant_message

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    session_id = data.get('session_id', 'default')

    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    response = get_bot_response(user_message, session_id)
    return jsonify({'response': response})

@app.route('/new-chat', methods=['POST'])
def new_chat():
    data = request.json
    session_id = data.get('session_id', 'default')

    if session_id in conversations:
        del conversations[session_id]

    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
