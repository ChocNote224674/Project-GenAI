"""
This module defines a Streamlit-based chatbot and QCM application,
including functionalities for text-to-speech, speech recognition,
and user feedback collection.
"""

import os
from io import BytesIO
import requests
import pandas as pd
import pyttsx3
import streamlit as st
import speech_recognition as sr
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from utils import is_feedback_file_empty

# ---------------- CONFIGURATION ----------------
API_ANSWER_URL = "http://127.0.0.1:8000/answer"
API_QCM_URL = "http://127.0.0.1:8000/qcm"
GENERAL_FEEDBACK_FILE = "feedback.csv"


def listen_and_transcribe():
    """Records and transcribes user speech input."""
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    with microphone as source:
        st.write("🎤 Adjusting for ambient noise...")
        recognizer.adjust_for_ambient_noise(source)
        st.write("🎧 Ready! Speak now...")
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            st.write("🔄 Processing audio...")
            text = recognizer.recognize_google(audio, language="en-EN")
            st.write(f"📝 **You said:** {text}")
            return text
        except sr.UnknownValueError:
            st.error("🤷 Sorry, I couldn't understand the audio.")
        except sr.RequestError as error:
            st.error(f"🌐 API error: {error}")
    return None


def text_to_speech(text: str):
    """Converts text to speech and plays the output."""
    engine = pyttsx3.init()
    engine.say(text[:1000])  # Limit speech to 200 characters
    engine.runAndWait()


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
st.markdown(
    "<h1 style='text-align: center;'>🔬 Medical Chatbot & QCM </h1>",
    unsafe_allow_html=True)

tab_about, tab_chat, tab_QCM, tab_feedback = st.tabs(
    ["🏥 About", "💬 Chatbot", "📚 QCM", "📢 Feedback"])

