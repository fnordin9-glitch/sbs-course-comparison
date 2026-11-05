"""SBS Course Comparison - pilot web app.

Deploy on Streamlit Community Cloud. Reference PDFs reside in course_plans/.
The app does not intentionally persist uploads or answers, but hosting and model
providers may process/retain data under their own terms.
"""
from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from google import genai
from google.genai import types

from core import Course, detect_courses_from_list, extract_pdf_text, load_catalog, make_prompt, SYSTEM_INSTRUCTION

BASE_DIR = Path(__file__).parent
REFERENCE_DIR = BASE_DIR / "course_plans"
MAX_UPLOAD_BYTES = 8 * 1024 * 1024
BATCH_SIZE = 8
MAX_SELECTED = 32
MAX_ANALYSES_SESSION = 3
MODEL = "gemini-2.5-flash"

st.set_page_config(page_title="SBS Course Comparison", page_icon="🎓", layout="centered")
st.title("SBS Course Comparison")
st.caption("A preliminary study-abroad course overlap guide. Not an official decision.")


def get_secret(name: str) -> str:
    try:
        return str(st.secrets.get(name, os.environ.get(name, "")))
    except (FileNotFoundError, KeyError):
        return str(os.environ.get(name, ""))


@st.cache_data(show_spinner=False)
def reference_courses() -> list[Course]:
    return load_catalog(REFERENCE_DIR)


@st.cache_data(show_spinner=False, max_entries=150)
def reference_text(file_path: str) -> str:
    content = Path(file_path).read_bytes()
    return extract_pdf_text(content, max_pages=35, max_chars=26000)[0]


# Optional shared pilot code. It is not a substitute for real university SSO.
access_code = get_secret("APP_ACCESS_CODE")
if access_code:
    entered = st.text_input("Pilot access code", type="password")
    if entered != access_code:
        st.info("Enter the pilot access code to continue.")
        st.stop()

with st.expander("What this service does and does not do", expanded=False):
    st.write(
        "This tool compares a proposed exchange course with the SBS courses you "
        "select as previously studied. It may miss similarities or report false "
        "positives. It checks only available reference PDFs, not your entire "
        "academic history. Please follow the official SBS Learning Agreement "
        "and credit-transfer instructions."
    )
    st.write(
        "Do not upload a transcript, name, student ID, personal identification "
        "number, grades, or other personal information. Use a simple list of "
        "course codes if you want to upload a list. The proposed course syllabus "
        "and relevant reference-text excerpts are sent to an external AI provider "
        "for analysis."
    )

try:
    courses = reference_courses()
except Exception as exc:
    st.error(f"Could not load the reference course bank: {exc}")
    st.stop()

if not courses:
    st.warning("No SBS reference PDFs have been added yet. The administrator must add PDFs to course_plans/ and redeploy.")
    st.stop()

st.success(f"{len(courses)} SBS reference syllabi available")
st.header("1. Select courses you have already studied")
st.write("Search the course list and select only courses you have completed. Or upload a plain list of course codes to suggest selections.")

plain_list = st.file_uploader(
    "Optional: upload a course list (PDF, TXT or CSV, no personal data)",
    type=["pdf", "txt", "csv"],
    key="history_file",
)
list_text = st.text_area("Or paste course codes/titles here (optional)", height=75,
                         placeholder="FE1234\nFE5678")

suggested: list[str] = []
if plain_list is not None:
    if plain_list.size > 2 * 1024 * 1024:
        st.error("The course list must be smaller than 2 MB.")
    else:
        try:
            if plain_list.name.lower().endswith(".pdf"):
                extracted, _ = extract_pdf_text(plain_list.getvalue(), max_pages=8, max_chars=12000)
            else:
                extracted = plain_list.getvalue().decode("utf-8-sig", errors="replace")[:12000]
            suggested.extend(detect_courses_from_list(extracted, courses))
        except Exception as exc:
            st.warning(f"Could not read the course list: {exc}")
if list_text.strip():
    suggested.extend(detect_courses_from_list(list_text, courses))

