from ..config import EVAL_MODEL
from ..llm import generate
from ..models import Evaluation, Question
import re

CRITERIA = ["relevance", "technical_accuracy", "communication", "jd_alignment"]
FIRST_PERSON = re.compile(r"\b(i|my|we|our|me)\b", re.I)
HYPOTHETICAL = re.compile(r"\b(i would|i'd|i will|we would|you should|you can)\b", re.I)

EVAL_SYSTEM = (
    "You are a strict, fair technical interviewer scoring one answer. Score each "
    "criterion from 1 to 5: "
    "1 = no answer, off-topic or wrong; 2 = mostly vague or partly wrong; "
    "3 = acceptable but generic, no specifics; 4 = good, specific and correct; "
    "5 = excellent, specific, correct and shows depth or trade-offs. "
    "Most answers deserve 2 to 4. Give 5 rarely. Judge only what the candidate said; "
    "do not give credit for things they did not say. "
    "The REFERENCE HINTS are examples of good content, not a checklist, and may be "
    "imperfect; use your own technical judgment. "
    "relevance = answers the question asked. technical_accuracy = statements are correct. "
    "communication = clear and structured. jd_alignment = shows skills the job needs. "
    "Quote a short phrase from the answer in 'evidence'. "
    "Set needs_followup true only if the answer was vague or skipped something "
    "important, and then write ONE short follow-up question (max 20 words) about the "
    "vague part. Otherwise needs_followup is false and followup_question is empty. "
    "Calibration rules: a generic textbook answer that never mentions the "
    "candidate's own work scores at most 3 on technical_accuracy and jd_alignment. "
    "For behavioral and project questions, an answer phrased as 'I would...' instead "
    "of describing something they actually did scores at most 2 on relevance. "
    "A one-line definition scores at most 3 on every criterion. "
    "'feedback' must be a statement about the answer, never a question."
)

def calibrate(ev: Evaluation, q: Question, answer: str) -> Evaluation:
    """Deterministic score caps. Small models ignore calibration rules in the prompt."""
    words = len(answer.split())
    cap = 5 if words >= 40 else 4 if words >= 20 else 3   # a 5 needs real depth
    for c in CRITERIA:
        setattr(ev, c, min(getattr(ev, c), cap))

    if not FIRST_PERSON.search(answer):                    # never mentions own work
        ev.technical_accuracy = min(ev.technical_accuracy, 3)
        ev.jd_alignment = min(ev.jd_alignment, 3)

    if q.category in ("behavioral", "project") and HYPOTHETICAL.search(answer):
        ev.relevance = min(ev.relevance, 2)                # asked for a real example
        ev.jd_alignment = min(ev.jd_alignment, 3)

    fb = ev.feedback.strip()
    if fb.endswith("?") or len(fb.split()) < 5:            # model echoed or asked a question
        low = min(CRITERIA, key=lambda c: getattr(ev, c))
        if getattr(ev, low) >= 4:
            ev.feedback = "Solid, specific answer."
        else:
            ev.feedback = f"Weakest area: {low.replace('_', ' ')} ({getattr(ev, low)}/5)."
    return ev


def evaluate(q: Question, asked: str, answer: str, job_title: str) -> Evaluation:
    # Skip the LLM for empty answers: faster and cannot be inflated.
    if len(answer.split()) < 4:
        return Evaluation(
            relevance=1, technical_accuracy=1, communication=1, jd_alignment=1,
            feedback="No substantive answer was given.", evidence="none",
            needs_followup=True,
            followup_question="Could you give it a try, even a partial answer?",
        )
    prompt = (
        f"JOB: {job_title}\n"
        f"CATEGORY: {q.category}\nTOPIC: {q.topic}\n"
        f"QUESTION ASKED: {asked}\n"
        f"REFERENCE HINTS: {'; '.join(q.ideal_points)}\n\n"
        f"CANDIDATE ANSWER:\n{answer}"
    )
    ev = generate(Evaluation, EVAL_SYSTEM, prompt, model=EVAL_MODEL,max_tokens=400)
    return calibrate(ev, q, answer)