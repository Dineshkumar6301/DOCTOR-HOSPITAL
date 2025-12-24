# clean_fixture.py
import json

INPUT = "raw.json"
OUTPUT = "data_fixed.json"

with open(INPUT, "rb") as f:
    raw = f.read()

# Decode using Windows-1252, then re-encode as clean UTF-8
text = raw.decode("cp1252", errors="replace")

data = json.loads(text)

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False)

print("✅ data_fixed.json created successfully")
