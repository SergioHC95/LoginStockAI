from openai import OpenAI
import time
import json
from pathlib import Path

def load_config():
    return json.loads((Path(__file__).parent / "config.json").read_text(encoding="utf‑8"))

def run_memoryless_responder():
    config = load_config()
    client = OpenAI(api_key=config["api_key"])

    instructions = (Path(__file__).parent / config["instructions_path"])\
        .read_text(encoding="utf‑8").strip()
    file_path = Path(__file__).parent / config["email_path"]

    # Upload file
    client.files.create(file=open(file_path, "rb"), purpose="assistants")

    # Create vector store and upload file content
    vector_store = client.vector_stores.create(name="Temporary Email Store")
    with open(file_path, "rb") as f:
        client.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id,
            files=[f]
        )

    # Use Responses API with file_search tool
    response = client.responses.create(
        model=config["model"],
        input=[{"role": "user", "content": ""}],  # user input can be blank or minimal
        instructions=instructions,
        tools=[{
            "type": "file_search",
            "vector_store_ids": [vector_store.id],
            "max_num_results": 5
        }],
        include=["output[*].file_search_call.search_results"]
    )

    # Print the LLM response text
    print("\n--- Assistant Reply ---\n")
    print(response.output_text)

if __name__ == "__main__":
    run_memoryless_responder()
