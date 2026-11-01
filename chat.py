import os

os.environ["HF_HUB_OFFLINE"] = "1"

from typing import TypedDict

from pydantic import BaseModel, Field
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END

from qdrant_client.models import Filter, FieldCondition, MatchValue, Range

from dotenv import load_dotenv
load_dotenv()

QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "cvs"

CATEGORIES = [
    "ACCOUNTANT", "ADVOCATE", "AGRICULTURE", "APPAREL", "ARTS", "AUTOMOBILE",
    "AVIATION", "BANKING", "BPO", "BUSINESS-DEVELOPMENT", "CHEF", "CONSTRUCTION",
    "CONSULTANT", "DESIGNER", "DIGITAL-MEDIA", "ENGINEERING", "FINANCE", "FITNESS",
    "HEALTHCARE", "HR", "INFORMATION-TECHNOLOGY", "PUBLIC-RELATIONS", "SALES", "TEACHER",
]


class SearchFilters(BaseModel):
    search_query: str = Field(description="Short search query with the job and the skills the user is looking for")
    category: str = Field(description="One category from the list, or '' if it is not clear")
    min_years: int = Field(0, description="Minimum years of experience asked, 0 if not mentioned")


class Grade(BaseModel):
    relevant: bool = Field(description="True if at least one candidate matches the request")


class State(TypedDict):
    question: str
    filters: SearchFilters
    candidates: list
    tries: int
    answer: str
    sources: list


llm = ChatGroq(
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model_name="openai/gpt-oss-20b",
)

filter_prompt = ChatPromptTemplate.from_template(
    '''
    A recruiter is searching for candidates.
    Extract the search filters from the question.

    possible categories :
    {categories}

    question :
    {question}
    '''
)

grade_prompt = ChatPromptTemplate.from_template(
    '''
    Does at least one of these candidates match the recruiter's request ?

    request :
    {question}

    candidates :
    {context}
    '''
)

prompt = ChatPromptTemplate.from_template(
    '''
    You are a helpful recruiting assistant
    you always answer the question given the candidates below
    cite every candidate you talk about with its file name in square brackets, like [10554236.pdf]
    never talk about a candidate that is not in the list
    if no candidate matches just say it

    question :
    {question}

    candidates :
    {context}
    '''
)

filter_chain = filter_prompt | llm.with_structured_output(SearchFilters)
grade_chain = grade_prompt | llm.with_structured_output(Grade)
answer_chain = prompt | llm | StrOutputParser()


# 1. Load the same embedding model

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# 2. Connect to the existing Qdrant collection

vector_store = QdrantVectorStore.from_existing_collection(
    embedding=embeddings,
    url=QDRANT_URL,
    collection_name=COLLECTION_NAME,
)


def build_filter(filters):
    conditions = []
    if filters.category in CATEGORIES:
        conditions.append(FieldCondition(key="metadata.category", match=MatchValue(value=filters.category)))
    if filters.min_years > 0:
        conditions.append(FieldCondition(key="metadata.years_experience", range=Range(gte=filters.min_years)))
    return Filter(must=conditions) if conditions else None


def doc_to_source(doc):
    # langchain_qdrant adds internal keys like _id and _collection_name to the metadata
    source = {key: value for key, value in doc.metadata.items() if not key.startswith("_")}
    source["profile"] = doc.page_content
    return source


def format_source(source):
    return (
        f"[{source['file_name']}] category={source['category']} | job_title={source['job_title']} | "
        f"years_experience={source['years_experience']} | education={source['education_level']} | "
        f"skills={', '.join(source['skills'])} | summary={source['summary']}"
    )


def format_candidates(documents):
    return "\n".join(format_source(doc_to_source(doc)) for doc in documents)


# 3. The nodes of the graph

def extract_filters(state):
    filters = filter_chain.invoke({"question": state["question"], "categories": CATEGORIES})
    print("Filters :", filters)
    return {"filters": filters, "tries": 0}


def retrieve(state):
    candidates = vector_store.similarity_search(
        state["filters"].search_query,
        k=5,
        filter=build_filter(state["filters"]),
    )
    return {"candidates": candidates}


def relax_filters(state):
    # the category guessed by the LLM is the most common mistake, so we remove it and search again
    print("No good candidates, searching again without the category")
    filters = state["filters"].model_copy(update={"category": ""})
    return {"filters": filters, "tries": state["tries"] + 1}


def generate(state):
    answer = answer_chain.invoke({
        "question": state["question"],
        "context": format_candidates(state["candidates"]),
    })
    return {"answer": answer, "sources": [doc_to_source(doc) for doc in state["candidates"]]}


def check_candidates(state):
    if state["tries"] >= 1:
        return "generate"
    if not state["candidates"]:
        return "relax"

    grade = grade_chain.invoke({
        "question": state["question"],
        "context": format_candidates(state["candidates"]),
    })
    return "generate" if grade.relevant else "relax"


# 4. Build the graph : extract_filters -> retrieve -> (generate | relax_filters -> retrieve)

graph = StateGraph(State)

graph.add_node("extract_filters", extract_filters)
graph.add_node("retrieve", retrieve)
graph.add_node("relax_filters", relax_filters)
graph.add_node("generate", generate)

graph.add_edge(START, "extract_filters")
graph.add_edge("extract_filters", "retrieve")
graph.add_conditional_edges("retrieve", check_candidates, {"generate": "generate", "relax": "relax_filters"})
graph.add_edge("relax_filters", "retrieve")
graph.add_edge("generate", END)

cv_graph = graph.compile()


if __name__ == "__main__":
    print("CV Screening Assistant")
    print("Try: find me IT profiles with Python and at least 3 years of experience")
    print("/bye to quit\n")

    while True:
        question = input('Ask something : ')
        if question.lower() in ['/quit', '/bye']:
            print("Exiting the program.")
            break

        result = cv_graph.invoke({"question": question})
        print('AI : ', result["answer"])
        print('Sources : ', ", ".join(source["file_name"] for source in result["sources"]), "\n")
