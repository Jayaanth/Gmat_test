import streamlit as st
import streamlit as st
from huggingface_hub import InferenceClient
import random
from dotenv import load_dotenv
import os
load_dotenv()
hf_token=os.getenv("HF_TOKEN")
# Initialize the Inference Client with your Hugging Face API token
client = InferenceClient(model='mistralai/Mistral-7B-Instruct-v0.2',token=hf_token)
print("Logged in")

# Difficulty levels mapping
DIFFICULTY_LEVELS = {"easy": 1, "medium": 2, "hard": 3}

def generate_question(difficulty):
    prompt = f"Generate a {difficulty} level GMAT Quantitative question with four options and the correct answer."
    response = client.text_generation(prompt)
    return parse_question(response)

def parse_question(text):
    lines = text.strip().split("\n")
    question = lines[0]
    options = lines[1:5]
    correct_answer = options[0]  # Assume the first option is correct
    random.shuffle(options)
    return {"question": question, "options": options, "answer": correct_answer}

st.title("AI-Powered Adaptive GMAT Test")

# Initialize session state variables
if "questions" not in st.session_state:
    st.session_state.questions = []
    st.session_state.difficulty = "medium"
    st.session_state.score = 0
    st.session_state.current_index = 0

# Start Test button
if st.button("Start Test"):
    st.session_state.questions = [generate_question(st.session_state.difficulty) for _ in range(10)]
    st.session_state.current_index = 0
    st.experimental_rerun()

# Display questions if available
if st.session_state.questions:
    q = st.session_state.questions[st.session_state.current_index]
    st.write(q["question"])
    user_answer = st.radio("Choose an answer:", q["options"])

    if st.button("Submit Answer"):
        if user_answer == q["answer"]:
            st.session_state.score += DIFFICULTY_LEVELS[st.session_state.difficulty]
            st.session_state.difficulty = "hard" if st.session_state.difficulty == "medium" else "medium"
        else:
            st.session_state.difficulty = "easy" if st.session_state.difficulty == "medium" else "medium"

        st.session_state.current_index += 1
        if st.session_state.current_index < 10:
            st.experimental_rerun()
        else:
            st.write(f"Test Completed! Your Score: {st.session_state.score}")

