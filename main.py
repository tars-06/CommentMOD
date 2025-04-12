import argparse
import csv
import json
import time
import os
import re
import sys
import requests
import matplotlib.pyplot as plt
from dotenv import load_dotenv

# for using utf-8 characters in windows
if sys.platform == "win32":
    os.system("")
    sys.stdout.reconfigure(encoding='utf-8')

# loading environment variables
load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    raise ValueError("OPENROUTER_API_KEY is not set in .env file")

# configuring cli (for more info read readme.md)
parser = argparse.ArgumentParser(description="LLM-Powered Comment Moderation")
parser.add_argument("input_file", help="Input file path (.csv or .json)")
parser.add_argument("--output_dir", default=".", help="Output directory path")
args = parser.parse_args()

INPUT_FILE = args.input_file
OUTPUT_DIR = args.output_dir

OUTPUT_FILE = os.path.join(OUTPUT_DIR, "moderated_comments.csv")
REPORT_FILE = os.path.join(OUTPUT_DIR, "moderation_report.txt")
CHART_FILE = os.path.join(OUTPUT_DIR, "offense_type_pie_chart.png")

# configuring genai model provider (in this case openrouter)
API_URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost",
    "X-Title": "comment-moderation-script"
}
MODEL = "nvidia/llama-3.1-nemotron-nano-8b-v1:free"
BATCH_SIZE = 10

# loading input file
def load_comments(filename):
    ext = os.path.splitext(filename)[1].lower()
    with open(filename, encoding='utf-8') as f:
        if ext == ".csv":
            return list(csv.DictReader(f))
        elif ext == ".json":
            return json.load(f)
        else:
            raise ValueError("Unsupported file format. Use .csv or .json")

comments = load_comments(INPUT_FILE)
print(f"Total comments : {len(comments)}")
print("Sample comment:", comments[0]['comment_text'])

# building the prompt (very important step)
def build_prompt(batch):
    prompt = (
        "You are a content moderation AI.\n"
        "For each of the following comments, return a JSON list with:\n"
        "- comment_id\n- is_offensive (True/False)\n- offense_type\n- explanation\n\n"
        "Comments:\n"
    )
    for i, c in enumerate(batch, 1):
        prompt += f"{i}. [comment_id: {c['comment_id']}] \"{c['comment_text']}\"\n"
    prompt += "\nOnly return the JSON list. No markdown or explanation."
    return prompt

def extract_json_block(text):
    match = re.search(r"```json\n(.+?)\n```", text, re.DOTALL)
    return match.group(1) if match else text.strip()

def sanitize_json_string(s):
    s = s.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    s = re.sub(r'(?<!\\)"', '"', s)  # fix stray quotes
    s = re.sub(r'\\(?![\"/bfnrtu])', "", s)  # strip invalid escapes
    return s

# sending api request to genai model
def moderate_batch(batch):
    prompt = build_prompt(batch)
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(API_URL, headers=HEADERS, data=json.dumps(body))
    response.raise_for_status()
    content = response.json()['choices'][0]['message']['content']
    clean = sanitize_json_string(extract_json_block(content))
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        print("❌ Failed to parse JSON after sanitizing. Skipping batch.")
        return []

# processing batch by batch
results = []
for i in range(0, len(comments), BATCH_SIZE):
    batch = comments[i:i + BATCH_SIZE]
    try:
        print(f"Processing batch {i // BATCH_SIZE + 1}")
        result = moderate_batch(batch)
        results.extend(result)
        time.sleep(2)
    except Exception as e:
        print(f"Error in batch {i // BATCH_SIZE + 1}: {e}")

comments_map = {str(c['comment_id']): c for c in comments}
for mod in results:
    cid = str(mod.get("comment_id"))
    if cid not in comments_map:
        print(f"⚠️ Skipping unknown comment_id: {cid}")
        continue
    comments_map[cid].update(mod)

# exporting the moderated csv with marked comments
fieldnames = list(comments[0].keys())
for field in ['is_offensive', 'offense_type', 'explanation']:
    if field not in fieldnames:
        fieldnames.append(field)
with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for c in comments_map.values():
        writer.writerow(c)

# summary report
offensive = [c for c in comments_map.values() if c.get('is_offensive') == True]
type_count = {}
for c in offensive:
    t = c.get('offense_type', 'unspecified')
    type_count[t] = type_count.get(t, 0) + 1

top_5 = sorted(offensive, key=lambda x: len(x.get('explanation', '')), reverse=True)[:5]

with open(REPORT_FILE, "w", encoding="utf-8") as f:
    f.write("=== Moderation Report ===\n\n")
    f.write(f"Total Comments: {len(comments)}\n")
    f.write(f"Offensive Comments: {len(offensive)}\n\n")
    f.write("Offense Type Breakdown:\n")
    for k, v in type_count.items():
        f.write(f"  - {k}: {v}\n")
    f.write("\nTop 5 Most Offensive Comments:\n")
    for i, c in enumerate(top_5, 1):
        f.write(f"{i}. {c['comment_text']}\n")
        f.write(f"   → Type: {c['offense_type']}\n")
        f.write(f"   → Explanation: {c['explanation']}\n\n")

print(f"✅ Report saved to {REPORT_FILE}")

# making a pie chart consisting of our results
if type_count:
    plt.figure(figsize=(6, 6))
    plt.pie(type_count.values(), labels=type_count.keys(), autopct='%1.1f%%', startangle=140)
    plt.title("Offensive Comment Type Distribution")
    plt.tight_layout()
    plt.savefig(CHART_FILE)
    plt.close()
    print(f"📊 Pie chart saved as {CHART_FILE}")
else:
    print("📭 No offensive comments – skipping pie chart.")
