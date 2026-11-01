import os

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from chat import cv_graph, format_candidates

QUESTIONS = [
    "find me IT profiles with at least 3 years of experience",
    "who are the best candidates for an HR manager position ?",
    "I need an accountant who knows QuickBooks",
    "compare the top 2 chefs",
    "do we have a nurse with a master degree ?",
    "find a designer who can do UI/UX",
]


class Judgement(BaseModel):
    faithfulness: int = Field(description="From 1 to 5, does the answer only use information from the candidates ?")
    relevance: int = Field(description="From 1 to 5, does the answer really answer the question ?")
    reason: str = Field(description="One short sentence explaining the scores")


# a bigger model is used as the judge
judge_llm = ChatGroq(
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model_name="openai/gpt-oss-120b",
    temperature=0,
)

judge_prompt = ChatPromptTemplate.from_template(
    '''
    You are evaluating a recruiting assistant.
    Score the answer given the question and the candidates it received.

    question :
    {question}

    candidates :
    {context}

    answer :
    {answer}
    '''
)

judge_chain = judge_prompt | judge_llm.with_structured_output(Judgement)


faithfulness_scores = []
relevance_scores = []

for question in QUESTIONS:
    result = cv_graph.invoke({"question": question})

    judgement = judge_chain.invoke({
        "question": question,
        "context": format_candidates(result["candidates"]),
        "answer": result["answer"],
    })
    faithfulness_scores.append(judgement.faithfulness)
    relevance_scores.append(judgement.relevance)

    print(f"Q : {question}")
    print(f"faithfulness={judgement.faithfulness} relevance={judgement.relevance} -> {judgement.reason}\n")

print(f"==> Faithfulness = {sum(faithfulness_scores) / len(faithfulness_scores):.2f} / 5")
print(f"==> Relevance    = {sum(relevance_scores) / len(relevance_scores):.2f} / 5")
