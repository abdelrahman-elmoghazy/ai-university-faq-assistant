"""
AI Service — Team Member 5
Supports OpenRouter API, Ollama local model, and mock fallback.
All API keys remain server-side; never exposed to the frontend.
"""
import os
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────
AI_PROVIDER = os.getenv("AI_PROVIDER", "mock")            # "openrouter" | "ollama" | "mock"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-3.5-turbo")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

SYSTEM_PROMPT = """You are the AI University FAQ Assistant. 
You answer university-related questions accurately and helpfully.
Use the provided context from university documents when available.
If you don't know the answer, say so honestly.
Keep responses concise, professional, and relevant to university topics."""


class AIService:
    """Handles AI answer generation with provider fallback chain."""

    @staticmethod
    def generate_answer(question: str, context_chunks: list = None) -> str:
        """
        Generate an AI answer for the given question.
        Uses context chunks from the vector store if available.
        Falls back through providers: configured → mock.
        """
        # Build the prompt with optional RAG context
        prompt = AIService._build_prompt(question, context_chunks)

        provider = AI_PROVIDER.lower()

        try:
            if provider == "openrouter" and OPENROUTER_API_KEY:
                return AIService._call_openrouter(prompt)
            elif provider == "ollama":
                return AIService._call_ollama(prompt)
            else:
                return AIService._mock_response(question)
        except Exception as e:
            logger.error(f"AI provider '{provider}' failed: {e}")
            # Fallback to mock on any failure
            return AIService._mock_response(question)

    # ── Private helpers ──────────────────────────────────────

    @staticmethod
    def _build_prompt(question: str, context_chunks: list = None) -> str:
        """Build a RAG-style prompt with optional document context."""
        context_text = ""
        if context_chunks:
            context_text = "\n\n--- Relevant Documents ---\n"
            for i, chunk in enumerate(context_chunks, 1):
                context_text += f"\n[Document {i}]:\n{chunk}\n"
            context_text += "\n--- End of Documents ---\n"

        return f"{context_text}\nUser Question: {question}"

    @staticmethod
    def _call_openrouter(prompt: str) -> str:
        """Call OpenRouter API (OpenAI-compatible)."""
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "AI University FAQ Assistant"
        }
        payload = {
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1024,
            "temperature": 0.7
        }

        resp = requests.post(OPENROUTER_BASE_URL, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()

    @staticmethod
    def _call_ollama(prompt: str) -> str:
        """Call Ollama local model."""
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "stream": False
        }
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=60
        )
        resp.raise_for_status()
        data = resp.json()
        return data["message"]["content"].strip()

    @staticmethod
    def _mock_response(question: str) -> str:
        """
        Intelligent mock response for demo / no-API-key scenarios.
        Returns contextually relevant placeholder answers.
        """
        q = question.lower()

        mock_answers = {
            "admission": "University admissions typically open in March for fall semester. "
                         "Requirements include a completed application form, transcripts, "
                         "and standardized test scores. Visit the admissions portal for details.",
            "tuition": "Tuition fees vary by program. Undergraduate programs start at approximately "
                       "$5,000 per semester. Financial aid and scholarships are available. "
                       "Contact the financial aid office for personalized information.",
            "registration": "Course registration opens two weeks before each semester. "
                            "Log in to the student portal, select your courses, and confirm "
                            "your schedule. Priority registration is available for seniors.",
            "library": "The university library is open Mon–Fri 8 AM – 10 PM and Sat–Sun 10 AM – 6 PM. "
                       "Digital resources are accessible 24/7 through the library portal.",
            "exam": "Final exams are scheduled during the last two weeks of each semester. "
                    "The exam schedule is published on the registrar's website four weeks before finals.",
            "scholarship": "Multiple scholarship opportunities are available based on academic merit, "
                           "financial need, and extracurricular achievements. Applications open each January.",
            "graduation": "Graduation requirements include completing all required credits, "
                          "maintaining the minimum GPA, and fulfilling any capstone or thesis requirements.",
        }

        for keyword, answer in mock_answers.items():
            if keyword in q:
                return answer

        return (
            f"Thank you for your question about: \"{question}\"\n\n"
            "Based on our university knowledge base, here is what I found:\n\n"
            "This is a demonstration response from the AI FAQ Assistant. "
            "In production, this would be powered by OpenRouter or Ollama with "
            "RAG (Retrieval Augmented Generation) using your uploaded university documents.\n\n"
            "For accurate information, please configure an AI provider in the environment settings "
            "or contact the university administration directly."
        )
