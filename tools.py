import os
import json
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_astradb import AstraDBVectorStore
from crewai.tools import BaseTool
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from dotenv import load_dotenv

load_dotenv()

# --- Initialize Connections ---
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))
openai_embeddings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))

# Setup connection to AstraDB (lazy initialization to avoid quota issues)
vstore = None

def get_vstore():
    global vstore
    if vstore is None:
        # Check if AstraDB credentials are available
        api_endpoint = os.getenv("ASTRA_DB_API_ENDPOINT")
        token = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
        
        if not api_endpoint or not token:
            # Return a mock vstore for testing without AstraDB
            class MockVstore:
                def add_texts(self, texts, metadatas=None):
                    return ["mock_id_123"]
            vstore = MockVstore()
        else:
            vstore = AstraDBVectorStore(
                embedding=openai_embeddings,
                collection_name="pharmacovigilance_reports",
                api_endpoint=api_endpoint,
                token=token,
            )
    return vstore

# --- Define Tools using CrewAI BaseTool ---
class DocumentLoaderTool(BaseTool):
    name: str = "Document Loader Tool"
    description: str = "Loads a document (.txt or .pdf) and returns its text content."
    
    def _run(self, file_path: str) -> str:
        if file_path.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        else:
            loader = TextLoader(file_path)
        documents = loader.load()
        return "\n".join(doc.page_content for doc in documents)

class FormTriageTool(BaseTool):
    name: str = "Form Triage Tool"
    description: str = "Identifies the type of medical form (MedWatch, CIOMS, E2B) from its content."
    
    def _run(self, document_text: str) -> str:
        prompt = f"""
        Based ONLY on the text below, identify the form type.
        The possible types are: MedWatch, CIOMS, E2B.
        Return ONLY the name of the form type and nothing else.

        TEXT:
        ---
        {document_text}
        ---
        """
        response = llm.invoke(prompt)
        return response.content.strip()

class DataExtractionTool(BaseTool):
    name: str = "Data Extraction and Storage Tool"
    description: str = "Extracts key medical data from a document, stores it in AstraDB, and returns a success message including the case ID and event description."
    
    def _run(self, document_text: str) -> str:
        prompt = f"""
        You are a precise medical data extraction assistant. Your task is to analyze the provided medical document text and extract the specified entities.

        RULES:
        1. You MUST ONLY use information present in the text provided below.
        2. DO NOT use any prior knowledge or invent any information.
        3. If a specific piece of information (e.g., patient_id) is not found in the text, you MUST return "Not Found" for that field.
        4. Return the result as a single, clean JSON object with no extra text or explanations.

        TEXT TO ANALYZE:
        ---
        {document_text}
        ---
        
        EXTRACTED JSON:
        """
        response_content = llm.invoke(prompt).content
        
        try:
            json_str = response_content.strip().replace("```json", "").replace("```", "")
            data = json.loads(json_str)
            
            event_description = data.get('event_description', 'N/A')
            text_to_embed = f"Event Description: {event_description} for Drug: {data.get('drug_name', 'N/A')}"
            
            vstore_instance = get_vstore()
            ids = vstore_instance.add_texts([text_to_embed], metadatas=[data])
            
            # Pass both a success message and the crucial event description forward
            return f"Successfully stored data in AstraDB. Case ID(s): {ids}. Event Description: {event_description}"
        except Exception as e:
            return f"Error in data extraction or storage: {e}. Raw LLM output was: {response_content}"

class AdverseEventClassifierTool(BaseTool):
    name: str = "Adverse Event Classifier Tool"
    description: str = "Classifies if an event is an 'Adverse Event' or 'Not an Adverse Event'."
    
    def _run(self, event_description: str) -> str:
        prompt = f"Is the following an adverse event? Answer only with 'Yes' or 'No'. Description: {event_description}"
        response = llm.invoke(prompt)
        return f"Classification: {response.content.strip()}. Original Description: {event_description}"

class SeriousnessClassifierTool(BaseTool):
    name: str = "Seriousness Classifier Tool"
    description: str = "Classifies the seriousness of an adverse event based on its description."
    
    def _run(self, event_description: str) -> str:
        prompt = f"""
        Review ONLY the event description provided. Does it meet any of the following seriousness criteria: Death, Life-Threatening, Hospitalization, Disability, Congenital Anomaly? 
        Return a Python list of the criteria that apply as a string. If none apply, return an empty list string '[]'.
        Description: {event_description}
        """
        response = llm.invoke(prompt)
        return response.content.strip()

# Create tool instances
load_document = DocumentLoaderTool()
identify_form_type = FormTriageTool()
extract_and_store_data = DataExtractionTool()
classify_adverse_event = AdverseEventClassifierTool()
classify_seriousness = SeriousnessClassifierTool()