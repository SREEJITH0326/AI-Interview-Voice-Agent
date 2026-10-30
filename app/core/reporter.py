import argparse
import json
from statistics import mean

from pydantic import BaseModel, Field

from ..llm import generate

CRITERIA = ["relevance", "technical_accuracy", "communication", "jd_alignment"]
# Technical accuracy counts most; weights are documented in the methodology.
WEIGHTS = {"technical_accuracy": 0.35, "jd_alignment": 0.25,
           "relevance": 0.20, "communication": 0.20}


class Narrative(BaseModel):
    summary: str = Field(description="2-3 sentence overall assessment")
    strengths: list[str] = Field(description="2-4 strengths, each backed by the data given")
    weaknesses: list[str] = Field(description="2-4 weaknesses, each backed by the data given")
    next_steps: list[str] = Field(description="3 concrete things to practise")


NARRATIVE_SYSTEM = (
    "You write the narrative part of an interview report for a hiring team. Use ONLY "
    "the scores, feedback and evidence provided. Do not invent facts or skills. "
    "Strengths come from high-scoring topics and criteria; weaknesses from low ones. "
    "Be specific, short and professional. Refer to topics by name."
)


def compute_stats(turns: list[dict]):
    crit = {c: round(mean(t["evaluation"][c] for t in turns), 2) for c in CRITERIA}
    overall = round(sum(crit[c] * w for c, w in WEIGHTS.items()), 2)
    per_topic: dict[str, list[float]] = {}
    for t in turns:
        score = mean(t["evaluation"][c] for c in CRITERIA)
        per_topic.setdefault(t["topic"], []).append(score)
    by_topic = {k: round(mean(v), 2) for k, v in per_topic.items()}
    return crit, overall, by_topic


def verdict(overall: float) -> str:
    if overall >= 4.0:
        return "Strongly recommended"
    if overall >= 3.3:
        return "Recommended"
    if overall >= 2.5:
        return "Borderline - needs further evaluation"
    return "Not recommended at this time"


def skill_gaps(analysis: dict, by_topic: dict) -> list[str]:
    tested = {k.lower(): v for k, v in by_topic.items()}
    assessed = {a["skill"].lower() for a in analysis["gap_analysis"]["assessments"]}
    gaps = []
    for a in analysis["gap_analysis"]["assessments"]:
        if a["status"] == "matched":
            continue
        label = a["status"].replace("_", " ")
        score = tested.get(a["skill"].lower())
        if score is None:
            gaps.append(f"{a['skill']} - {label} on resume, not covered in the interview")
        elif score < 4:
            gaps.append(f"{a['skill']} - {label} on resume; interview score {score}/5")
        # score >= 4: the interview confirmed the skill, so it is not a gap
    for topic, score in by_topic.items():
        if score < 3 and topic.lower() not in assessed:
            gaps.append(f"{topic} - scored {score}/5 in the interview")
    return gaps


def build_report(turns: list[dict], analysis: dict) -> str:
    if not turns:
        return "# Interview Report\n\nNo answers were recorded."
    crit, overall, by_topic = compute_stats(turns)
    gaps = skill_gaps(analysis, by_topic)

    facts = (
        f"ROLE: {analysis['job']['title']}\n"
        f"OVERALL SCORE: {overall}/5\n"
        f"CRITERIA AVERAGES: {json.dumps(crit)}\n"
        f"TOPIC SCORES: {json.dumps(by_topic)}\n"
        "PER-ANSWER NOTES:\n"
        + "\n".join(
            f"- {t['topic']}: {t['evaluation']['feedback']} "
            f"(evidence: {t['evaluation']['evidence']})" for t in turns
        )
        
    )
    ranked = sorted(by_topic.items(), key=lambda kv: kv[1])
    facts += (
        f"\nWEAKEST TOPICS: {[k for k, _ in ranked[:2]]}"
        f"\nSTRONGEST TOPICS: {[k for k, _ in ranked[-2:]]}"
    )
    n = generate(Narrative, NARRATIVE_SYSTEM, facts)

    cand = analysis["candidate"]
    lines = [
        f"# Interview Report: {cand['name']}",
        f"**Role:** {analysis['job']['title']}  ",
        f"**Experience:** {cand['total_years_experience']} years  ",
        f"**Overall score:** {overall} / 5  ",
        f"**Recommendation:** {verdict(overall)}",
        "",
        "## Summary", n.summary, "",
        "## Scores by criterion",
        "| Criterion | Score |", "|---|---|",
        *[f"| {c.replace('_', ' ').title()} | {crit[c]} |" for c in CRITERIA],
        "",
        "## Scores by topic",
        "| Topic | Score |", "|---|---|",
        *[f"| {k} | {v} |" for k, v in by_topic.items()],
        "",
        "## Strengths", *[f"- {s}" for s in n.strengths], "",
        "## Weaknesses", *[f"- {s}" for s in n.weaknesses], "",
        "## Skill gaps", *([f"- {g}" for g in gaps] or ["- None identified"]), "",
        "## Suggested next steps", *[f"- {s}" for s in n.next_steps], "",
        "## Appendix: transcript",
    ]
    for i, t in enumerate(turns, 1):
        e = t["evaluation"]
        tag = " (follow-up)" if t["is_followup"] else ""
        lines += [
            f"**{i}. {t['topic']}{tag}**  ",
            f"Q: {t['question']}  ",
            f"A: {t['answer']}  ",
            f"Scores: R{e['relevance']} T{e['technical_accuracy']} "
            f"C{e['communication']} J{e['jd_alignment']} - {e['feedback']}",
            "",
        ]
    return "\n".join(lines)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("session")
    ap.add_argument("analysis")
    ap.add_argument("-o", "--out", default="samples/report.md")
    args = ap.parse_args()

    turns = json.load(open(args.session, encoding="utf-8"))
    analysis = json.load(open(args.analysis, encoding="utf-8"))
    report = build_report(turns, analysis)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(report)
    print(report)