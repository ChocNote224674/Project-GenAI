from io import BytesIO  
import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import speech_recognition as sr
import time
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from utils import is_feedback_file_empty

# ---------------- CONFIGURATION ----------------
API_ANSWER_URL = "http://127.0.0.1:8000/answer"
API_QCM_URL = "http://127.0.0.1:8000/qcm"
GENERAL_FEEDBACK_FILE = "feedback.csv"


def listen_and_transcribe():
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()

        with microphone as source:
            st.write("🎤 Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source)
            st.write("🎧 Ready! Speak now...")

            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                st.write("🔄 Processing audio...")

                # Transcription avec Google Speech Recognition
                text = recognizer.recognize_google(audio, language="en-EN")
                st.write(f"📝 **You said:** {text}")
                return text

            except sr.UnknownValueError:
                st.error("🤷 Sorry, I couldn't understand the audio.")
                return None
            except sr.RequestError as e:
                st.error(f"🌐 API error: {e}")
                return None
# ---------------- STYLE ----------------
st.markdown(
    """
    <style>
    .stButton>button {
        display: flex;
        margin: 0 auto;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------- INTERFACE ----------------
st.markdown("<h1 style='text-align: center;'>🔬 Medical Chatbot & QCM </h1>", unsafe_allow_html=True)

tab_about, tab_chat, tab_QCM, tab_feedback = st.tabs(["🏥 About", "💬 Chatbot", "📚 QCM", "📢 Feedback"])

# ---------------- ABOUT ----------------
with tab_about:
    st.header("🏥 About the Medical Chatbot & QCM")
    st.markdown("""
        This tool helps users:
        - ✅ **Ask medical-related questions** and receive AI-generated answers.  
        - ✅ **Test their knowledge** with multiple-choice quizzes (QCM).  
        - ✅ **Download QCMs as PDFs** for offline practice.  
    """)

# ---------------- CHATBOT ----------------
with tab_chat:
    st.header("💬 Chat with AI")
    st.write("Ask a medical question and receive AI-generated responses.")

    if "history" not in st.session_state:
        st.session_state.history = []

    # ---------------- Affichage de l'historique des messages ----------------
    for chat in st.session_state.history:
        with st.chat_message("user"):
            st.write(chat["question"])
        with st.chat_message("assistant"):
            st.write(chat["response"])

            # Expander pour afficher les détails (Source, Focus Area, Similarity Score)
            with st.expander("📄 Details"):
                st.write(f"**Source:** {chat.get('source', 'Unknown')}")
                st.write(f"**Focus Area:** {chat.get('focus_area', 'N/A')}")
                st.write(f"**Similarity Score:** {chat.get('similarity', 'N/A')}")

            # Expander pour afficher les métriques (si disponibles)
            metrics = chat.get("metrics", {})
            if metrics:
                with st.expander("📊 View Metrics"):
                    st.json(metrics)  # Affichage propre des métriques JSON

    # ---------------- Choix entre Écrit et Audio ----------------
    mode = st.radio("🔄 Choose input mode:", ["📝 Text", "🎤 Voice"], horizontal=True)

    # ---------------- Mode Écrit ----------------
    if mode == "📝 Text":
        question = st.chat_input("Type your message...")
        if question:
            try:
                response = requests.post(API_ANSWER_URL, json={"question": question}, timeout=500)
                if response.status_code == 200:
                    data = response.json()
                    chatbot_response = data.get("answer")

                    # Récupération des autres informations
                    chatbot_source = data.get("source")
                    chatbot_focus_area = data.get("focus_area")
                    chatbot_similarity = data.get("similarity")
                    chatbot_metrics = data.get("metrics")

                else:
                    chatbot_response = "⚠️ Error retrieving the answer."
                    chatbot_source, chatbot_focus_area, chatbot_similarity, chatbot_metrics = "Unknown", "N/A", "N/A", {}

                # Ajout à l'historique avec tous les détails
                st.session_state.history.append({
                    "question": question,
                    "response": chatbot_response,
                    "source": chatbot_source,
                    "focus_area": chatbot_focus_area,
                    "similarity": chatbot_similarity,
                    "metrics": chatbot_metrics,
                })
                st.rerun()  # Recharge la page pour afficher le message
            except requests.exceptions.RequestException as e:
                st.error(f"🚨 API request failed: {e}")

    # ---------------- Mode Audio ----------------
    elif mode == "🎤 Voice":
        if st.button("🎤 Start Recording"):
            spoken_text = listen_and_transcribe()
            if spoken_text:
                try:
                    response = requests.post(API_ANSWER_URL, json={"question": spoken_text}, timeout=500)
                    if response.status_code == 200:
                        data = response.json()
                        chatbot_response = data.get("answer", "No answer available.")

                        # Récupération des autres informations
                        chatbot_source = data.get("source", "Unknown")
                        chatbot_focus_area = data.get("focus_area", "N/A")
                        chatbot_similarity = data.get("similarity", "N/A")
                        chatbot_metrics = data.get("metrics", {})

                    else:
                        chatbot_response = "⚠️ Error retrieving the answer."
                        chatbot_source, chatbot_focus_area, chatbot_similarity, chatbot_metrics = "Unknown", "N/A", "N/A", {}

                    # Ajouter au chat avec les détails
                    st.session_state.history.append({
                        "question": spoken_text,
                        "response": chatbot_response,
                        "source": chatbot_source,
                        "focus_area": chatbot_focus_area,
                        "similarity": chatbot_similarity,
                        "metrics": chatbot_metrics,
                    })
                    st.rerun()  # Recharge la page pour afficher le message
                except requests.exceptions.RequestException as e:
                    st.error(f"🚨 API request failed: {e}")

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
    general_score = st.slider("Rate the overall experience:", 1, 5, 3)
    general_comment = st.text_area("Any suggestions to improve the application?")
    
    if st.button("Submit General Feedback"):
        df = pd.DataFrame([[general_score, general_comment]], columns=["score", "comment"])
        if is_feedback_file_empty(GENERAL_FEEDBACK_FILE):
            df.to_csv(GENERAL_FEEDBACK_FILE, mode='w', header=True, index=False)
        else:
            df.to_csv(GENERAL_FEEDBACK_FILE, mode='a', header=False, index=False)
        st.success("✅ Thank you for your feedback!")
