import argparse
import json

from ..models import Evaluation, QuestionPlan
from .evaluator import evaluate


class Interview:
    def __init__(self, plan: QuestionPlan, job_title: str, max_followups: int = 1):
        self.questions = plan.questions
        self.job_title = job_title
        self.max_followups = max_followups
        self.idx = 0
        self.followups_used = 0
        self.pending_followup: str | None = None
        self.turns: list[dict] = []

    @property
    def done(self) -> bool:
        return self.idx >= len(self.questions)

    @property
    def current_text(self) -> str | None:
        if self.done:
            return None
        return self.pending_followup or self.questions[self.idx].question

    def submit(self, answer: str) -> Evaluation:
        q = self.questions[self.idx]
        asked = self.current_text
        ev = evaluate(q, asked, answer, self.job_title)
        self.turns.append({
            "category": q.category,
            "topic": q.topic,
            "question": asked,
            "is_followup": self.pending_followup is not None,
            "answer": answer,
            "evaluation": ev.model_dump(),
        })

        # Python decides the flow, not the model: at most max_followups per question.
        can_follow = (
            ev.needs_followup
            and ev.followup_question.strip()
            and self.pending_followup is None
            and self.followups_used < self.max_followups
        )
        if can_follow:
            self.pending_followup = ev.followup_question.strip()
            self.followups_used += 1
        else:
            self.pending_followup = None
            self.followups_used = 0
            self.idx += 1
        return ev


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("analysis")
    ap.add_argument("-o", "--out", default="samples/session.json")
    args = ap.parse_args()

    plan = QuestionPlan.model_validate_json(open(args.plan, encoding="utf-8").read())
    analysis = json.load(open(args.analysis, encoding="utf-8"))
    iv = Interview(plan, analysis["job"]["title"])

    print(f"\nInterview for: {analysis['job']['title']}  (type 'quit' to stop)\n")
    while not iv.done:
        print(f"Interviewer: {iv.current_text}")
        answer = input("You: ").strip()
        if answer.lower() == "quit":
            break
        print("  (scoring...)")
        ev = iv.submit(answer)
        print(f"  [R{ev.relevance} T{ev.technical_accuracy} C{ev.communication} J{ev.jd_alignment}] {ev.feedback}\n")

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(iv.turns, f, indent=2)
    print(f"Saved {len(iv.turns)} turns to {args.out}")