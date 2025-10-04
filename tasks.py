from crewai import Task
from agents import triage_agent, extraction_agent, safety_agent, seriousness_agent

# Task 1: Triage the document
triage_task = Task(
    description='Load the medical document from the provided file path, extract its text, and identify the form type.',
    expected_output='A string with the raw text content of the document and a string identifying the form type (e.g., MedWatch, CIOMS).',
    agent=triage_agent
)

# Task 2: Extract and store data
extraction_task = Task(
    description='Using the document text, extract all key medical information. Then, store this structured data in the AstraDB vector database.',
    expected_output='A confirmation message that data was successfully stored in AstraDB, including the new Case ID.',
    agent=extraction_agent,
    context=[triage_task]
)

# Task 3: Assess for adverse event
assessment_task = Task(
    description='Analyze the extracted event description from the context to classify if the event is an adverse event.',
    expected_output='A classification of "Yes" or "No". The description of the event should also be passed forward.',
    agent=safety_agent,
    context=[extraction_task]
)

# Task 4: Classify seriousness
seriousness_task = Task(
    description='If the event has been classified as adverse, analyze its description and classify its seriousness based on standard criteria. If not an adverse event, state that no seriousness classification is needed.',
    expected_output='A final JSON report containing the adverse event status and a list of any applicable seriousness criteria.',
    agent=seriousness_agent,
    context=[assessment_task]
)
