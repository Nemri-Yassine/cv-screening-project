from pathlib import Path

import pandas as pd
from langchain_community.document_loaders import PyPDFLoader

FOLDER_PATH = Path(__file__).parent / "data"
MAX_CHARS = 1500  # keep the CVs short so the fine-tuning fits on a free Colab GPU


# 1. Read every PDF, the label is the name of its folder

rows = []
pdf_files = sorted(FOLDER_PATH.rglob("*.pdf"))

for i, pdf_path in enumerate(pdf_files, start=1):
    pages = PyPDFLoader(str(pdf_path)).load()
    text = " ".join(page.page_content for page in pages)
    text = " ".join(text.split())[:MAX_CHARS]  # remove the extra spaces and new lines

    rows.append({"text": text, "category": pdf_path.parent.name})
    print(f"[{i}/{len(pdf_files)}] {pdf_path.name}")


# 2. Shuffle and split 80% train / 20% test

df = pd.DataFrame(rows).sample(frac=1, random_state=42)
split = int(len(df) * 0.8)

df[:split].to_csv(Path(__file__).parent / "train.csv", index=False)
df[split:].to_csv(Path(__file__).parent / "test.csv", index=False)

print(f"train.csv : {split} CVs | test.csv : {len(df) - split} CVs")
