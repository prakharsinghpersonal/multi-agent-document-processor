import streamlit as st
from crewai import Crew, Process
from agents import triage_agent, extraction_agent, safety_agent, seriousness_agent
from tasks import triage_task, extraction_task, assessment_task, seriousness_task
import tempfile
import os
from dotenv import load_dotenv

load_dotenv()

# --- Streamlit Page Configuration ---
st.set_page_config(page_title="CogniVigilance AI", layout="wide")
st.title("⚕️ CogniVigilance: AI Agent Workflow for Pharmacovigilance")

st.markdown("""
This application uses a team of AI agents to automate the processing of medical safety reports.
Upload a document to begin.
""")

# --- File Uploader ---
uploaded_file = st.file_uploader(
    "Upload a medical report (.txt or .pdf)",
    type=['txt', 'pdf']
)

if uploaded_file is not None:
    # Save the uploaded file to a temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name

    st.success(f"Uploaded `{uploaded_file.name}`")

    # --- Button to Kickoff the Crew ---
    if st.button("Begin Processing", type="primary"):
        with st.spinner("The AI agent team is analyzing the document... This may take a moment."):
            
            # Assemble the crew
            medical_crew = Crew(
                agents=[triage_agent, extraction_agent, safety_agent, seriousness_agent],
                tasks=[triage_task, extraction_task, assessment_task, seriousness_task],
                process=Process.sequential,
                verbose=True
            )

            # Kick off the process with the file path as input
            result = medical_crew.kickoff(inputs={'file_path': tmp_file_path})
            
            st.markdown("---")
            st.subheader("Final Analysis Report:")
            st.json(result)
            st.success("Document processing complete!")

        # Clean up the temporary file
        os.remove(tmp_file_path)