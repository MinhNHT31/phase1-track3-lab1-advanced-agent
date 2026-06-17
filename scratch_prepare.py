import zipfile
import json
import random
from pathlib import Path

zip_path = Path("data/hotpot_dev_distractor_v1.json.zip")
out_json_path = Path("data/hotpot_extended.json")

print(f"Opening zip archive: {zip_path}")
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    namelist = zip_ref.namelist()
    json_filename = namelist[0]
    with zip_ref.open(json_filename) as f:
        print(f"Reading {json_filename} from zip...")
        data = json.load(f)

print(f"Total examples found in original dev set: {len(data)}")

# We need to pick 100 questions to match the user's requirement.
# Let's seed random for reproducibility
random.seed(42)
selected_raw = random.sample(data, 100)

formatted_examples = []
for item in selected_raw:
    # Map raw context to ContextChunk structure
    context_chunks = []
    for title, sentences in item.get("context", []):
        # combine sentences into a single text block
        text = "".join(sentences)
        context_chunks.append({
            "title": title,
            "text": text
        })
    
    # Map level to difficulty: "easy", "medium", "hard"
    level = item.get("level", "medium")
    if level not in ["easy", "medium", "hard"]:
        level = "medium"
        
    formatted_examples.append({
        "qid": item.get("_id"),
        "difficulty": level,
        "question": item.get("question"),
        "gold_answer": item.get("answer"),
        "context": context_chunks
    })

print(f"Formatted {len(formatted_examples)} examples.")

# Save to data/hotpot_extended.json
out_json_path.parent.mkdir(parents=True, exist_ok=True)
with open(out_json_path, "w", encoding="utf-8") as f:
    json.dump(formatted_examples, f, indent=2, ensure_ascii=False)

print(f"Successfully saved to {out_json_path}")
