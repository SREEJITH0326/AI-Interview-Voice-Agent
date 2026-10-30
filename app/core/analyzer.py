import argparse
import json

from ..llm import generate
from ..models import CandidateProfile, JobProfile, GapAnalysis
from ..parsing.extractor import extract_text

RESUME_SYSTEM = (
    "You extract structured data from resumes. Use ONLY information present in the "
    "resume. Do not invent skills, employers or dates. If something is unknown, use "
    "an empty list or 0. Include internships as roles. Estimate total_years_experience "
    "from the date ranges (for example July 2025 to March 2026 is about 0.7 years). "
    "List every project in the PROJECTS section."
)
JD_SYSTEM = (
    "You extract structured data from job descriptions. The title is the role name "
    "from the first line. Separate hard requirements (must-have) from preferred ones "
    "(nice-to-have). Use only what the text states."
)
GAP_SYSTEM = (
    "You check a resume against a list of skills. Assess EVERY skill in the list, "
    "and ONLY skills from the list. Status rules: "
    "'matched' = the resume shows real use in a role or project. Equivalents count: "
    "MySQL supports SQL; FAISS with embeddings supports vector databases and RAG; "
    "an OpenAI API chatbot supports LLMs. "
    "'weak_evidence' = only named in a skills list, or only loosely related. "
    "'missing' = no sign of it. "
    "In 'evidence', give a short phrase copied from the resume, or 'none'."
)

STATUS_ORDER = {"missing": 0, "weak_evidence": 1, "matched": 2}


def build_probe_topics(job: JobProfile, gaps: GapAnalysis, limit: int = 8) -> list[str]:
    status = {a.skill.lower(): a.status for a in gaps.assessments}
    skills = [(s, True) for s in job.must_have_skills] + \
             [(s, False) for s in job.nice_to_have_skills]
    # Skills the model forgot to assess are treated as weak_evidence (worth probing).
    ranked = sorted(
        skills,
        key=lambda t: (not t[1], STATUS_ORDER[status.get(t[0].lower(), "weak_evidence")]),
    )
    return [s for s, _ in ranked][:limit]


def analyze(resume_text: str, jd_text: str) -> dict:
    print("1/3 Reading resume...")
    candidate = generate(CandidateProfile, RESUME_SYSTEM, f"RESUME:\n{resume_text}")

    print("2/3 Reading job description...")
    job = generate(JobProfile, JD_SYSTEM, f"JOB DESCRIPTION:\n{jd_text}")

    print("3/3 Checking each job skill against the resume...")
    skills = job.must_have_skills + job.nice_to_have_skills
    checklist = "\n".join(f"- {s}" for s in skills)
    gaps = generate(
        GapAnalysis,
        GAP_SYSTEM,
        f"RESUME:\n{resume_text}\n\nSKILLS TO CHECK:\n{checklist}",
    )
    return {
        "candidate": candidate.model_dump(),
        "job": job.model_dump(),
        "gap_analysis": gaps.model_dump(),
        "probe_topics": build_probe_topics(job, gaps),
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("resume")
    ap.add_argument("jd")
    ap.add_argument("-o", "--out", help="save JSON to this file")
    args = ap.parse_args()

    result = analyze(extract_text(args.resume), extract_text(args.jd))
    output = json.dumps(result, indent=2)
    print(output)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output)