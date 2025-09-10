import streamlit as st
import subprocess
import os

st.set_page_config(page_title="Skipera Runner", layout="wide")
st.title("🚀 Skipera Course Runner")

cookies = st.text_area("🍪 Enter your cookies (JSON format)")
api_key = st.text_input("🔑 Enter Perplexity API Key", type="password")
course_name = st.text_input("📘 Enter Course Slug (e.g. project-management-foundations-initiation)")
use_llm = st.checkbox("Use LLM to solve graded assignments", value=True)

if st.button("▶️ Start Course"):
    if not cookies or not api_key or not course_name:
        st.error("Please provide all required inputs.")
    else:
        # set environment vars so config.py picks them
        os.environ["SKIPERA_COOKIES"] = cookies
        os.environ["PERPLEXITY_API_KEY"] = api_key

        st.info(f"Running course: **{course_name}** ...")
        log_placeholder = st.empty()

        command = ["python", "main.py", course_name]
        if use_llm:
            command.append("--llm")

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        logs = ""
        for line in process.stdout:
            logs += line
            log_placeholder.text_area("📜 Logs", logs, height=400)

        process.wait()
        st.success("✅ Course execution finished!")
