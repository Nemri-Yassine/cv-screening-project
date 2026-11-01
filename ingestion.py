from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, Filter, FieldCondition, MatchValue

from metadata_extractor import extract_metadata

QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "cvs"
FOLDER_PATH = Path(__file__).parent / "data"
MAX_PER_CATEGORY = 10  # 24 categories -> 240 CVs. set to None to ingest everything (a lot of LLM calls)


embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# 1. Create the "cvs" collection if it doesn't exist

client = QdrantClient(url=QDRANT_URL)

if not client.collection_exists(COLLECTION_NAME):
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )

vector_store = QdrantVectorStore(
    client=client,
    collection_name=COLLECTION_NAME,
    embedding=embeddings,
)


def already_ingested(file_name):
    points, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=Filter(must=[
            FieldCondition(key="metadata.file_name", match=MatchValue(value=file_name))
        ]),
        limit=1,
    )
    return len(points) > 0


# 2. List the PDFs, each folder name is the category of the CV

pdf_files = []
for category_folder in sorted(FOLDER_PATH.iterdir()):
    if category_folder.is_dir():
        pdf_files += sorted(category_folder.glob("*.pdf"))[:MAX_PER_CATEGORY]


# 3. Load each CV, extract its metadata with the LLM, store it in Qdrant

for i, pdf_path in enumerate(pdf_files, start=1):
    if already_ingested(pdf_path.name):
        print(f"[{i}/{len(pdf_files)}] Skipping already ingested: {pdf_path.name}")
        continue

    pages = PyPDFLoader(str(pdf_path)).load()
    text = "\n".join(page.page_content for page in pages)

    try:
        metadata = extract_metadata(text)
    except Exception as e:
        # rate limit or bad output from the LLM: skip it, run the script again later
        print(f"[{i}/{len(pdf_files)}] Error on {pdf_path.name}: {e}")
        continue

    # the embedding model only reads ~256 tokens, so we embed a short profile, not the full CV
    profile = f"{metadata['job_title']}. {metadata['summary']} Skills: {', '.join(metadata['skills'])}"

    document = Document(
        page_content=profile,
        metadata={"file_name": pdf_path.name, "category": pdf_path.parent.name, **metadata},
    )

    vector_store.add_documents([document])
    print(f"[{i}/{len(pdf_files)}] Ingested {pdf_path.name} -> {document.metadata}")

print("CVs successfully stored in Qdrant.")
