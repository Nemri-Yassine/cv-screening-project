import os

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from dotenv import load_dotenv
load_dotenv()


class CVMetadata(BaseModel):
    job_title: str = Field(description="Current or most recent job title")
    years_experience: int = Field(description="Total years of professional experience, 0 if unknown")
    education_level: str = Field(description="Highest degree: 'High School', 'Bachelor', 'Master', 'PhD' or 'Unknown'")
    skills: list[str] = Field(description="The 10 main skills of the candidate")
    summary: str = Field(description="One sentence describing the candidate")


llm = ChatGroq(
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model_name="openai/gpt-oss-120b",
    temperature=0,
)

prompt = ChatPromptTemplate.from_template(
    '''
    Extract the candidate metadata from the CV below.
    The text comes from a PDF, so the layout can be messy.
    Compute the years of experience from the dates of the jobs.

    CV text:
    {text}
    '''
)

extraction_chain = prompt | llm.with_structured_output(CVMetadata)


def extract_metadata(text):
    # some CVs are very long, the first 6000 characters are enough
    return extraction_chain.invoke({"text": text[:6000]}).model_dump()


if __name__ == "__main__":
    from pathlib import Path
    from langchain_community.document_loaders import PyPDFLoader

    path = Path(__file__).parent / "data" / "HR"
    pdf_path = sorted(path.glob("*.pdf"))[0]
    pages = PyPDFLoader(str(pdf_path)).load()
    text = "\n".join(page.page_content for page in pages)
    print(pdf_path.name)
    print(extract_metadata(text))
