import os
import time
from pathlib import Path

import pandas as pd
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

from dotenv import load_dotenv
load_dotenv()

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"
ADAPTER_PATH = Path(__file__).parent / "slm-cv-classifier"
N_TESTS = 50

train = pd.read_csv(Path(__file__).parent / "train.csv")
test = pd.read_csv(Path(__file__).parent / "test.csv").head(N_TESTS)
categories = sorted(train["category"].unique())


# same prompt as in the notebook, the SLM was trained with it

def build_prompt(text):
    return (
        f"Classify this CV into one of these categories: {', '.join(categories)}.\n"
        f"Answer with the category only.\n\n"
        f"CV:\n{text}"
    )


# 1. The fine-tuned SLM : base model + the LoRA adapter trained on Colab

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
base_model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, torch_dtype=torch.float32)
slm = PeftModel.from_pretrained(base_model, str(ADAPTER_PATH))
slm.eval()


def classify_with_slm(text):
    messages = [{"role": "user", "content": build_prompt(text)}]
    chat_text = tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
    inputs = tokenizer(chat_text, return_tensors="pt")

    with torch.no_grad():
        output = slm.generate(**inputs, max_new_tokens=10, do_sample=False)

    return tokenizer.decode(output[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()


# 2. The big LLM on Groq, no fine-tuning

llm = ChatGroq(
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model_name="openai/gpt-oss-20b",
    temperature=0,
)

llm_chain = ChatPromptTemplate.from_template("{prompt}") | llm | StrOutputParser()


def classify_with_llm(text):
    return llm_chain.invoke({"prompt": build_prompt(text)}).strip()


# 3. Same test CVs for both : accuracy and time

for name, classify in [("SLM fine-tuned", classify_with_slm), ("Groq LLM", classify_with_llm)]:
    correct = 0
    start = time.time()

    for i, row in enumerate(test.itertuples(), start=1):
        prediction = classify(row.text)
        correct += prediction.upper() == row.category
        print(f"[{name}] {i}/{len(test)} expected={row.category} predicted={prediction}")

    duration = time.time() - start
    print(f"\n==> {name} : accuracy = {correct / len(test):.2%} | {duration / len(test):.2f} s per CV\n")
