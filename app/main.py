import os
from pathlib import Path
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_AI_BASE_URL = "https://api.openai.com/v1"

app = FastAPI(title="EduGenie", description="A focused assistant for learning.")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


class StudyRequest(BaseModel):
    action: Literal["ask", "simplify", "quiz", "path", "summarize"]
    content: str = Field(min_length=1, max_length=12000)
    level: Literal["beginner", "intermediate", "advanced"] = "beginner"

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, content: str) -> str:
        if not content.strip():
            raise ValueError("Add a topic or passage first.")
        return content.strip()


class StudyResponse(BaseModel):
    answer: str
    mode: Literal["ai", "demo"]


ACTION_INSTRUCTIONS = {
    "ask": "Answer the learner's question accurately and concisely. Explain unfamiliar terms briefly.",
    "simplify": "Explain the supplied topic in plain language for the learner's level. Use a concrete analogy when useful.",
    "quiz": "Create a short quiz of 5 questions about the supplied topic. Include multiple choice options, then an answer key with brief explanations at the end.",
    "path": "Create a structured learning path for the supplied subject, progressing from beginner to advanced. Include topics, a realistic timeline, practice tasks, and suggestions for what to learn next.",
    "summarize": "Summarize the supplied passage for the learner's level. Keep the key facts, remove repetition, and do not add claims absent from the text.",
}


def demo_answer(request: StudyRequest) -> str:
    topic = request.content.strip().rstrip("?.!")
    normalized = topic.lower()

    if request.action == "ask":
        if "largest ocean" in normalized or "biggest ocean" in normalized:
            return "The Pacific Ocean is the largest ocean on Earth. It covers more area than all of Earth's land combined."
        return (
            f"I can help you explore {topic}. Demo mode has no language model connected, so it cannot reliably answer "
            "open-ended questions yet. Add an AI model in the environment settings to get a tailored explanation."
        )

    if request.action == "simplify":
        return (
            f"Let's make {topic} easier to approach. Start by identifying its main idea, then connect each new term "
            "to something you already know. Demo mode cannot interpret this topic in depth; connect an AI model for a "
            "topic-specific explanation."
        )

    if request.action == "quiz":
        if "pythag" in normalized:
            return (
                "1. A right triangle has legs of 3 cm and 4 cm. What is the hypotenuse?\n"
                "   A) 5 cm  B) 7 cm  C) 12 cm\n\n"
                "2. Which equation is the Pythagorean theorem?\n"
                "   A) a + b = c  B) a^2 + b^2 = c^2  C) a x b = c\n\n"
                "3. A right triangle has a hypotenuse of 13 and one leg of 5. Find the other leg.\n"
                "   A) 8  B) 12  C) 18\n\n"
                "Answer key: 1) A, since 3^2 + 4^2 = 5^2. 2) B. 3) B, since 5^2 + 12^2 = 13^2."
            )
        return (
            f"Quick check for {topic}:\n"
            "1. What is the central idea, and how would you explain it in one sentence?\n"
            "2. Which key term or step is most important to understand?\n"
            "3. Can you give a real-world example or solve a basic problem using it?\n\n"
            "Demo mode cannot verify answers or generate topic-specific distractors. Connect an AI model for a full quiz."
        )

    if request.action == "path":
        return (
            f"Learning path: {topic}\n\n"
            "1. Foundations (weeks 1-2): learn core terms and the basic purpose of the subject. Make a one-page glossary.\n"
            "2. Core skills (weeks 3-4): work through beginner examples and practice one small exercise each day.\n"
            "3. Applied practice (weeks 5-6): build a small project that combines the concepts you've learned.\n"
            "4. Advanced study (weeks 7-8): explore optimization, edge cases, and a real-world case study.\n\n"
            "Suggestion: keep a learning log and revisit topics you find difficult. This is a general template; connect an AI model for a tailored plan."
        )

    sentences = [part.strip() for part in request.content.replace("\n", " ").split(".") if part.strip()]
    if len(sentences) <= 2:
        return (
            "Your passage is already short. Identify its main claim and one supporting detail. "
            "Connect an AI model for a faithful, passage-specific summary."
        )
    return (
        "Key points from your passage:\n"
        + "\n".join(f"- {sentence}." for sentence in sentences[:3])
        + "\n\nDemo mode extracts the opening sentences only; connect an AI model for an accurate summary."
    )


async def generate_with_model(request: StudyRequest) -> str:
    api_key = os.getenv("AI_API_KEY", "")
    base_url = os.getenv("AI_BASE_URL", DEFAULT_AI_BASE_URL).rstrip("/")
    model = os.getenv("AI_MODEL", "gpt-4o-mini")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are EduGenie, a careful educational assistant. Be clear, concise, age-appropriate, "
                    "and honest about uncertainty. "
                    + ACTION_INSTRUCTIONS[request.action]
                ),
            },
            {
                "role": "user",
                "content": f"Learner level: {request.level}\n\nTopic or passage:\n{request.content}",
            },
        ],
        "temperature": 0.5,
    }
    try:
        async with httpx.AsyncClient(timeout=40) as client:
            response = await client.post(
                f"{base_url}/chat/completions", headers=headers, json=payload
            )
            response.raise_for_status()
            answer = response.json()["choices"][0]["message"]["content"]
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as error:
        raise HTTPException(
            status_code=502,
            detail="The configured AI model could not complete this request. Check the model settings and try again.",
        ) from error

    if not isinstance(answer, str) or not answer.strip():
        raise HTTPException(status_code=502, detail="The configured AI model returned an empty answer.")
    return answer.strip()


@app.get("/")
async def home() -> FileResponse:
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/api/status")
async def status() -> dict[str, str]:
    configured = bool(os.getenv("AI_API_KEY") or os.getenv("AI_BASE_URL"))
    return {"mode": "ai" if configured else "demo"}


@app.post("/api/study", response_model=StudyResponse)
async def study(request: StudyRequest) -> StudyResponse:
    configured = bool(os.getenv("AI_API_KEY") or os.getenv("AI_BASE_URL"))
    if configured:
        answer = await generate_with_model(request)
        return StudyResponse(answer=answer, mode="ai")
    return StudyResponse(answer=demo_answer(request), mode="demo")