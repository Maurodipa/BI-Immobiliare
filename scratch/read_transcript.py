import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r"C:\Users\mauro\.gemini\antigravity\brain\175b7fe0-188c-4061-a9c8-745b4b82a986\.system_generated\logs\transcript.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        data = json.loads(line)
        idx = data.get("step_index")
        if idx in range(2225, 2246):
            print(f"STEP {idx} ({data.get('source')} - {data.get('type')}):")
            content = data.get("content", "")
            if content:
                print(content[:600])
            if data.get("tool_calls"):
                print("TOOL CALLS:", [tc["name"] for tc in data["tool_calls"]])
            print("="*50)
