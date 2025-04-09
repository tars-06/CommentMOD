# 🛡️ Comment Moderation using OpenRouter + LLM

A Python CLI tool that reads user comments from a CSV or JSON file, uses a Generative AI model via [OpenRouter](https://openrouter.ai) to detect offensive or inappropriate content, and generates a clean report with visual insights.

> Uses reliable and open-source `nvidia/llama-3.1-nemotron-nano-8b-v1:free` model from OpenRouter.

---

## ✨ Features

- 🧠 LLM-powered moderation using OpenRouter
- 📁 Supports `.csv` and `.json` input
- 🚫 Fully LLM-based (no profanity filter)
- 🧹 Auto-fixes messy JSON responses
- 📝 Generates a detailed summary report
- 📊 Produces a pie chart of offense types
- 🧃 CLI support for flexible input/output

---

## 🚀 Installation

```bash
git clone https://github.com/tars-06/commentMOD.git
cd comment-moderation
pip install -r requirements.txt
```

### Requirements (`requirements.txt`)
```
requests
matplotlib
python-dotenv
```

---

## 🔑 Setup

1. Create a `.env` file in the project root:
    ```
    OPENROUTER_API_KEY=sk-your-openrouter-api-key
    ```

2. Enable prompt training on your OpenRouter account:  
   👉 https://openrouter.ai/settings/privacy

---

## 📂 Input Format

### CSV (`comments.csv`)
```csv
comment_id,username,comment_text
1,alice,"I love the way you explained it!"
2,bob,"You're so dumb it's painful."
...
```

### JSON (`comments.json`)
```json
[
  {
    "comment_id": 1,
    "username": "alice",
    "comment_text": "I love the way you explained it!"
  },
  ...
]
```

---

## 🧪 Usage

### Basic run:
```bash
python moderate_comments.py comments.csv
```

### With JSON input:
```bash
python moderate_comments.py comments.json
```

### With custom output folder:
```bash
python moderate_comments.py comments.csv --output_dir outputs/
```

---

## 📦 Output Files

| File                           | Description                                      |
|--------------------------------|--------------------------------------------------|
| `moderated_comments.csv`       | All comments + moderation results                |
| `moderation_report.txt`        | Summary report + top 5 most offensive comments   |
| `offense_type_pie_chart.png`   | Pie chart of offensive comment types             |

---

## 🔎 What the Model Returns

Each comment is enriched with the following fields:

```json
{
  "comment_id": 42,
  "is_offensive": true,
  "offense_type": "harassment",
  "explanation": "Contains threatening and derogatory language."
}
```

---

## 🛠 Troubleshooting

- **401 Unauthorized**  
  → Check if your API key is valid and loaded via `.env`

- **404 from OpenRouter**  
  → Go to https://openrouter.ai/settings/privacy and enable "Allow prompt training"

- **JSONDecodeError**  
  → Script automatically sanitizes bad output or skips malformed batches.

---

## 🧯 Notes

- Uses batch prompting (10 comments per API call)
- Automatically handles smart quotes, bad punctuation, and broken JSON
- Purely LLM-driven — no keyword-based filtering

---

## 📜 License

MIT © Aaditya Saraf
