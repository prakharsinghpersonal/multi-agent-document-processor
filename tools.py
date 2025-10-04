import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_astradb import AstraDBVectorStore
from langchain.tools import tool
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from dotenv import load_dotenv

load_dotenv()

# --- Initialize Connections ---
llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0)
google_embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# Setup connection to AstraDB
vstore = AstraDBVectorStore(
    embedding=google_embeddings,
    collection_name="pharmacovigilance_reports",
    api_endpoint=os.getenv("ASTRA_DB_API_ENDPOINT"),
    token=os.getenv("ASTRA_DB_APPLICATION_TOKEN"),
)

# --- Define Tools ---
@tool("Document Loader Tool")
def load_document(file_path: str) -> str:
    """Loads a document (.txt or .pdf) and returns its text content."""
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    else:
        loader = TextLoader(file_path)
    documents = loader.load()
    return "\n".join(doc.page_content for doc in documents)

@tool("Form Triage Tool")
def identify_form_type(document_text: str) -> str:
    """Identifies the type of medical form (MedWatch, CIOMS, E2B) from its content."""
    prompt = f"Identify the form type from the following text: MedWatch, CIOMS, or E2B. Read the text carefully and return only the form name as a single string. Text:\n\n{document_text}"
    response = llm.invoke(prompt)
    return response.content.strip()

@tool("Data Extraction and Storage Tool")
def extract_and_store_data(document_text: str) -> str:
    """Extracts key medical data from a document, stores it in AstraDB, and returns a success message including the case ID."""
    prompt = f"""
    Based on the following medical document text, extract these entities: patient_id, drug_name, event_description, event_date.
    Return the data as a single, clean JSON object with no extra text or explanations.
    Text: {document_text}
    """
    response_content = llm.invoke(prompt).content
    
    try:
        # Clean the response to ensure it's a valid JSON
        json_str = response_content.strip().replace("```json", "").replace("```", "")
        data = json.loads(json_str)
        
        # Create a text chunk to embed in the vector DB
        text_to_embed = f"Event Description: {data.get('event_description', 'N/A')} for Drug: {data.get('drug_name', 'N/A')}"
        
        # Store in AstraDB and get the IDs of the added documents
        ids = vstore.add_texts([text_to_embed], metadatas=[data])
        return f"Successfully extracted and stored data in AstraDB. Case ID(s): {ids}"
    except Exception as e:
        return f"Error in data extraction or storage: {e}. Raw LLM output was: {response_content}"

@tool("Adverse Event Classifier Tool")
def classify_adverse_event(event_description: str) -> str:
    """Classifies if an event is an 'Adverse Event' or 'Not an Adverse Event' based on its description."""
    prompt = f"Is the following an adverse event? Answer only with 'Yes' or 'No'. Description: {event_description}"
    response = llm.invoke(prompt)
    return response.content.strip()

@tool("Seriousness Classifier Tool")
def classify_seriousness(event_description: str) -> str:
    """Classifies the seriousness of an adverse event based on its description."""
    prompt = f"""
    Review the event description. Does it meet any of the following seriousness criteria: Death, Life-Threatening, Hospitalization, Disability, Congenital Anomaly? 
    Return a Python list of the criteria that apply as a string. If none apply, return an empty list string '[]'.
    Description: {event_description}
    """
    response = llm.invoke(prompt)
    return response.content.strip()
