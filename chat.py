import os
import chromadb
from dotenv import load_dotenv
from together import Together

load_dotenv()
client = Together(api_key=os.getenv("TOGETHER_API_KEY"))

# Connect to the same database we built in ingest.py
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_collection(name="pdf_knowledge")

# Conversation history for memory
conversation_history = []

# Track if we've explained Self 1/Self 2 yet
self_concepts_explained = False

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

def ask_bot(question):
    global conversation_history, self_concepts_explained

    # 1. Turn the question into a vector
    q_res = client.embeddings.create(
        model="togethercomputer/m2-bert-80M-32k-retrieval",
        input=question
    )
    q_vector = q_res.data[0].embedding

    # 2. Find the top 5 matching chunks from The Inner Game of Tennis
    results = collection.query(query_embeddings=[q_vector], n_results=5)
    context = "\n\n---\n\n".join(results['documents'][0])

    # 3. Add user message to history
    conversation_history.append({"role": "user", "content": question})

    # 4. Build messages with system prompt, context, and conversation history
    system_content = f"{SYSTEM_PROMPT}\n\n--- REFERENCE MATERIAL (use if relevant) ---\n{context}\n---"

    # Add instruction to explain Self 1/Self 2 if not yet explained
    if not self_concepts_explained:
        system_content += "\n\nNote: If you mention Self 1 or Self 2, briefly explain what they mean since this player may not know."

    messages = [
        {"role": "system", "content": system_content}
    ] + conversation_history

    # 5. Get response from fine-tuned model
    # Allow more tokens on first response to explain Self 1/Self 2
    tokens = 400 if not self_concepts_explained else 300
    response = client.chat.completions.create(
        model="daaljack7_5be9/Meta-Llama-3.1-8B-Instruct-Reference-tennis-coach-aa641c3d",
        messages=messages,
        max_tokens=tokens
    )

    assistant_message = response.choices[0].message.content

    # Trim incomplete sentences if response was cut off
    if assistant_message and assistant_message[-1] not in '.!?':
        # Find the last complete sentence
        last_period = assistant_message.rfind('.')
        last_exclaim = assistant_message.rfind('!')
        last_question = assistant_message.rfind('?')
        last_end = max(last_period, last_exclaim, last_question)
        if last_end > 0:
            assistant_message = assistant_message[:last_end + 1]

    # 6. Mark Self 1/Self 2 as explained after first response
    if not self_concepts_explained:
        self_concepts_explained = True

    # 7. Add assistant response to history
    conversation_history.append({"role": "assistant", "content": assistant_message})

    # 8. Keep only last 10 exchanges to avoid token limits
    if len(conversation_history) > 20:
        conversation_history = conversation_history[-20:]

    return assistant_message

if __name__ == "__main__":
    try:
        print("Greetings! I am your Tennis Guru. I specialize in helping you improve your mental game on the court. How can I help you today?")
        while True:
            query = input("\n")
            print("\n\n")
            print(ask_bot(query))
    except KeyboardInterrupt:
        print("\nGoodbye! Keep practicing and improving your game! Always believe in yourself.")