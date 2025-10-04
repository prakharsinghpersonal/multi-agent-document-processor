from crewai import Agent
from langchain_openai import ChatOpenAI
from tools import load_document, identify_form_type, extract_and_store_data, classify_adverse_event, classify_seriousness
import os

# Initialize the OpenAI LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, api_key=os.getenv("OPENAI_API_KEY"))

# Agent 1: The Triage Specialist
triage_agent = Agent(
    role='Medical Form Triage Specialist',
    goal='Accurately identify the type of an incoming medical form and extract its raw text content.',
    backstory='An expert in recognizing different pharmacovigilance reporting formats and preparing them for processing.',
    llm=llm,
    allow_delegation=False,
    verbose=True
)

# Agent 2: The Data Extractor
extraction_agent = Agent(
    role='Medical Data Extraction and Storage Specialist',
    goal='Precisely extract patient and event data from the form text and store it in the AstraDB vector database.',
    backstory='A meticulous agent designed for parsing medical documents and structuring information for database entry.',
    llm=llm,
    allow_delegation=False,
    verbose=True
)

# Agent 3: The Safety Assessor
safety_agent = Agent(
    role='Adverse Event Safety Assessor',
    goal='Analyze an extracted event description to determine if it constitutes an adverse event.',
    backstory='A clinical expert trained to classify medical events based on standard safety definitions.',
    llm=llm,
    allow_delegation=False,
    verbose=True
)

# Agent 4: The Seriousness Classifier
seriousness_agent = Agent(
    role='Clinical Seriousness Classifier',
    goal='Evaluate an adverse event against established seriousness criteria (e.g., Death, Life-Threatening).',
    backstory='A specialist in pharmacovigilance regulations, responsible for classifying the severity of reported events.',
    llm=llm,
    allow_delegation=False,
    verbose=True
)