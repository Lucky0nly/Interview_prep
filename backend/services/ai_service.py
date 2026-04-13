import json
import os
from typing import Any

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - handled with mock fallback
    OpenAI = None


ROLE_KEYWORDS = {
    "Software Engineer": {"scalability", "testing", "api", "database", "performance", "architecture", "tradeoff"},
    "Data Scientist": {"model", "feature", "metric", "validation", "bias", "dataset", "experiment"},
    "Web Developer": {"accessibility", "performance", "responsive", "javascript", "html", "css", "security"},
}


def evaluate_interview(role: str, difficulty: str, questions: list[str], answers: list[str]) -> dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and OpenAI is not None:
        try:
            return _evaluate_with_openai(api_key, role, difficulty, questions, answers)
        except Exception:
            return _evaluate_with_mock(role, difficulty, questions, answers)
    return _evaluate_with_mock(role, difficulty, questions, answers)


def _evaluate_with_openai(api_key: str, role: str, difficulty: str, questions: list[str], answers: list[str]) -> dict[str, Any]:
    client = OpenAI(api_key=api_key)
    prompt = {
        "role": role,
        "difficulty": difficulty,
        "instructions": [
            "Evaluate each answer on a 0-10 scale.",
            "Be fair, concise, and practical.",
            "Return strict JSON only.",
            "Each item should include strengths, weaknesses, and suggestions.",
            "Provide an overall summary with strengths, weaknesses, and next steps.",
        ],
        "responses": [{"question": question, "answer": answer} for question, answer in zip(questions, answers)],
        "output_schema": {
            "questions": [
                {
                    "score": "number between 0 and 10",
                    "strengths": ["string"],
                    "weaknesses": ["string"],
                    "suggestions": ["string"],
                }
            ],
            "overall": {
                "summary": "string",
                "strengths": ["string"],
                "weaknesses": ["string"],
                "suggestions": ["string"],
            },
        },
    }

    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert technical interviewer. Always return valid JSON without markdown fences "
                    "or extra narration."
                ),
            },
            {"role": "user", "content": json.dumps(prompt)},
        ],
    )
    content = response.choices[0].message.content or "{}"
    parsed = _load_json(content)
    return _normalize_evaluation(role, difficulty, questions, answers, parsed)


def _evaluate_with_mock(role: str, difficulty: str, questions: list[str], answers: list[str]) -> dict[str, Any]:
    role_keywords = ROLE_KEYWORDS.get(role, set())
    question_results = []
    total_score = 0.0
    strengths_seen: list[str] = []
    weaknesses_seen: list[str] = []
    suggestions_seen: list[str] = []

    for question, answer in zip(questions, answers):
        clean_answer = answer.strip()
        word_count = len(clean_answer.split())
        keyword_hits = sum(1 for keyword in role_keywords if keyword in clean_answer.lower())
        structure_hits = sum(
            1 for marker in ["because", "for example", "for instance", "tradeoff", "first", "then", "finally"] if marker in clean_answer.lower()
        )

        if not clean_answer:
            score = 0.0
        else:
            score = min(10.0, round((word_count / 22) + (keyword_hits * 1.2) + (structure_hits * 0.6), 1))
            if difficulty == "Hard" and word_count > 90:
                score = min(10.0, round(score + 0.8, 1))
            elif difficulty == "Easy" and word_count > 35:
                score = min(10.0, round(score + 0.4, 1))

        strengths = []
        weaknesses = []
        suggestions = []

        if clean_answer:
            strengths.append("Provides a direct response instead of avoiding the question.")
        if word_count >= 40:
            strengths.append("Includes enough detail to show reasoning rather than a one-line answer.")
        if keyword_hits >= 2:
            strengths.append("Uses role-relevant technical concepts that fit the question.")
        if structure_hits >= 2:
            strengths.append("Shows a structured explanation with cause, example, or sequencing.")

        if word_count < 20:
            weaknesses.append("Needs more depth and supporting detail.")
        if keyword_hits == 0 and clean_answer:
            weaknesses.append("Could connect the answer more clearly to role-specific concepts.")
        if structure_hits == 0 and clean_answer:
            weaknesses.append("Would be stronger with an example, tradeoff, or step-by-step structure.")
        if not clean_answer:
            weaknesses.append("No answer was provided.")

        if word_count < 40:
            suggestions.append("Add a concrete example, metric, or implementation detail.")
        if "tradeoff" not in clean_answer.lower() and difficulty in {"Medium", "Hard"}:
            suggestions.append("Mention tradeoffs, constraints, or alternative approaches.")
        if keyword_hits < 2:
            suggestions.append(f"Use {role.lower()} terminology to show role alignment.")
        if difficulty == "Hard":
            suggestions.append("Discuss scale, reliability, risk, or stakeholder impact to sound senior-level.")

        question_results.append(
            {
                "question": question,
                "answer": clean_answer,
                "score": score,
                "strengths": _deduplicate(strengths)[:3],
                "weaknesses": _deduplicate(weaknesses)[:3],
                "suggestions": _deduplicate(suggestions)[:3],
            }
        )
        total_score += score
        strengths_seen.extend(question_results[-1]["strengths"])
        weaknesses_seen.extend(question_results[-1]["weaknesses"])
        suggestions_seen.extend(question_results[-1]["suggestions"])

    average_score = round(total_score / len(question_results), 2) if question_results else 0.0
    summary = (
        "Strong effort overall with useful foundations, but there is room to sharpen depth, examples, and technical precision."
        if average_score >= 6
        else "The answers show promising intent, and the biggest opportunity is adding clearer structure, detail, and role-specific depth."
    )

    normalized = {
        "questions": question_results,
        "overall": {
            "summary": summary,
            "strengths": _deduplicate(strengths_seen)[:5],
            "weaknesses": _deduplicate(weaknesses_seen)[:5],
            "suggestions": _deduplicate(suggestions_seen)[:5],
        },
    }
    return _normalize_evaluation(role, difficulty, questions, answers, normalized)


