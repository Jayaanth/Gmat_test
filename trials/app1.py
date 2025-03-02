import streamlit as st
import pandas as pd
import random
import json
from dotenv import load_dotenv
import os
load_dotenv()
from huggingface_hub import InferenceClient

# Set page configuration
st.set_page_config(page_title="GMAT Quant Quiz", page_icon="🧮", layout="centered")

# Initialize session state variables
if 'current_question' not in st.session_state:
    st.session_state.current_question = None
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'questions_asked' not in st.session_state:
    st.session_state.questions_asked = 0
if 'selected_level' not in st.session_state:
    st.session_state.selected_level = None

# Hugging Face API key (in production, use environment variables)
# st.secrets["HF_TOKEN"] for Streamlit Cloud
def get_api_key():
    api_key = os.getenv("HF_TOKEN")
    if not api_key:
        api_key = st.secrets.get("HF_TOKEN", None)
    return api_key

# Function to generate a question using Mistral-7B
def generate_question(level):
    hf_token = get_api_key()
    if not hf_token:
        st.error("API key not found. Please set the HF_TOKEN.")
        return None
    
    # Initialize the client
    client = InferenceClient(
        model='deepseek-ai/DeepSeek-R1-Distill-Qwen-32B',
        token=hf_token
    )
    
    # Craft a detailed prompt based on the difficulty level
    level_descriptions = {
        "easy": "basic arithmetic, simple algebra, straightforward data interpretation",
        "medium": "intermediate algebra, rates and ratios, moderate geometry, basic statistics",
        "hard": "challenging algebra, complex geometry, probability, advanced number properties, difficult word problems"
    }
    
    # Topic selection based on GMAT content areas
    topics = {
        "easy": ["Basic Arithmetic", "Simple Algebra", "Data Interpretation"],
        "medium": ["Algebra", "Geometry", "Statistics", "Word Problems"],
        "hard": ["Advanced Algebra", "Probability", "Combinatorics", "Complex Geometry"]
    }
    
    # Randomly select a topic appropriate for the level
    selected_topic = random.choice(topics[level])
    
    # Create a prompt for Mistral model
    prompt = f"""<s>[INST] You are a GMAT question generator specialized in creating quantitative questions.
    
Generate a GMAT quantitative question of {level} difficulty level on the topic of {selected_topic}.

The question should:
- Be {level} level ({level_descriptions[level]})
- Include exactly 4 answer choices (A, B, C, D)
- Have only one correct answer
- Include a detailed explanation of the solution
- Be formatted as a valid JSON object with the following structure:

{{
    "question": "The full question text here",
    "choices": ["A. choice 1", "B. choice 2", "C. choice 3", "D. choice 4"],
    "correct_answer": "The letter of the correct answer (A, B, C, or D)",
    "explanation": "A step-by-step explanation of how to solve the problem"
}}

Ensure the JSON is valid with no formatting issues. The question should authentically reflect the style and difficulty of real GMAT questions.
Make sure there are no extra characters, only valid JSON. [/INST]</s>
"""
    
    try:
        # Generate text using the model
        response = client.text_generation(prompt)
        
        # Find JSON in the response
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = response[json_start:json_end]
            # Remove any formatting issues that might cause JSON parsing to fail
            json_str = json_str.replace('\n', ' ').replace('\r', ' ')
            question_data = json.loads(json_str)
            
            # Add level to the question data
            question_data["level"] = level
            
            return question_data
        else:
            st.error("Could not extract valid JSON from the API response.")
            st.write(response)  # For debugging
            return None
            
    except Exception as e:
        st.error(f"Error generating question: {str(e)}")
        return None

# Function to check the answer
def check_answer(selected_answer, correct_answer):
    # Extract just the letter if the full answer was selected
    if selected_answer.startswith(("A.", "B.", "C.", "D.")):
        selected_letter = selected_answer[0]
    else:
        selected_letter = selected_answer
        
    # Extract just the letter if the correct answer contains the full option
    if correct_answer.startswith(("A.", "B.", "C.", "D.")):
        correct_letter = correct_answer[0]
    else:
        correct_letter = correct_answer
        
    return selected_letter == correct_letter

# Cache a few questions to avoid repeated API calls during development
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_cached_question(level):
    return generate_question(level)

# Main app layout
st.title("GMAT Quant Quiz with Dynamic Questions")

# Welcome message and instructions
st.markdown("""
Welcome to the GMAT Quant Quiz! This app dynamically generates questions 
based on your selected difficulty level using the Mistral-7B language model.
""")

# API key input (for development purposes)
with st.sidebar:
    if not get_api_key():
        user_api_key = st.text_input("Enter Hugging Face API Token:", type="password")
        if user_api_key:
            os.environ["HF_TOKEN"] = user_api_key
            st.success("API key set!")

# Level selection at the start
if st.session_state.current_question is None:
    st.subheader("Select Question Level")
    level = st.radio(
        "Choose difficulty level:",
        options=["easy", "medium", "hard"],
        index=0
    )
    
    if st.button("Generate Question"):
        with st.spinner("Generating a new question..."):
            st.session_state.selected_level = level
            st.session_state.current_question = get_cached_question(level)
            if st.session_state.current_question:
                st.experimental_rerun()
            else:
                st.error("Failed to generate a question. Please try again.")

# Display the current question
if st.session_state.current_question is not None:
    # Display question information
    st.subheader(f"Question {st.session_state.questions_asked + 1}")
    st.markdown(f"**Level: {st.session_state.current_question['level']}**")
    st.markdown(f"**{st.session_state.current_question['question']}**")
    
    # Display choices
    choice = st.radio(
        "Select your answer:",
        options=st.session_state.current_question['choices'],
        key="current_choice"
    )
    
    # Check answer
    if st.button("Submit Answer"):
        is_correct = check_answer(choice, st.session_state.current_question['correct_answer'])
        
        if is_correct:
            st.success("Correct! 🎉")
            st.session_state.score += 1
        else:
            correct_choice = st.session_state.current_question['correct_answer']
            # If correct answer is just the letter, find the full answer
            if correct_choice in ["A", "B", "C", "D"]:
                for c in st.session_state.current_question['choices']:
                    if c.startswith(f"{correct_choice}."):
                        correct_choice = c
                        break
            st.error(f"Incorrect. The correct answer is: {correct_choice}")
        
        # Show explanation
        st.info(f"Explanation: {st.session_state.current_question['explanation']}")
        
        # Update questions asked
        st.session_state.questions_asked += 1
        
        # Next question button
        if st.button("Next Question"):
            with st.spinner("Generating next question..."):
                st.session_state.current_question = get_cached_question(st.session_state.selected_level)
                if not st.session_state.current_question:
                    st.error("Failed to generate a question. Please try again.")
            
# Display score
if st.session_state.questions_asked > 0:
    st.sidebar.subheader("Quiz Progress")
    st.sidebar.write(f"Score: {st.session_state.score}/{st.session_state.questions_asked}")
    st.sidebar.write(f"Current Level: {st.session_state.selected_level}")
    
    # Option to restart quiz
    if st.sidebar.button("Restart Quiz"):
        st.session_state.current_question = None
        st.session_state.score = 0
        st.session_state.questions_asked = 0
        st.session_state.selected_level = None
        st.experimental_rerun()
        
    # Option to change difficulty
    if st.sidebar.button("Change Difficulty"):
        st.session_state.current_question = None
        st.experimental_rerun()