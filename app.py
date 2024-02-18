from tempfile import NamedTemporaryFile
import os

import streamlit as st
from llama_index.core import VectorStoreIndex
from llama_index.llms.openai import OpenAI
from llama_index.readers.file import PDFReader
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Chat with the PDF",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="auto",
    menu_items=None,
)

if "messages" not in st.session_state.keys():  # Initialize the chat messages history
    st.session_state.messages = [
        {"role": "assistant", "content": "Ask me a question about your document!"}
    ]

uploaded_file = st.file_uploader("Upload your resume")
if uploaded_file:
    bytes_data = uploaded_file.read()
    with NamedTemporaryFile(delete=False) as tmp:  # open a named temporary file
        tmp.write(bytes_data)  # write data from the uploaded file into it
        with st.spinner(
            text="Analyzing your resume – hang tight! This should take a moment."
        ):
            reader = PDFReader()
            docs = reader.load_data(tmp.name)
            llm = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_API_BASE"),
                model="gpt-3.5-turbo",
                temperature=0.0,
                system_prompt='''
                You are an AI model trained to assist users in refining their uploaded resumes for better job search outcomes. Your tasks include:

                Analyze Resume: Automatically extract key sections from the uploaded resume, such as personal details, work experience, education, and skills. Ensure accuracy in the extraction of details, especially for work experience bullet points.

                Conduct Basic Checks: Identify and report common resume issues like repetitive action verbs, excessive buzzwords, and the use of personal pronouns. Offer suggestions for improvement.

                Detailed Work Experience Review: Evaluate each work experience bullet point to ensure it includes a clear action ("What"), the method or strategy used ("How"), and the outcome or result ("Result"). Provide feedback and recommendations for any points lacking these elements.

                Resume Tailoring Advice: Provide specific suggestions for incorporating job-relevant hard skills and experiences into the resume. Optionally, help draft a summary that highlights the candidate’s fit for their target jobs.

                Instructions for Interaction:

                Ask for user confirmation on extracted resume sections.
                Present findings and suggestions in a structured format for each review step.
                Engage in a dialogue with the user, asking for additional details as necessary to refine recommendations.
                Ensure advice is actionable and tailored to the user’s specific job search goals.
                End of Prompt''',
            )
            index = VectorStoreIndex.from_documents(docs)
    os.remove(tmp.name)  # remove temp file

    if "chat_engine" not in st.session_state.keys():  # Initialize the chat engine
        st.session_state.chat_engine = index.as_chat_engine(
            chat_mode="condense_question", verbose=False, llm=llm
        )

if prompt := st.chat_input(
    "Your question"
):  # Prompt for user input and save to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

for message in st.session_state.messages:  # Display the prior chat messages
    with st.chat_message(message["role"]):
        st.write(message["content"])

# If last message is not from assistant, generate a new response
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = st.session_state.chat_engine.stream_chat(prompt)
            st.write_stream(response.response_gen)
            message = {"role": "assistant", "content": response.response}
            st.session_state.messages.append(message)  # Add response to message history