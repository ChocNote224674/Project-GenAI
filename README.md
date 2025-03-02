# 🚀 Project-GenAI: Medical Q&A Chatbot

## 📌 Description

**Project-GenAI** is an AI-powered chatbot designed to answer medical-related queries for medical students. It leverages **Retrieval-Augmented Generation (RAG)** to fetch information from medical databases and generate context-aware responses. The application is hosted on **Google Cloud Platform (GCP)** and utilizes cloud storage and computing services for optimal performance.

Additionally, the chatbot supports **speech recognition**, allowing users to input queries using voice commands, enhancing accessibility and user experience.

## 📂 Project Structure

```plaintext
Project-GenAI/
│── tools/
│ │── utils.py                     # Utility functions
│ │── retrieve.py                 # Search engine for medical data retrieval
│ │── config.py                   # API key configurations
│ │── agents.py                  # Manages chatbot agents
│── database_init/
│ │── database.py                 # Cloud SQL database management
│ │── generate_embeddings.py      # Embedding generation for document retrieval
│ │── medquad.csv                 # Medical dataset in CSV format
│ │── medquad_utf8.csv            # UTF-8 version of the medical dataset
│── eval/
│ │── eval.py                     # Model performance evaluation
│ │── feedback.csv                # User feedback data
│── api.py                     # Streamlit API for chatbot access
│── app.py                     # Main entry point of the application
│── requirements.txt            # Project dependencies
└── README.md                   # Project documentation
```

## 🎯 Features

- 🔎 **Accurate medical responses** using a RAG-based system.
- 🏥 **Generation of interactive multiple-choice quizzes (MCQs)** for learning.
- 🔄 **Feedback system** to improve response accuracy.
- 🎙️ **Speech Recognition** for voice-based question input.
- ☁️ **Deployed on Google Cloud Platform (GCP)**.

## 🏗️ Architecture

- **Data Storage:** Medical datasets are downloaded from Kaggle and stored in **Cloud SQL**.
- **Processing:** RAG-based model with embeddings generated using **Hugging Face**.
- **Backend:**  API for handling user queries.
- **Language Model:** **Gemini LLM** for medical question answering.
- **Evaluation Metrics:** Cosine Similarity, Jaccard Similarity, BERTScore, METEOR.

## 🔧 Installation & Deployment

### 1️⃣ Prerequisites

- Python 3.8+
- Google Cloud account with access to Cloud SQL
- Gemini API Key
### 2️⃣ Install Dependencies

```bash
git clone https://github.com/ChocNote224674/Project-GenAI.git
cd Project-GenAI
pip install -r requirements.txt
```
### 3️⃣ Run the API

```bash
python app.py
```
The API will be accessible at **http://localhost:5000**.

## 📊 Model Optimization

- **Fine-tuning** on domain-specific data (medical textbooks and verified MCQ datasets).
- **Conditional Adaptive Generation (CAG):** Improves response fluency and relevance by dynamically adjusting the model’s retrieval strategy based on user intent.

---




