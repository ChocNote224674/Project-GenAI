"""
Medical Chatbot & QCM Application using Streamlit.

This application allows users to:
- Ask medical-related questions and receive AI-generated answers.
- Take multiple-choice quizzes (QCM) and download them as PDFs.
- Provide feedback on the chatbot.
"""
from io import BytesIO  

# Third-party libraries
import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Internal modules
from utils import is_feedback_file_empty
# ---------------- CONFIGURATION ----------------
API_ANSWER_URL = "http://127.0.0.1:8000/answer"
API_QCM_URL = "http://127.0.0.1:8000/qcm"
GENERAL_FEEDBACK_FILE = "feedback.csv"

# ---------------- STYLE FOR CENTERED CONTENT ----------------
st.markdown(
    """
    <style>
    .centered {
        text-align: center;
    }
    .stButton>button {
        display: flex;
        margin: 0 auto;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------- STREAMLIT INTERFACE ----------------
st.markdown(
    """
    <h1 style="text-align: center;">🔬 Medical Chatbot & QCM </h1>
    """,
    unsafe_allow_html=True
)

# Inject CSS to center the tabs
st.markdown(
    """
    <style>
    div[data-testid="stHorizontalBlock"] {
        display: flex;
        justify-content: center;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Title (Centered)
st.markdown(
    """
    <h1 style="text-align: center;">🏥🤖 Medical Chatbot & QCM 📚</h1>
    """,
    unsafe_allow_html=True
)

tab_about, tab_chat, tab_QCM, tab_feedback = st.tabs(["🏥 About", "💬 Chatbot", "📚 QCM", "📢 Feedback"])

# ---------------- ABOUT THE APPLICATION ----------------
with tab_about:
    st.header("🏥 About the Medical Chatbot & QCM")
    st.markdown("""
        Welcome to the **Medical Chatbot & QCM** application! 🏥  
        
        This tool helps users:
        - ✅ **Ask medical-related questions** and receive AI-generated answers.  
        - ✅ **Test their knowledge** with multiple-choice quizzes (QCM).  
        - ✅ **Download QCMs as PDFs** for offline practice.  
        
        🚀 Whether you're a medical student, professional, or just curious about healthcare,  
        this tool is designed to **enhance your learning experience**!  
    """)

# ---------------- CHATBOT ----------------
with tab_chat:
    st.header("💬 Chat with AI")
    st.write("Ask a medical question and receive AI-generated responses.")

    if "history" not in st.session_state:
        st.session_state.history = []

    for chat in st.session_state.history:
        with st.chat_message("user"):
            st.write(chat["question"])
        with st.chat_message("assistant"):
            st.write(chat["response"])
            st.markdown(f"🔍 **Source:** {chat['sources']}")
            st.markdown(f"📌 **Focus Area:** {chat['focus_area']}")
            st.markdown(f"💡 **Similarity Score:** {chat['similarity']}")
            if chat.get("metrics"):
                with st.expander("📊 View Metrics"):
                    st.code(chat["metrics"], language="json")

    question = st.chat_input("Type your message...")
    if question:
        response = requests.post(API_ANSWER_URL, json={"question": question}, timeout=500)
        if response.status_code == 200:
            data = response.json()
            st.session_state.history.append({
                "question": question,
                "response": data.get('answer', "No answer available."),
                "sources": data.get('source', "Unknown"),
                "focus_area": data.get('focus_area', "Not specified"),
                "similarity": data.get('similarity', "N/A"),
                "metrics": data.get("metrics", {}),
                "feedback": None,
            })
            st.rerun()
        else:
            st.error("Error retrieving the answer.")

# ---------------- QCM ----------------
with tab_QCM:
    st.header("📚 QCM Practice")
    st.write("Test your knowledge with multiple-choice questions.")

    if "qcm_questions" not in st.session_state:
        st.session_state.qcm_questions = []

    if st.button("Generate QCM"):
        response = requests.get(API_QCM_URL, params={"n": 5}, timeout=500)  
        if response.status_code == 200:
            st.session_state.qcm_questions = response.json().get("questions", [])
            st.success("✅ QCM Generated! You can now take the test or download it.")
        else:
            st.error("⚠️ Failed to fetch QCM questions.")

    if st.session_state.qcm_questions:
        pdf_content = BytesIO()  
        c = canvas.Canvas(pdf_content, pagesize=letter)
        c.setFont("Helvetica", 12)
        Y_POSITION = 750  

        for i, q in enumerate(st.session_state.qcm_questions, start=1):
            c.drawString(50, Y_POSITION, f"Q{i}: {q['question']}")
            Y_POSITION -= 20
            for option in q["options"]:
                c.drawString(70, Y_POSITION, f"- {option}")
                Y_POSITION -= 15
            c.drawString(50, Y_POSITION, f"✅ Correct Answer: {q['correct_answer']}")
            Y_POSITION -= 30

        c.save()
        pdf_content.seek(0)

        st.download_button(
            label="📥 Download QCM as PDF",
            data=pdf_content,
            file_name="QCM.pdf",
            mime="application/pdf"
        )

    if st.session_state.qcm_questions:
        user_answers = {}
        for idx, q in enumerate(st.session_state.qcm_questions):
            st.subheader(f"Q{idx+1}: {q['question']}")
            user_answers[q["question"]] = st.radio(
                "Select your answer:",
                q["options"],
                key=f"qcm_{idx}"
            )

        if st.button("Submit Answers"):
            score = sum(1 for q in st.session_state.qcm_questions if user_answers[q["question"]] == q["correct_answer"])
            st.success(f"✅ You scored {score} / {len(st.session_state.qcm_questions)}!")
            for q in st.session_state.qcm_questions:
                if user_answers[q["question"]] != q["correct_answer"]:
                    st.warning(f"❌ Incorrect: {q['question']}")
                    st.info(f"✔️ Correct Answer: {q['correct_answer']}")

# ---------------- FEEDBACK ----------------
with tab_feedback:
    st.header("📢 User Feedback")

    # General feedback
    st.subheader("📝 General Feedback")
    general_score = st.slider("Rate the overall experience:", 1, 5, 3)
    general_comment = st.text_area("Any suggestions to improve the application?")
    
    if st.button("Submit General Feedback"):
        df = pd.DataFrame([[general_score, general_comment]], columns=["score", "comment"])
        if is_feedback_file_empty(GENERAL_FEEDBACK_FILE):
            df.to_csv(GENERAL_FEEDBACK_FILE, mode='w', header=True, index=False)
        else:
            df.to_csv(GENERAL_FEEDBACK_FILE, mode='a', header=False, index=False)
        st.success("✅ Thank you for your feedback!")

    # Feedback dashboard
    if st.checkbox("📊 View Feedback Dashboard"):
        df = pd.read_csv(GENERAL_FEEDBACK_FILE)
        
        # Display Average Score
        avg_score = df["score"].mean()
        st.write(f"**Average Rating:** ⭐ {avg_score:.2f}/5")

        # Count occurrences of each score (1 to 5)
        score_counts = df["score"].value_counts().sort_index()

        # Create a bar chart using Seaborn
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.barplot(x=score_counts.index, y=score_counts.values, palette="Blues", ax=ax)

        ax.set_title("User Feedback Distribution", fontsize=14)
        ax.set_xlabel("Ratings (1 = Bad, 5 = Excellent)", fontsize=12)
        ax.set_ylabel("Number of Responses", fontsize=12)
        ax.set_xticks(range(1, 6))  # Ensure labels show 1 to 5

        # Display the chart
        st.pyplot(fig)