by_code = {c.code: c for c in courses}
if len(suggested) > 0:
    st.info(f"Identified {len(set(suggested))} possible SBS course(s) from your list. Confirm the selection below.")

# Distinct widget key when a newly uploaded list has different suggestions.
suggested = sorted(set(suggested))
import hashlib
list_signature = hashlib.sha256((str(sorted(suggested)) + str(plain_list.name if plain_list else "")).encode()).hexdigest()[:12]
chosen = st.multiselect(
    "Previously studied courses (confirm manually)",
    options=list(by_code),
    default=suggested,
    format_func=lambda code: by_code[code].display,
    key=f"selected_{list_signature}",
    max_selections=MAX_SELECTED,
)
if chosen:
    st.caption(f"{len(chosen)} selected course(s). Only these will be used for the comparison.")

st.header("2. Upload the course you want to study abroad")
foreign_file = st.file_uploader("Foreign course syllabus (PDF, maximum 8 MB)", type=["pdf"], key="foreign")

st.header("3. Compare")
consent = st.checkbox(
    "I confirm that the uploaded documents contain no personal data, and I understand "
    "that the selected course texts and proposed course syllabus are processed by Google's Gemini API."
)

if "analysis_count" not in st.session_state:
    st.session_state.analysis_count = 0

if st.button("Compare courses", type="primary", disabled=not(bool(chosen) and foreign_file and consent)):
    if st.session_state.analysis_count >= MAX_ANALYSES_SESSION:
        st.error("This pilot allows up to three analyses per browser session.")
        st.stop()
    if foreign_file.size > MAX_UPLOAD_BYTES:
        st.error("The foreign syllabus exceeds 8 MB.")
        st.stop()
    key = get_secret("GEMINI_API_KEY")
    if not key:
        st.error("The administrator has not configured the GEMINI_API_KEY secret.")
        st.stop()
    try:
        foreign_text, pages = extract_pdf_text(foreign_file.getvalue(), max_pages=30, max_chars=38000)
    except Exception as exc:
        st.error(f"Could not read the foreign syllabus: {exc}")
        st.stop()

    st.session_state.analysis_count += 1
    selected_courses = [by_code[code] for code in chosen]
    model_client = genai.Client(api_key=key)
    responses: list[tuple[list[str], str]] = []
    failed = False
    for start in range(0, len(selected_courses), BATCH_SIZE):
        batch = selected_courses[start:start + BATCH_SIZE]
        refs: list[tuple[Course, str]] = []
        try:
            for course in batch:
                refs.append((course, reference_text(course.path)))
            prompt = make_prompt(foreign_text, refs)
            with st.spinner(f"Comparing courses {start + 1}-{start + len(batch)} of {len(selected_courses)}..."):
                reply = model_client.models.generate_content(
                    model=MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.2,
                        max_output_tokens=4500,
                    ),
                )
            if not reply.text:
                raise RuntimeError("The AI returned no text.")
            responses.append(([c.code for c in batch], reply.text))
        except Exception:
            # Avoid showing raw provider errors in the student UI or storing the upload.
            st.error("The analysis could not be completed. A service quota, unreadable reference PDF, or temporary API issue may be responsible. Contact the SBS administrator.")
            failed = True
            break

    if responses:
        st.subheader("Preliminary comparison")
        for codes, answer in responses:
            if len(responses) > 1:
                st.markdown("**Selected SBS courses:** " + ", ".join(codes))
            st.markdown(answer)
            st.divider()
        st.warning(
            "Preliminary guidance only. A missed overlap is possible. The tool compared only "
            "your selected courses and the available PDFs. No approval or credit-transfer decision is made."
        )
        st.download_button(
            "Download comparison as text",
            data="\n\n".join(answer for _, answer in responses),
            file_name="SBS_preliminary_course_comparison.txt",
            mime="text/plain",
        )
    if failed and responses:
        st.warning("The results above cover only completed batches; remaining selected courses were NOT checked.")

st.divider()
st.caption("Pilot version. No student database or account is created by this app. The hosting platform and AI provider have their own data-processing terms. SBS should approve the deployment before inviting students.")
