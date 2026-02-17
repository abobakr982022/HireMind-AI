import requests
import streamlit as st
from io import BytesIO
from pypdf import PdfReader
import docx

# PDF generation
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch


st.set_page_config(page_title="HireMind AI PRO", layout="centered")
st.title("HireMind AI 🧠 PROOOOOO")
st.caption("Professional HR Screening Engine")

# ================= MASTER HR PROMPT =================

BASE_PROMPT = """
You are a Senior HR Talent Acquisition Specialist and Workforce Strategist.

Your task is to perform a complete professional screening analysis of a candidate against the Job Description.

IMPORTANT:
- Be strictly evidence-based.
- Do NOT assume skills not clearly stated.
- Be objective and structured.
- Return clean structured text (NOT JSON, NOT markdown).

=============================
1) EXECUTIVE SUMMARY
=============================
- 4–6 lines maximum.
- Mention strongest alignment and biggest concern.

=============================
2) CORE COMPETENCY MATCH
=============================
A. Technical / Functional Skills
- Matched Skills
- Missing or Weak Skills

B. Tools & Systems Fit

C. Domain / Industry Experience

=============================
3) EXPERIENCE & SENIORITY ANALYSIS
=============================

=============================
4) PERFORMANCE & IMPACT INDICATORS
=============================

=============================
5) BEHAVIORAL & SOFT SKILLS ASSESSMENT
=============================

=============================
6) RISK ASSESSMENT
=============================

Classify Risk Level:
Low / Medium / High

=============================
7) SCORING MODEL (TOTAL 100)
=============================

Score using:
Skills Match (0–30)
Experience Fit (0–20)
Domain & Tools Fit (0–20)
Impact & Achievements (0–15)
Behavioral & Leadership Fit (0–10)
Risk Adjustment (+/-5)

Return:
Total Score: XX/100
Hiring Signal: Strong Hire | Hire | Conditional | Not Recommended

=============================
8) INTERVIEW STRATEGY
=============================
- 5 Technical Questions
- 3 Behavioral Questions
- 2 Risk Validation Questions

=============================
9) FINAL HR RECOMMENDATION
=============================

Job Description:
<<JOB_DESCRIPTION>>

Candidate CV:
<<CANDIDATE_CV>>
"""

# ================= OLLAMA =================

def call_ollama(prompt, model):
    url = "http://localhost:11434/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False}
    r = requests.post(url, json=payload, timeout=180)
    r.raise_for_status()
    return r.json().get("response", "").strip()


# ================= FILE READING =================

def read_pdf(file):
    reader = PdfReader(BytesIO(file.getvalue()))
    text = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text.append(t)
    return "\n".join(text)

def read_docx(file):
    document = docx.Document(BytesIO(file.getvalue()))
    return "\n".join([p.text for p in document.paragraphs if p.text.strip()])

def read_txt(file):
    return file.getvalue().decode("utf-8", errors="ignore")

def extract_text(file):
    name = file.name.lower()
    if name.endswith(".pdf"):
        return read_pdf(file)
    if name.endswith(".docx"):
        return read_docx(file)
    if name.endswith(".txt"):
        return read_txt(file)
    return ""


# ================= PDF REPORT =================

def generate_pdf(report_text):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("HireMind AI – Professional HR Screening Report", styles["Title"]))
    story.append(Spacer(1, 0.3 * inch))

    for line in report_text.split("\n"):
        story.append(Paragraph(line.replace("&", "&amp;"), styles["Normal"]))
        story.append(Spacer(1, 0.15 * inch))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ================= UI =================

with st.sidebar:
    model_name = st.text_input("Ollama Model", "llama3.1:8b")
    st.caption("Make sure Ollama is running: ollama serve")

st.subheader("Upload Job Description")
jd_file = st.file_uploader("Upload JD (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"])

st.subheader("Upload Candidate CV")
cv_file = st.file_uploader("Upload CV (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"])

if st.button("Analyze Candidate", use_container_width=True):

    if not jd_file or not cv_file:
        st.error("Please upload both JD and CV files.")
        st.stop()

    jd_text = extract_text(jd_file)
    cv_text = extract_text(cv_file)

    prompt = BASE_PROMPT.replace("<<JOB_DESCRIPTION>>", jd_text).replace("<<CANDIDATE_CV>>", cv_text)

    with st.spinner("Analyzing candidate professionally..."):
        report = call_ollama(prompt, model_name)

    st.subheader("Professional Screening Report")
    st.write(report)

    # Download TXT
    st.download_button(
        "Download Report (TXT)",
        data=report,
        file_name="hiremind_report.txt",
        mime="text/plain",
        use_container_width=True
    )

    # Download PDF
    pdf_bytes = generate_pdf(report)
    st.download_button(
        "Download Report (PDF)",
        data=pdf_bytes,
        file_name="hiremind_report.pdf",
        mime="application/pdf",
        use_container_width=True
    )