def _normalize_evaluation(
    role: str,
    difficulty: str,
    questions: list[str],
    answers: list[str],
    evaluation_payload: dict[str, Any],
) -> dict[str, Any]:
    raw_questions = evaluation_payload.get("questions", [])
    normalized_breakdown = []
    per_question_scores: list[float] = []

    for index, question in enumerate(questions):
        raw_item = raw_questions[index] if index < len(raw_questions) else {}
        score = max(0.0, min(10.0, float(raw_item.get("score", 0.0))))
        normalized_item = {
            "question": question,
            "answer": answers[index].strip(),
            "score": round(score, 1),
            "strengths": _normalize_list(raw_item.get("strengths"), "Clear intent was shown in the answer."),
            "weaknesses": _normalize_list(raw_item.get("weaknesses"), "More specificity would improve the answer."),
            "suggestions": _normalize_list(raw_item.get("suggestions"), "Add a concrete example or tradeoff next time."),
        }
        normalized_breakdown.append(normalized_item)
        per_question_scores.append(normalized_item["score"])

    total_score = round(sum(per_question_scores), 2)
    average_score = round(total_score / len(per_question_scores), 2) if per_question_scores else 0.0
    overall = evaluation_payload.get("overall", {})

    return {
        "scores": {
            "role": role,
            "difficulty": difficulty,
            "total": total_score,
            "average": average_score,
            "max_total": len(per_question_scores) * 10,
            "per_question": per_question_scores,
        },
        "feedback": {
            "summary": overall.get("summary", "Interview review completed."),
            "strengths": _normalize_list(overall.get("strengths"), "You answered with a consistent baseline across the interview."),
            "weaknesses": _normalize_list(overall.get("weaknesses"), "Several answers would benefit from deeper technical detail."),
            "suggestions": _normalize_list(overall.get("suggestions"), "Practice answering with examples, structure, and tradeoffs."),
            "breakdown": normalized_breakdown,
        },
    }


def _load_json(content: str) -> dict[str, Any]:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json", "", 1).strip()
    return json.loads(cleaned)


def _normalize_list(value: Any, fallback: str) -> list[str]:
    if isinstance(value, list):
        normalized = [str(item).strip() for item in value if str(item).strip()]
        if normalized:
            return _deduplicate(normalized)[:5]
    return [fallback]


def _deduplicate(items: list[str]) -> list[str]:
    seen = set()
    output = []
    for item in items:
        if item not in seen:
            seen.add(item)
            output.append(item)
    return output