# ---------------- ABOUT ----------------
with tab_about:
    st.header("🏥 About the Medical Chatbot & QCM")
    st.markdown("""
        Welcome to our **Medical Chatbot & QCM** platform! This tool is designed to assist you in two key ways:

        - 🤖 **Ask medical-related questions** and receive AI-powered responses to enhance your knowledge.
        - 📝 **Test yourself** with interactive multiple-choice quizzes (QCM) to reinforce your learning.

        We also value your feedback! 💬 Your ratings and comments help us improve the chatbot and the QCM experience.
        Visit the **User Feedback** section to share your thoughts and check the overall satisfaction scores.
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

            # Expander pour afficher les détails (Source, Focus Area,
            # Similarity Score)
            with st.expander("📝 Details"):
                st.write(f"**Source:** {chat.get('source', 'Unknown')}")
                st.write(f"**Focus Area:** {chat.get('focus_area', 'N/A')}")
                st.write(
                    f"**Similarity Score:** {chat.get('similarity', 'N/A')}")

            # Expander pour afficher les métriques (si disponibles)
            metrics = chat.get("metrics", {})
            if metrics:
                with st.expander("📊 View Metrics"):
                    st.json(metrics)  # Affichage propre des métriques JSON

            # Bouton pour lire la réponse à haute voix
            if st.button(f"🎤 Listen to response {chat['question'][:10]}..."):
                st.write("Playing audio...")
                # Fonction pour lire la réponse
                text_to_speech(chat["response"])

    # ---------------- Choix entre Écrit et Audio ----------------
    mode = st.radio(
        "🔄 Choose input mode:", [
            "📝 Text", "🎤 Voice"], horizontal=True)

    # ---------------- Mode Écrit ----------------
    if mode == "📝 Text":
        question = st.chat_input("Type your message...")
        if question:
            try:
                response = requests.post(
                    API_ANSWER_URL, json={
                        "question": question}, timeout=500)
                if response.status_code == 200:
                    data = response.json()
                    CHAT_BOT_RESPONSE = data.get("answer")

                    # Récupération des autres informations
                    chatbot_source = data.get("source")
                    chatbot_focus_area = data.get("focus_area")
                    chatbot_similarity = data.get("similarity")
                    chatbot_metrics = data.get("metrics")

                else:
                    CHAT_BOT_RESPONSE = "⚠️ Error retrieving the answer."
                    chatbot_source, chatbot_focus_area, chatbot_similarity, chatbot_metrics = "Unknown", "N/A", "N/A", {}

                # Ajout à l'historique avec tous les détails
                st.session_state.history.append({
                    "question": question,
                    "response": CHAT_BOT_RESPONSE,
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
                    response = requests.post(
                        API_ANSWER_URL, json={
                            "question": spoken_text}, timeout=500)
                    if response.status_code == 200:
                        data = response.json()
                        chatbot_response = data.get(
                            "answer", "No answer available.")

                        # Récupération des autres informations
                        chatbot_source = data.get("source", "Unknown")
                        chatbot_focus_area = data.get("focus_area", "N/A")
                        chatbot_similarity = data.get("similarity", "N/A")
                        chatbot_metrics = data.get("metrics", {})

                    else:
                        CHAT_BOT_RESPONSE = "⚠️ Error retrieving the answer."
                        chatbot_source, chatbot_focus_area, chatbot_similarity, chatbot_metrics = "Unknown", "N/A", "N/A", {}

                    # Ajouter au chat avec les détails
                    st.session_state.history.append({
                        "question": spoken_text,
                        "response": CHAT_BOT_RESPONSE,
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

    # Récupérer les focus_area disponibles depuis l'API
    response = requests.get(API_QCM_URL + "/themes", timeout=500)
    if response.status_code == 200:
        available_themes = response.json().get("themes", [])
    else:
        available_themes = []

    # Choix du thème
    selected_theme = st.selectbox("Choose a topic:", available_themes)

    if "qcm_questions" not in st.session_state:
        st.session_state.qcm_questions = []

    if st.button("Generate QCM") and selected_theme:
        response = requests.get(
            API_QCM_URL,
            params={
                "n": 5,
                "focus_area": selected_theme},
            timeout=500)
        if response.status_code == 200:
            st.session_state.qcm_questions = response.json().get("questions", [])
            st.success(
                f"✅ QCM Generated for {selected_theme}! You can now take the test or download it.")
        else:
            st.error("⚠️ Failed to fetch QCM questions.")

    # Affichage des questions et téléchargement
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
            c.drawString(
                50, Y_POSITION, f"✅ Correct Answer: {
                    q['correct_answer']}")
            Y_POSITION -= 30

        c.save()
        pdf_content.seek(0)

        st.download_button(
            label="📥 Download QCM as PDF",
            data=pdf_content,
            file_name="QCM.pdf",
            mime="application/pdf"
        )

    # Soumission des réponses utilisateur
    if st.session_state.qcm_questions:
        user_answers = {}
        for idx, q in enumerate(st.session_state.qcm_questions):
            st.subheader(f"Q{idx + 1}: {q['question']}")
            user_answers[q["question"]] = st.radio(
                "Select your answer:",
                q["options"],
                key=f"qcm_{idx}"
            )

        if st.button("Submit Answers"):
            score = sum(
                1 for q in st.session_state.qcm_questions if user_answers[q["question"]] == q["correct_answer"])
            st.success(
                f"✅ You scored {score} / {len(st.session_state.qcm_questions)}!")
            for q in st.session_state.qcm_questions:
                if user_answers[q["question"]] != q["correct_answer"]:
                    st.warning(f"❌ Incorrect: {q['question']}")
                    st.info(f"✔️ Correct Answer: {q['correct_answer']}")

# ---------------- FEEDBACK ----------------
with tab_feedback:
    st.header("📢 User Feedback")
    general_score = st.slider("Rate the overall experience:", 1, 5, 3)
    general_comment = st.text_area(
        "Any suggestions to improve the application?")

    if st.button("Submit General Feedback"):
        df = pd.DataFrame([[general_score, general_comment]],
                          columns=["score", "comment"])
        if is_feedback_file_empty(GENERAL_FEEDBACK_FILE):
            df.to_csv(
                GENERAL_FEEDBACK_FILE,
                mode='w',
                header=True,
                index=False)
        else:
            df.to_csv(
                GENERAL_FEEDBACK_FILE,
                mode='a',
                header=False,
                index=False)
        st.success("✅ Thank you for your feedback!")

    # Charger les feedbacks existants
    if os.path.exists(GENERAL_FEEDBACK_FILE):
        df_feedback = pd.read_csv(GENERAL_FEEDBACK_FILE)
    else:
        df_feedback = pd.DataFrame(columns=["score", "comment"])

    if not df_feedback.empty:
        # Compter le nombre d'occurrences de chaque score
        score_counts = df_feedback["score"].value_counts().sort_index()

        # Calcul de la moyenne générale des feedbacks
        mean_general = df_feedback["score"].mean()

        # Affichage du graphique
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(score_counts.index, score_counts.values, color="skyblue")
        ax.set_xlabel("Score")
        ax.set_ylabel("Nombre d'occurrences")
        ax.set_title("Fréquence des Scores")
        ax.set_xticks(range(1, 6))
        ax.grid(axis="y", linestyle="--", alpha=0.7)

        st.pyplot(fig)

        # Affichage du message
        st.write(
            f"### La moyenne générale des feedbacks est de {
                mean_general:.2f}.")
    else:
        st.write("### Aucun feedback enregistré pour le moment.")
