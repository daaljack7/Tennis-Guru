import os
from together import Together
from dotenv import load_dotenv

load_dotenv()
client = Together(api_key=os.getenv("TOGETHER_API_KEY"))

# Step 1: Upload the training file
print("Uploading training data...")
file_response = client.files.upload(
    file="training_data.jsonl",
    purpose="fine-tune"
)
file_id = file_response.id
print(f"File uploaded! ID: {file_id}")

# Step 2: Start fine-tuning job
print("\nStarting fine-tuning job with LoRA...")
finetune_response = client.fine_tuning.create(
    training_file=file_id,
    model="meta-llama/Meta-Llama-3.1-8B-Instruct-Reference",
    n_epochs=3,
    n_checkpoints=1,
    batch_size="max",
    learning_rate=1e-5,
    lora=True,
    train_on_inputs="auto",
    suffix="tennis-coach"
)

print(f"\nFine-tuning job started!")
print(f"Job ID: {finetune_response.id}")
print(f"Status: {finetune_response.status}")
print(f"\nYour fine-tuned model will be named something like:")
print(f"  {os.getenv('TOGETHER_API_KEY')[:8]}.../{finetune_response.model}-tennis-coach")
print(f"\nCheck status at: https://api.together.xyz/playground")
print(f"Or run: python check_finetune.py {finetune_response.id}")
