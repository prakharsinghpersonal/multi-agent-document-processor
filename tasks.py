from crewai import Task
from agents import triage_agent, extraction_agent, safety_agent, seriousness_agent
from tools import load_document, identify_form_type, extract_and_store_data, classify_adverse_event, classify_seriousness

# Task 1: Triage the document
triage_task = Task(
    description=(
        "Load the medical document from the file_path input, extract its text, and "
        "identify the form type from the text content. You must use the 'Document Loader Tool' first with the file_path input."
    ),
    expected_output=(
        "A string containing the full text content of the document, and a second string "
        "identifying the form type (e.g., MedWatch, CIOMS, or E2B)."
    ),
    agent=triage_agent,
    tools=[load_document, identify_form_type],
    inputs=["file_path"]
)

# Task 2: Extract and store data
extraction_task = Task(
    description=(
        "Using the document text provided in the context from the triage_task, and ONLY that text, "
        "extract all key medical information. Do not use any external knowledge or make up information. "
        "After extraction, store this structured data in the AstraDB vector database."
    ),
    expected_output=(
        "A confirmation message that data was successfully stored in AstraDB, including the new Case ID. "
        "The message should also include the extracted event description to pass to the next task."
    ),
    agent=extraction_agent,
    context=[triage_task],
    tools=[extract_and_store_data]
)

# Task 3: Assess for adverse event
assessment_task = Task(
    description=(
        "Analyze ONLY the extracted event description provided in the context from the previous task. "
        "Classify whether the event is an adverse event based on this description alone."
    ),
    expected_output=(
        'A classification of "Yes" or "No", along with the original event description for context.'
    ),
    agent=safety_agent,
    context=[extraction_task],
    tools=[classify_adverse_event]
)

# Task 4: Classify seriousness
seriousness_task = Task(
    description=(
        "Review the context from the previous task. If the event was classified as 'Yes' (adverse), "
        "analyze its description and classify its seriousness based on standard criteria "
        "(Death, Life-Threatening, Hospitalization, Disability, Congenital Anomaly). "
        "Use only the provided description. If the event was 'No', state that no seriousness classification is needed."
    ),
    expected_output=(
        'A final JSON report containing the adverse event status ("Yes" or "No") and, if applicable, '
        'a list of any identified seriousness criteria.'
    ),
    agent=seriousness_agent,
    context=[assessment_task],
    tools=[classify_seriousness]
)