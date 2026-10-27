import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r"C:\Users\mauro\.gemini\antigravity\brain\175b7fe0-188c-4061-a9c8-745b4b82a986\.system_generated\logs\transcript.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        data = json.loads(line)
        if data.get('step_index') == 2094:
            print(data.get('content'))
