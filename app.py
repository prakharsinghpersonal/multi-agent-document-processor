import streamlit as st
import tempfile
import os
from agents import DocumentProcessor
import json
from logger_config import setup_logger
import time

# Setup logger for the main application
app_logger = setup_logger('streamlit_app')

st.set_page_config(
    page_title="Document Processing System",
    page_icon="📄",
    layout="wide"
)

def save_uploaded_file(uploaded_file):
    """Save uploaded file to a temporary location."""
    app_logger.info("Attempting to save uploaded file")
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            app_logger.info(f"File saved successfully at: {tmp_file.name}")
            return tmp_file.name
    except Exception as e:
        app_logger.error(f"Error saving file: {str(e)}", exc_info=True)
        st.error(f"Error saving file: {str(e)}")
        return None

def read_log_file(logger_name):
    """Read the contents of a log file."""
    log_file = os.path.join("logs", f"{logger_name}.log")
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            return f.read()
    return "No logs available."

def process_document(pdf_path, fast_mode=True):
    """Process document and update status in session state."""
    processor = DocumentProcessor(fast_mode=fast_mode)
    
    # Text extraction
    st.session_state.processing_status["text_extraction"]["status"] = "in_progress"
    st.session_state.processing_status["text_extraction"]["progress"] = 0
    
    st.session_state.processing_status["text_extraction"]["progress"] = 50
    extracted_text = processor.extractor.process(pdf_path)
    
    st.session_state.processing_status["text_extraction"]["progress"] = 100
    st.session_state.processing_status["text_extraction"]["status"] = "completed"
    
    # Summarization
    st.session_state.processing_status["summarization"]["status"] = "in_progress"
    st.session_state.processing_status["summarization"]["progress"] = 0
    
    st.session_state.processing_status["summarization"]["progress"] = 50
    summary = processor.summarizer.process(extracted_text)
    
    st.session_state.processing_status["summarization"]["progress"] = 100
    st.session_state.processing_status["summarization"]["status"] = "completed"
    
    # Field extraction
    st.session_state.processing_status["field_extraction"]["status"] = "in_progress"
    st.session_state.processing_status["field_extraction"]["progress"] = 0
    
    st.session_state.processing_status["field_extraction"]["progress"] = 50
    fields = processor.field_extractor.process(extracted_text)
    
    st.session_state.processing_status["field_extraction"]["progress"] = 100
    st.session_state.processing_status["field_extraction"]["status"] = "completed"
    
    return {
        "extracted_text": extracted_text,
        "summary": summary,
        "fields": fields
    }

