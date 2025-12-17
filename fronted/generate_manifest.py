import json
from pathlib import Path

# Configuration
MANIFEST_PATH = Path("../imgs_monkey/manifest.jsonl")
OUTPUT_FILE = Path("public/monkey_manifest.json")

def generate_manifest():
    if not MANIFEST_PATH.exists():
        print(f"Error: Manifest file {MANIFEST_PATH} does not exist.")
        return

    images = []
    
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                if record.get("ok"):
                    # input: "imgs/filename.jpg"
                    # output: "imgs_monkey/filename__jpg.png"
                    
                    input_path = Path(record["input"])
                    output_path = Path(record["output"])
                    
                    images.append({
                        "id": output_path.stem,
                        "pig_url": f"/imgs/{input_path.stem}.webp",
                        "monkey_url": f"/imgs_monkey/{output_path.stem}.webp",
                        "original_name": input_path.name
                    })
            except json.JSONDecodeError:
                continue

    # Write to JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(images, f, ensure_ascii=False, indent=2)

    print(f"Manifest generated: {len(images)} pairs found.")
    print(f"Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_manifest()
