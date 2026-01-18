import json

# Load your coaching dialogs
with open("coaching_dialogs.json", "r") as f:
    dialogs = json.load(f)

# System prompt for the fine-tuned model
SYSTEM_PROMPT = """You are a tennis mental performance coach. You help players with the psychological aspects of tennis: confidence, pressure, nerves, focus, motivation, and emotional regulation.

Your style is:
- Direct and concise
- Encouraging but honest
- Process-focused, not outcome-focused
- You ask clarifying questions to help players think deeper
- You reframe negative thoughts into actionable insights"""

# Convert to Together AI JSONL format
training_data = []

for dialog_name, dialog in dialogs.items():
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(dialog["messages"])
    training_data.append({"messages": messages})

# Write JSONL file
with open("training_data.jsonl", "w") as f:
    for item in training_data:
        f.write(json.dumps(item) + "\n")

print(f"Created training_data.jsonl with {len(training_data)} conversations")
print(f"Total turns: {sum(len(d['messages']) for d in training_data)}")