def main():
    app_logger.info("Starting application")
    st.title("📄 Multi-Agent Document Processing System")
    
    # Initialize session state
    if 'results' not in st.session_state:
        st.session_state.results = None
        app_logger.debug("Initialized results in session state")
    if 'processing_status' not in st.session_state:
        st.session_state.processing_status = {
            "text_extraction": {"status": "pending", "progress": 0},
            "summarization": {"status": "pending", "progress": 0},
            "field_extraction": {"status": "pending", "progress": 0}
        }
        app_logger.debug("Initialized processing_status in session state")

    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📤 Upload", 
        "⚙️ Processing", 
        "📝 Extracted Text", 
        "📋 Summary", 
        "🔑 Key Fields"
    ])

    with tab1:
        st.header("Upload Document")
        
        # Fast mode toggle
        col1, col2 = st.columns([1, 2])
        with col1:
            fast_mode = st.checkbox("🚀 Fast Mode (Recommended)", value=True, help="Use lightweight text analysis for instant results. Uncheck for AI-powered analysis (slower but more accurate).")
        with col2:
            if fast_mode:
                st.success("⚡ Fast mode enabled - Instant processing!")
            else:
                st.info("🤖 AI mode enabled - Slower but more accurate")
        
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
        
        if uploaded_file is not None:
            app_logger.info(f"File uploaded: {uploaded_file.name}")
            if st.button("Extract"):
                app_logger.info("Extract button clicked")
                with st.spinner("Processing document..."):
                    try:
                        # Reset processing status
                        st.session_state.processing_status = {
                            "text_extraction": {"status": "in_progress", "progress": 0},
                            "summarization": {"status": "pending", "progress": 0},
                            "field_extraction": {"status": "pending", "progress": 0}
                        }
                        
                        # Save uploaded file
                        pdf_path = save_uploaded_file(uploaded_file)
                        if pdf_path:
                            app_logger.info("Initializing document processor")
                            
                            # Process document
                            app_logger.info("Starting document processing")
                            st.session_state.results = process_document(pdf_path, fast_mode=fast_mode)
                            
                            # Clean up temporary file
                            os.unlink(pdf_path)
                            app_logger.info("Temporary file cleaned up")
                            
                            st.success("Document processed successfully!")
                            app_logger.info("Document processing completed successfully")
                    except Exception as e:
                        app_logger.error(f"Error processing document: {str(e)}", exc_info=True)
                        st.error(f"Error processing document: {str(e)}")

    with tab2:
        st.header("Processing Status")
        
        # Display processing status for each step
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Processing Steps")
            
            # Text Extraction Status
            st.write("📄 Text Extraction")
            text_extraction_status = st.session_state.processing_status["text_extraction"]
            st.progress(text_extraction_status["progress"] / 100)
            st.write(f"Status: {text_extraction_status['status'].replace('_', ' ').title()}")
            
            # Summarization Status
            st.write("📝 Summarization")
            summarization_status = st.session_state.processing_status["summarization"]
            st.progress(summarization_status["progress"] / 100)
            st.write(f"Status: {summarization_status['status'].replace('_', ' ').title()}")
            
            # Field Extraction Status
            st.write("🔑 Field Extraction")
            field_extraction_status = st.session_state.processing_status["field_extraction"]
            st.progress(field_extraction_status["progress"] / 100)
            st.write(f"Status: {field_extraction_status['status'].replace('_', ' ').title()}")
        
        with col2:
            st.subheader("Live Logs")
            log_tabs = st.tabs(["App", "Extractor", "Summarizer", "Field Extractor"])
            
            with log_tabs[0]:
                st.text_area("Application Logs", read_log_file("streamlit_app"), height=200)
            with log_tabs[1]:
                st.text_area("Extractor Logs", read_log_file("extractor_agent"), height=200)
            with log_tabs[2]:
                st.text_area("Summarizer Logs", read_log_file("summarizer_agent"), height=200)
            with log_tabs[3]:
                st.text_area("Field Extractor Logs", read_log_file("field_extractor_agent"), height=200)

    with tab3:
        st.header("Extracted Text")
        if st.session_state.results:
            app_logger.debug("Displaying extracted text")
            st.text_area("Raw Text", st.session_state.results["extracted_text"], height=400)
        else:
            app_logger.debug("No extracted text to display")
            st.info("No text extracted yet. Please upload and process a document.")

    with tab4:
        st.header("Summary")
        if st.session_state.results:
            app_logger.debug("Displaying document summary")
            st.text_area("Document Summary", st.session_state.results["summary"], height=400)
        else:
            app_logger.debug("No summary to display")
            st.info("No summary available yet. Please upload and process a document.")

    with tab5:
        st.header("Key Fields")
        if st.session_state.results:
            app_logger.debug("Displaying extracted fields")
            fields = st.session_state.results["fields"]
            
            # Check if there was an error in field extraction
            if "error" in fields:
                app_logger.warning("Field extraction had errors")
                st.warning("⚠️ Some fields could not be extracted properly")
                st.error(f"Error: {fields['error']}")
                if "raw_response" in fields:
                    st.text("Raw LLM Response:")
                    st.code(fields["raw_response"])
                
                st.subheader("Extracted Fields (Partial)")
                fields = fields["parsed_fields"]
            
            # Format JSON for better display
            formatted_json = json.dumps(fields, indent=2)
            st.json(formatted_json)
            
            # Add download button for JSON
            st.download_button(
                label="Download JSON",
                data=formatted_json,
                file_name="extracted_fields.json",
                mime="application/json"
            )
            app_logger.debug("JSON download button added")
        else:
            app_logger.debug("No fields to display")
            st.info("No fields extracted yet. Please upload and process a document.")

if __name__ == "__main__":
    main() 