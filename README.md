# CV Screening Assistant

A recruiter asks questions in natural language ("find me IT profiles with Python and 3+ years of experience")
and the assistant searches a database of CVs (PDF) to answer.

What the project covers :

- LangChain / LangGraph : `chat.py` is a small LangGraph (extract filters -> retrieve -> check -> generate)
- RAG / Advanced : metadata extracted from each CV by the LLM, metadata filtering in Qdrant, retry without the category filter
- Evaluation : `eval_retrieval.py` (Precision@k, MRR, basic vs advanced) and `eval_generation.py` (LLM as a judge)
- SLM / Fine-Tuning : `finetune_slm.ipynb` fine-tunes Qwen2.5-0.5B with LoRA to classify CVs, `compare_slm_vs_llm.py` compares it with the Groq LLM

## Creating the Vector DB

1- Open docker (docker desktop for windows)
2- launch the docker compose using
```bash
docker compose up -d
```
3- Check the Qdrant UI on : localhost:6333/dashboard

## Downloading the data

4- Download the dataset at : https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset

5- Create a folder named data : cv-screening-project/data
6- Copy the category folders (ACCOUNTANT, HR, INFORMATION-TECHNOLOGY ...) from `data/data/` of the download inside it.
You should have : data/ACCOUNTANT/10554236.pdf, data/HR/...

7- Copy .env.example to .env and put your Groq API key

## Running the project

8 - `python metadata_extractor.py` : test the extraction on one CV
9 - `python ingestion.py` : extract the metadata of the CVs and store them in Qdrant (MAX_PER_CATEGORY CVs per category)
10 - `python chat.py` : ask questions, /bye to quit
11 - `python eval_retrieval.py` then `python eval_generation.py`

## Fine-tuning the SLM

12 - `python build_dataset.py` : creates train.csv and test.csv from the PDFs
13 - Open `finetune_slm.ipynb` on Google Colab (Runtime -> T4 GPU), upload train.csv and test.csv, run all the cells
14 - Unzip the downloaded `slm-cv-classifier.zip` in this folder
15 - `python compare_slm_vs_llm.py`
