import streamlit as st
from huggingface_hub import InferenceClient
import json
import pandas as pd
import matplotlib.pyplot as plt
import os
import time
from dotenv import load_dotenv
import numpy as np
import re
import random   # Added for shuffling
import uuid     # Added for random element generation

# Load environment variables from .env file
load_dotenv()

# Initialize Hugging Face Inference Client with API token
HF_TOKEN = os.getenv("HF_TOKEN")  # Load token from environment variable
if not HF_TOKEN:
    st.error("Please set the HF_TOKEN environment variable with your Hugging Face API token.")
    st.stop()

client = InferenceClient(token=HF_TOKEN)

# Define unique prompt templates for each difficulty level
easy_prompts = [
    "Generate an easy GMAT-style quantitative question that involves subtracting two large numbers (e.g., a six-digit number minus a two-digit number). Include five answer choices labeled A–E.",
    "Create an easy quantitative problem where the question asks for the sum of a sequence of consecutive integers (for example, summing all numbers from 51 to 100). Provide five multiple-choice options.",
    "Write a GMAT-style question on percent calculations where the problem involves finding the percent increase or decrease of a single value.",
    "Design an easy quantitative question that asks for the average of a small set of numbers. Ensure the question has five multiple-choice options in a GMAT style.",
    "Generate a straightforward GMAT quantitative problem involving a basic ratio or proportion between two numbers. Include five answer choices labeled A–E.",
    "Create an easy question that requires calculating speed, distance, or time with simple numerical values. Format the answer as five multiple-choice options.",
    "Write an easy GMAT quantitative problem on a work-rate scenario involving a single worker completing a task. Provide five multiple-choice answer options.",
    "Design an easy quantitative question that asks for the calculation of simple interest given principal, rate, and time. Include five answer choices labeled A–E.",
    "Generate a basic GMAT-style problem where the candidate solves a single-step linear equation. Format the question with five multiple-choice options.",
    "Create an easy probability question (e.g., finding the probability of a simple event with equally likely outcomes). Present five answer options in GMAT format."
]

medium_prompts = [
    "Generate a medium-difficulty GMAT quantitative problem that involves properties of factorials and divisibility by certain factors. Provide five multiple-choice answer options.",
    "Design a medium-level question requiring a two-step percent change calculation (e.g., an item’s price increases then decreases). Include five answer choices labeled A–E.",
    "Write a GMAT-style quantitative problem on profit and loss where two transactions or conditions must be considered. Provide five multiple-choice options.",
    "Create a medium-difficulty problem that involves mixing two solutions or ingredients and determining the final concentration. Include five answer choices.",
    "Develop a medium-level GMAT question on sequences defined by a simple recurrence relation (for example, each term is a linear function of the previous term). Format with five answer options.",
    "Write a quantitative question in the GMAT style where two or three workers with different rates complete a job. Include five multiple-choice answer options.",
    "Generate a medium-difficulty problem on ratio and proportion that involves combining two or more ratios to find an unknown quantity. Present five answer choices.",
    "Create a medium-level GMAT Data Sufficiency question that asks whether a given algebraic statement is sufficient to determine an unknown value. Provide two statements and five answer options.",
    "Develop a GMAT-style probability problem that requires using combinations to determine the probability of a specific event. Format the question with five answer choices.",
    "Design a medium-difficulty quantitative problem that combines percentage calculations with an average (arithmetic mean) computation. Provide five answer choices."
]

