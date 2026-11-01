import os
import tempfile
import json
import time
import pandas as pd
import plotly.express as px
import streamlit as st
from docx import Document

try:
    from google import genai
    from google.genai import types
except Exception:
    pass

st.set_page_config(page_title="Foreign Office Action Intelligence Engine", page_icon="📑", layout="wide")
st.title("📑 Foreign Office Action Intelligence Engine")
st.markdown('<p style="font-size: 1.25rem; font-weight: 500; color: #38bdf8 !important; margin-bottom: 25px;">Automated Cross-Lingual OCR, Prior Art Risk Modeling & Claims Dissection</p>', unsafe_allow_html=True)
def create_docx(text_content, title="Office Action Analysis Report"):
    doc = Document()
    doc.add_heading(title, level=1)
    for line in text_content.split('\n'):
        clean_line = line.strip()
        if clean_line: doc.add_paragraph(clean_line)
    tmp_docx = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    doc.save(tmp_docx.name)
    with open(tmp_docx.name, "rb") as f:
        data = f.read()
    os.unlink(tmp_docx.name)
    return data

with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Enter Gemini API Key:", type="password")
    model_choice = st.selectbox(options=["gemini-3.8-flash", "gemini-3.6-flash"], label="Select AI Model Engine:")

uploaded_file = st.file_uploader("Upload Scanned Foreign Office Action PDF:", type=["pdf"])
if not api_key:
    st.info("👈 Enter your Gemini API Key in the sidebar configuration panel to unlock the workspace.")
elif uploaded_file is not None:
    if st.button("Parse & Analyze Office Action 🚀", type="primary"):
        with st.spinner("Processing document..."):
            try:
                client = genai.Client(api_key=api_key.strip())
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
                    tmp_file.close()
                st.info("🔄 Staging document within Google File Manager framework...")
                doc_file = client.files.upload(file=tmp_path)
                SINGLE_PASS_PROMPT = """
                You are an expert bilingual Patent Attorney. Analyze the attached foreign office action PDF.
                Perform a deep OCR read, translate all rejections, extract prior art citations, and dissect independent claims.
                Generate your output in two explicit sections separated exactly by the split marker '---CLAIMS_MATRIX_SPLIT---'.
                SECTION 1: Detailed Legal Analysis Report in clean Markdown format including Overview, Ground of Rejections, and strategic Suggestions for the Office Action responses.
                ---CLAIMS_MATRIX_SPLIT---
                SECTION 2: Element-by-element Claim Dissection Matrix Table mapping application features directly against primary references.
                """
                response = None
                for attempt in range(5):
                    try:
                        response = client.models.generate_content(model=model_choice, contents=[doc_file, SINGLE_PASS_PROMPT])
                        break
                    except Exception as api_err:
                        if "503" in str(api_err) and attempt < 4:
                            st.warning(f"⚠️ Server is busy. Retrying automatically...")
                            time.sleep(8)
                        else:
                            raise api_err
                os.unlink(tmp_path)
                if response is None or not response.text:
                    st.error("❌ Empty response received from the engine layer. Please click parse to retry.")
                    st.stop()
                full_content = response.text
                if "---CLAIMS_MATRIX_SPLIT---" in full_content:
                    analysis_part, claims_part = full_content.split("---CLAIMS_MATRIX_SPLIT---", 1)
                else:
                    analysis_part = full_content
                    claims_part = "The claim charts are appended within the primary analysis layer. Please review the Report tab."
                tab1, tab2 = st.tabs(["📝 Legal Analysis Report", "⚖️ Claims Mapping Matrix"])
                with tab1:
                    st.success("✅ Analysis Complete!")
                    st.markdown(analysis_part)
                    st.divider()
                    st.download_button(label="📥 DOWNLOAD REPORT (.docx)", data=create_docx(analysis_part, "CNIPA Legal Analysis Report"), file_name="CNIPA_Report.docx")
                with tab2:
                    st.subheader("⚔️ Element-by-Element Independent Claim Charts")
                    st.markdown(claims_part)
                    st.divider()
                    st.download_button(label="📥 DOWNLOAD MATRIX (.docx)", data=create_docx(claims_part, "Claims Mapping Matrix"), file_name="CNIPA_Claims_Matrix.docx")
            except Exception as e:
                st.error(f"❌ Processing Error: {str(e)}")
