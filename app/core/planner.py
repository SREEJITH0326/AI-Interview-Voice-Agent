import argparse
import json

from ..llm import generate
from ..models import QuestionPlan

PLANNER_SYSTEM = (
    "You are a technical interviewer. Write exactly ONE question for each slot, in the "
    "same order as the slots. Each question must be at most 25 words, natural when "
    "spoken aloud, and ask only ONE thing (never join two questions with 'and'). "
    "Ground every question in the candidate's real experience shown under CANDIDATE "
    "EXPERIENCE; do not ask about technologies the candidate never used, unless the "
    "slot is a gap_probe. "
    "gap_probe = little or no evidence of this skill; ask how they would approach it, "
    "linking to something they have really done (for example Flask when the skill is FastAPI). "
    "technical = the resume claims this skill; ask HOW they used it in their own work. "
    "project = ask about one design decision or trade-off in that project. "
    "behavioral = ask for one real past example. "
    "ideal_points = 2-4 concrete technical facts a strong answer would mention. "
    "NEVER write instructions like 'explain', 'describe', 'provide' or 'link to'. "
    "Example for a FastAPI question: "
    "['async def endpoints with await for I/O', 'uvicorn workers for scaling', "
    "'avoid blocking calls inside async code']. "
    "For behavioral questions, ideal_points are things like 'names a specific situation', "
    "'states their own action', 'gives a measurable result'."
)

BAD_STARTS = ("explain", "describe", "link", "provide", "highlight", "discuss")


def build_slots(analysis: dict, max_topics: int = 4) -> list[dict]:
    assessed = {a["skill"].lower(): a for a in analysis["gap_analysis"]["assessments"]}
    slots = []

    for topic in analysis["probe_topics"][:max_topics]:
        a = assessed.get(topic.lower(), {})
        status = a.get("status", "weak_evidence")
        slots.append({
            "category": "technical" if status == "matched" else "gap_probe",
            "topic": topic,
            "resume_status": status,
            "resume_evidence": a.get("evidence", "none"),
        })

    projects = analysis["candidate"]["projects"]
    if projects:
        p = projects[0]
        slots.append({
            "category": "project",
            "topic": p["name"],
            "resume_status": "claimed",
            "resume_evidence": p["description"],
        })

    duties = analysis["job"]["responsibilities"]
    slots.append({
        "category": "behavioral",
        "topic": duties[-1] if duties else "teamwork",
        "resume_status": "n/a",
        "resume_evidence": "none",
    })
    return slots


def find_problems(result: QuestionPlan, slots: list[dict]) -> list[str]:
    problems = []
    if len(result.questions) != len(slots):
        problems.append(f"Return exactly {len(slots)} questions, one per slot.")
    for i, q in enumerate(result.questions, 1):
        if len(q.question.split()) > 30:
            problems.append(f"Question {i} is too long; max 25 words.")
        if any(p.lower().startswith(BAD_STARTS) for p in q.ideal_points):
            problems.append(f"Question {i}: ideal_points must be concrete facts, not instructions.")
    return problems


def plan(analysis: dict, retries: int = 2) -> QuestionPlan:
    slots = build_slots(analysis)
    experience = "\n".join(
        f"- {h}" for r in analysis["candidate"]["roles"] for h in r["highlights"]
    )
    prompt = (
        f"ROLE: {analysis['job']['title']}\n"
        f"CANDIDATE: {analysis['candidate']['summary']}, "
        f"{analysis['candidate']['total_years_experience']} years experience\n"
        f"CANDIDATE EXPERIENCE:\n{experience}\n\n"
        f"SLOTS:\n{json.dumps(slots, indent=2)}"
    )

    result = generate(QuestionPlan, PLANNER_SYSTEM, prompt)
    for _ in range(retries):
        problems = find_problems(result, slots)
        if not problems:
            break
        print("Retrying:", "; ".join(problems))
        result = generate(QuestionPlan, PLANNER_SYSTEM, prompt + "\n\nFIX THESE PROBLEMS:\n" + "\n".join(problems))

    # Slots are the source of truth for category and topic, so the model can't drift.
    for q, s in zip(result.questions, slots):
        q.category = s["category"]
        q.topic = s["topic"]
    return result



if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("analysis", help="path to analysis.json from the analyzer")
    ap.add_argument("-o", "--out", help="save the plan to this file")
    args = ap.parse_args()

    with open(args.analysis, encoding="utf-8") as f:
        analysis = json.load(f)

    result = plan(analysis)
    for i, q in enumerate(result.questions, 1):
        print(f"\n{i}. [{q.category}] {q.topic}\n   {q.question}")
        for point in q.ideal_points:
            print(f"     - {point}")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, indent=2)