import os
import sys
from together import Together
from dotenv import load_dotenv

load_dotenv()
client = Together(api_key=os.getenv("TOGETHER_API_KEY"))

if len(sys.argv) > 1:
    job_id = sys.argv[1]
    # Check specific job
    job = client.fine_tuning.retrieve(job_id)
    print(f"Job ID: {job.id}")
    print(f"Status: {job.status}")
    print(f"Model: {job.model}")
    if hasattr(job, 'output_name') and job.output_name:
        print(f"Output model name: {job.output_name}")
else:
    # List all jobs
    print("Your fine-tuning jobs:\n")
    jobs = client.fine_tuning.list()
    for job in jobs.data:
        print(f"ID: {job.id}")
        print(f"  Status: {job.status}")
        print(f"  Model: {job.model}")
        if hasattr(job, 'output_name') and job.output_name:
            print(f"  Output: {job.output_name}")
        print()