hard_prompts = [
    "Generate a challenging GMAT-style quantitative question involving factorials and the determination of the highest power of a prime factor in n!. Include five multiple-choice answer options.",
    "Create a hard GMAT question that requires multi-step reasoning in a profit and loss scenario with varying markups and discounts. Provide five answer choices.",
    "Design a difficult quantitative problem where a mixture’s concentration changes over time due to evaporation. The question should include several calculation steps and five answer choices.",
    "Write a hard GMAT-style question on sequences where the recurrence relation is non-linear or requires additional insight to find a specific term. Format the question with five answer options.",
    "Generate a challenging GMAT quantitative problem involving work and time where multiple workers with different efficiencies complete overlapping tasks. Include five answer choices labeled A–E.",
    "Develop a hard GMAT Data Sufficiency question that involves two or more interrelated algebraic expressions. Provide two statements and five answer options.",
    "Create a challenging GMAT probability problem that requires calculating conditional probabilities for multiple interdependent events. Format the question with five answer options.",
    "Design a hard GMAT-style question in coordinate geometry that involves solving a system of equations to determine a geometric property (e.g., the distance between two points). Include five answer choices.",
    "Generate a challenging quantitative problem where the candidate must work with functions and their inverses, including composite function operations. Present five answer choices.",
    "Write a hard GMAT quantitative question that involves complex ratios and proportions with fractional relationships, requiring multiple steps to solve. Provide five answer choices labeled A–E."
]

