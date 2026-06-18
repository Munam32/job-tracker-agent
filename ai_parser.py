"""
ai_parser.py — Parse job descriptions using Google Gemini (free tier)
Extracts: title, location, salary, required skills, and a short summary.
"""

import json
from typing import Optional

from google import genai
from config import GEMINI_API_KEY, GEMINI_MODEL


SYSTEM_PROMPT = """You are a job description parser.
Extract structured information from the job description the user provides.

Respond ONLY with a valid JSON object — no markdown, no explanation — in this exact shape:
{
  "title": "Job title",
  "location": "City / Remote / Hybrid",
  "salary": "Salary range or empty string",
  "skills": ["skill1", "skill2", ...],
  "summary": "2-sentence plain-English summary of the role"
}

Rules:
- skills: list of concrete technical or domain skills only (e.g. Python, React, SQL, AWS). Max 10.
- salary: include currency if mentioned. Empty string if not stated.
- title: use the exact title from the posting.
- summary: be concise and factual, 1-2 sentences max.
"""


STATUS_PARSER_PROMPT = """You are an email analyzer for job applications.
Analyze the email content and extract job application status information.

Respond ONLY with a valid JSON object — no markdown, no explanation — in this exact shape:
{
  "company": "Company name",
  "role": "Job role/title",
  "status": "One of: Applied, Under Review, Interview Scheduled, Interview Completed, Offer Received, Rejected, Withdrawn",
  "confidence": 0.0-1.0,
  "notes": "Any relevant details"
}

If this is NOT a job application related email, return null.
"""


class AIParser:
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is not set. "
                "Add it to your environment or config.py. "
                "Get a free API key from https://aistudio.google.com/"
            )
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model_name = GEMINI_MODEL

    def _generate(self, prompt: str) -> Optional[str]:
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            return response.text.strip() if response.text else None
        except Exception as e:
            print(f"Gemini API error: {e}")
            return None

    def _parse_json_response(self, raw: str) -> Optional[dict]:
        if not raw:
            return None
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        if raw.lower() == "null":
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    def parse_jd(self, jd_text: str) -> Optional[dict]:
        """
        Parse a raw job description string.
        Returns a dict with keys: title, location, salary, skills, summary.
        Returns None on failure.
        """
        if not jd_text or not jd_text.strip():
            return None

        prompt = f"{SYSTEM_PROMPT}\n\nJob Description:\n{jd_text[:8000]}"
        raw = self._generate(prompt)
        return self._parse_json_response(raw)

    def parse_with_ai(self, prompt: str) -> Optional[dict]:
        """
        Generic method to parse any prompt with AI and return JSON.
        Used for email status parsing.
        """
        raw = self._generate(prompt)
        return self._parse_json_response(raw)

    def assess_fit(self, jd_text: str, resume_summary: str) -> str:
        """
        Optional: given a JD and a brief resume summary,
        return a short AI-generated assessment of fit.
        """
        prompt = (
            f"Job description:\n{jd_text[:4000]}\n\n"
            f"Candidate summary:\n{resume_summary}\n\n"
            "In 3-4 sentences, assess how well this candidate fits the role. "
            "Be direct and specific."
        )
        raw = self._generate(prompt)
        if raw is None:
            return "Error assessing fit"
        return raw
