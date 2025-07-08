# LoginStockAI

System for retrieving, threading, and processing email conversations using AI prompts.

## Setup

1. Create config files from examples:
   ```
   cp fetcher/config.example.json fetcher/config.json
   cp assistant/assistant.config.example.json assistant/config.json
   cp assistant/instructions.example.txt assistant/instructions.txt
   ```

2. (Optional) Set up environment:
   ```
   conda env create -f environment.yaml
   conda activate loginstockai
   ```

## Run

Main entry point:
```
python main.py
```

This fetches emails and prepares them for downstream processing.

## Assistant

The assistant module takes a thread and a prompt, and returns structured analysis or a response suggestion. The behavior is configured via `assistant/config.json` and `instructions.txt` (prompt).

Both modules are under active development. Future versions will include classification, task extraction, and integrated workflows.