# Updated function to generate a question using a custom prompt with a random element
def generate_question(custom_prompt, max_attempts=3):
    model = "mistralai/Mistral-7B-Instruct-v0.3"
    # Append a random UUID to the prompt to add variability
    random_element = str(uuid.uuid4())
    structured_instruction = (
        "\n\nIMPORTANT: Your entire output MUST be a valid JSON object with exactly these keys: "
        "'question', 'choices', and 'correct_answer'. No additional text should be output. "
        "The 'choices' value must be an array of 5 strings, each starting with 'A.', 'B.', 'C.', 'D.', and 'E.' respectively. "
        "Example: {\"question\": \"What is 2+2?\", \"choices\": [\"A. 3\", \"B. 4\", \"C. 5\", \"D. 6\", \"E. 7\"], \"correct_answer\": \"B\"}"
    )
    final_prompt = custom_prompt + " " + random_element + structured_instruction

    attempts = 0
    while attempts < max_attempts:
        try:
            response = client.text_generation(final_prompt, model=model)
            try:
                question_data = json.loads(response)
            except json.JSONDecodeError:
                json_match = re.search(r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    json_str = re.sub(r',\s*}', '}', json_str)
                    try:
                        question_data = json.loads(json_str)
                    except json.JSONDecodeError:
                        question_data = None
                else:
                    question_data = None

            if question_data is not None and all(k in question_data for k in ['question', 'choices', 'correct_answer']):
                if len(question_data['choices']) < 5:
                    question_data['choices'] += [f"{chr(65+i)}. Option {i+1}" for i in range(len(question_data['choices']), 5)]
                if question_data['correct_answer'] and question_data['correct_answer'][0] in ['A', 'B', 'C', 'D', 'E']:
                    question_data['correct_answer'] = question_data['correct_answer'][0]
                else:
                    question_data['correct_answer'] = 'A'
                return question_data
        except Exception as e:
            st.error(f"Error generating question: {str(e)}")
        attempts += 1
        time.sleep(1)

    st.warning("Unable to generate valid question format after multiple attempts. Using placeholder.")
    return {
        "question": "Sample question (placeholder due to invalid format generation)",
        "choices": ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4", "E. Option 5"],
        "correct_answer": "A"
    }

# Function to generate question bank with 10 questions per difficulty using unique prompts
def generate_question_bank():
    st.write("Generating questions for your test...")
    progress_bar = st.progress(0)
    question_bank = {"easy": [], "medium": [], "hard": []}
    prompt_dict = {
        "easy": easy_prompts,
        "medium": medium_prompts,
        "hard": hard_prompts
    }
    for difficulty in question_bank.keys():
        # Shuffle the prompts to randomize their order
        prompts = prompt_dict[difficulty].copy()
        random.shuffle(prompts)
        count = 0
        while count < 10 and count < len(prompts):
            custom_prompt = prompts[count]
            question = generate_question(custom_prompt)
            retry_count = 0
            while any(q['question'] == question['question'] for q in question_bank[difficulty]) and retry_count < 3:
                time.sleep(1)
                question = generate_question(custom_prompt)
                retry_count += 1
            if any(q['question'] == question['question'] for q in question_bank[difficulty]):
                question = {
                    "question": f"Unique sample {difficulty} question {count+1}",
                    "choices": [f"A. Option 1", f"B. Option 2", f"C. Option 3", f"D. Option 4", f"E. Option 5"],
                    "correct_answer": "A"
                }
            question_bank[difficulty].append(question)
            count += 1
            overall_progress = (len(question_bank["easy"]) + len(question_bank["medium"]) + len(question_bank["hard"])) / 30
            progress_bar.progress(overall_progress)
    progress_bar.progress(1.0)
    st.success("Question bank successfully generated!")
    return question_bank

# Updated update_difficulty function based on the new rules:
def update_difficulty(was_correct, current_difficulty, streak):
    # New adaptive rules:
    # - If correct:
    #     - easy  → medium
    #     - medium → hard
    #     - hard   → hard (remains unchanged)
    # - If wrong:
    #     - easy   → easy (remains unchanged)
    #     - medium → easy
    #     - hard   → medium
    if was_correct:
        if current_difficulty == "easy":
            new_difficulty = "medium"
        elif current_difficulty == "medium":
            new_difficulty = "hard"
        else:  # current_difficulty == "hard"
            new_difficulty = "hard"
    else:
        if current_difficulty == "easy":
            new_difficulty = "easy"
        elif current_difficulty == "medium":
            new_difficulty = "easy"
        else:  # current_difficulty == "hard"
            new_difficulty = "medium"
    
    new_streak = 0
    return new_difficulty, new_streak

def calculate_adaptive_score(difficulty_history, answers):
    difficulty_points = {'easy': 1, 'medium': 2, 'hard': 3}
    raw_score = sum(difficulty_points[diff] for i, diff in enumerate(difficulty_history) if answers[i])
    max_score = sum(difficulty_points[diff] for diff in difficulty_history)
    percentage = (raw_score / max_score) * 100 if max_score > 0 else 0
    weighted_score = 0
    total_weight = 0
    for i, diff in enumerate(difficulty_history):
        weight = (i + 1) / len(difficulty_history)
        total_weight += weight
        if answers[i]:
            weighted_score += difficulty_points[diff] * weight
    normalized_weighted_score = (weighted_score / total_weight) * len(difficulty_history) if total_weight > 0 else 0
    return {
        'raw_score': raw_score,
        'max_score': max_score,
        'percentage': percentage,
        'weighted_score': round(normalized_weighted_score, 1)
    }

def main():
    st.title("Adaptive GMAT Quantitative Test")
    if "question_bank" not in st.session_state:
        st.session_state.question_bank = None
        st.session_state.bank_generated = False
    if "current_question_number" not in st.session_state:
        st.session_state.current_question_number = 0
    if "selected_questions" not in st.session_state:
        st.session_state.selected_questions = []
    if "answers" not in st.session_state:
        st.session_state.answers = []
    if "difficulty_history" not in st.session_state:
        st.session_state.difficulty_history = []
    if "difficulty" not in st.session_state:
        st.session_state.difficulty = "medium"
    if "difficulty_streak" not in st.session_state:
        st.session_state.difficulty_streak = 0
    if "test_started" not in st.session_state:
        st.session_state.test_started = False

    if not st.session_state.bank_generated:
        if st.button("Generate Question Bank"):
            with st.spinner("Generating questions..."):
                st.session_state.question_bank = generate_question_bank()
                st.session_state.bank_generated = True

    if st.session_state.bank_generated and not st.session_state.test_started:
        st.subheader("Test Settings")
        initial_difficulty = st.radio(
            "Select your preferred starting difficulty level:",
            options=["easy", "medium", "hard"],
            index=1,
            horizontal=True
        )
        if st.button("Start Test"):
            st.session_state.test_started = True
            st.session_state.difficulty = initial_difficulty
            st.session_state.current_question_number = 1
            st.session_state.difficulty_streak = 0
            initial_question = st.session_state.question_bank[initial_difficulty][0]
            st.session_state.selected_questions.append(initial_question)
            st.session_state.difficulty_history.append(initial_difficulty)
            st.session_state.question_bank[initial_difficulty].pop(0)
            st.experimental_rerun()

    if st.session_state.test_started and st.session_state.current_question_number <= 10:
        current_q = st.session_state.selected_questions[-1]
        col1, col2 = st.columns([7, 3])
        with col1:
            st.write(f"Question {st.session_state.current_question_number} of 10")
            st.progress(st.session_state.current_question_number / 10)
        with col2:
            st.info(f"Current difficulty: {st.session_state.difficulty_history[-1].capitalize()}")
        st.markdown(f"**{current_q['question']}**")
        user_answer = st.radio("Select your answer:", current_q["choices"], key=f"q{st.session_state.current_question_number}")
        if st.button("Submit Answer"):
            correct_answer = current_q["correct_answer"]
            was_correct = user_answer.startswith(correct_answer)
            st.session_state.answers.append(was_correct)
            if was_correct:
                st.success(f"Correct! The answer is {correct_answer}.")
            else:
                st.error(f"Incorrect. The correct answer is {correct_answer}.")
            new_difficulty, new_streak = update_difficulty(
                was_correct, 
                st.session_state.difficulty_history[-1],
                st.session_state.difficulty_streak
            )
            st.session_state.difficulty = new_difficulty
            st.session_state.difficulty_streak = new_streak
            if st.session_state.current_question_number < 10:
                if new_difficulty != st.session_state.difficulty_history[-1]:
                    if new_difficulty == "hard":
                        st.success("Great job! The next question will be harder.")
                    elif new_difficulty == "easy":
                        st.info("The next question will be easier.")
                    else:
                        st.info(f"Adjusting difficulty to {new_difficulty}.")
                if st.session_state.question_bank[new_difficulty]:
                    next_question = st.session_state.question_bank[new_difficulty][0]
                    st.session_state.selected_questions.append(next_question)
                    st.session_state.difficulty_history.append(new_difficulty)
                    st.session_state.question_bank[new_difficulty].pop(0)
                else:
                    fallback_difficulties = [d for d in ["easy", "medium", "hard"] if st.session_state.question_bank[d]]
                    if fallback_difficulties:
                        fallback_diff = fallback_difficulties[0]
                        next_question = st.session_state.question_bank[fallback_diff][0]
                        st.session_state.selected_questions.append(next_question)
                        st.session_state.difficulty_history.append(fallback_diff)
                        st.session_state.question_bank[fallback_diff].pop(0)
                        st.warning(f"No more questions available at {new_difficulty} difficulty. Using {fallback_diff} instead.")
                    else:
                        st.error("No more questions available in the bank. Test will end now.")
                        st.session_state.current_question_number = 10
                st.session_state.current_question_number += 1
                time.sleep(1)
                st.experimental_rerun()
            else:
                st.session_state.current_question_number += 1
                st.write("Test complete! View your results below.")
                time.sleep(1)
                st.experimental_rerun()

    if st.session_state.test_started and st.session_state.current_question_number > 10:
        st.header("Test Results")
        score_data = calculate_adaptive_score(st.session_state.difficulty_history, st.session_state.answers)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Raw Score", f"{score_data['raw_score']}/{score_data['max_score']}")
        with col2:
            st.metric("Percentage", f"{score_data['percentage']:.1f}%")
        with col3:
            st.metric("Weighted Score", f"{score_data['weighted_score']}")
        st.subheader("Your Difficulty Progression")
        fig, ax = plt.subplots(figsize=(10, 5))
        difficulty_numeric = [{"easy": 1, "medium": 2, "hard": 3}[d] for d in st.session_state.difficulty_history]
        ax.plot(range(1, 11), difficulty_numeric, marker='o', linestyle='-', color='blue', linewidth=2)
        for i, correct in enumerate(st.session_state.answers):
            color = 'green' if correct else 'red'
            ax.plot(i+1, difficulty_numeric[i], marker='o', markersize=10, color=color)
        ax.set_yticks([1, 2, 3])
        ax.set_yticklabels(['Easy', 'Medium', 'Hard'])
        ax.set_xticks(range(1, 11))
        ax.set_xlabel('Question Number')
        ax.set_ylabel('Difficulty Level')
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.set_title('Difficulty Progression Throughout the Test')
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], marker='o', color='w', markerfacecolor='green', markersize=10, label='Correct Answer'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=10, label='Incorrect Answer')
        ]
        ax.legend(handles=legend_elements)
        st.pyplot(fig)
        st.subheader("Question Details")
        summary_data = {
            "Question": [f"Q{i+1}" for i in range(10)],
            "Difficulty": st.session_state.difficulty_history,
            "Result": ["✓" if ans else "✗" for ans in st.session_state.answers],
            "Points": [{"easy": 1, "medium": 2, "hard": 3}[diff] if ans else 0 
                      for diff, ans in zip(st.session_state.difficulty_history, st.session_state.answers)]
        }
        summary_df = pd.DataFrame(summary_data)
        def highlight_result(val):
            color = 'lightgreen' if val == "✓" else 'lightcoral' if val == "✗" else ''
            return f'background-color: {color}'
        styled_df = summary_df.style.applymap(highlight_result, subset=['Result'])
        st.write(styled_df)
        st.subheader("Performance Analysis")
        difficulty_stats = {}
        for diff in ["easy", "medium", "hard"]:
            questions = [i for i, d in enumerate(st.session_state.difficulty_history) if d == diff]
            if questions:
                correct = sum(st.session_state.answers[i] for i in questions)
                total = len(questions)
                difficulty_stats[diff] = {
                    "correct": correct,
                    "total": total,
                    "percentage": round((correct / total) * 100, 1) if total > 0 else 0
                }
        cols = st.columns(3)
        for i, diff in enumerate(["easy", "medium", "hard"]):
            if diff in difficulty_stats:
                with cols[i]:
                    st.metric(
                        f"{diff.capitalize()} Questions", 
                        f"{difficulty_stats[diff]['correct']}/{difficulty_stats[diff]['total']}",
                        f"{difficulty_stats[diff]['percentage']}%"
                    )
        st.subheader("Skill Assessment")
        if score_data['percentage'] >= 80:
            if difficulty_stats.get('hard', {}).get('percentage', 0) >= 70:
                assessment = "Advanced"
                description = "You have mastered most GMAT quantitative concepts."
            elif difficulty_stats.get('medium', {}).get('percentage', 0) >= 70:
                assessment = "Proficient"
                description = "You have solid understanding of most GMAT quantitative concepts."
            else:
                assessment = "Intermediate"
                description = "You have good grasp of basic concepts but should work on harder problems."
        elif score_data['percentage'] >= 60:
            assessment = "Developing"
            description = "You understand foundational concepts but need more practice with medium and hard problems."
        else:
            assessment = "Foundational"
            description = "Focus on strengthening your understanding of basic GMAT quantitative concepts."
        st.info(f"**Overall Assessment: {assessment}**\n\n{description}")
        if st.button("Take Another Test"):
            st.session_state.test_started = False
            st.session_state.current_question_number = 0
            st.session_state.selected_questions = []
            st.session_state.answers = []
            st.session_state.difficulty_history = []
            st.session_state.difficulty = "medium"
            st.session_state.difficulty_streak = 0
            st.experimental_rerun()

if __name__ == "__main__":
    main()
