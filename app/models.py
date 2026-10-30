from typing import Literal

from pydantic import BaseModel, Field


class Role(BaseModel):
    title: str
    company: str
    duration: str = Field(description="e.g. '2 years' or '2021-2023'")
    highlights: list[str]


class Project(BaseModel):
    name: str
    description: str
    technologies: list[str]


class CandidateProfile(BaseModel):
    name: str
    summary: str = Field(description="2-sentence summary of the candidate")
    total_years_experience: float
    skills: list[str]
    roles: list[Role]
    projects: list[Project]
    education: list[str]


class JobProfile(BaseModel):
    title: str = Field(description="The job role name, e.g. 'Backend Engineer'. Not a section heading.")
    seniority: Literal["intern", "junior", "mid", "senior", "lead"]
    min_years_experience: float
    must_have_skills: list[str]
    nice_to_have_skills: list[str]
    responsibilities: list[str]


class SkillAssessment(BaseModel):
    skill: str
    status: Literal["matched", "weak_evidence", "missing"]
    evidence: str = Field(description="Short phrase from the resume showing this skill, or 'none'")


class GapAnalysis(BaseModel):
    assessments: list[SkillAssessment]


class Question(BaseModel):
    category: Literal["gap_probe", "technical", "project", "behavioral"]
    topic: str
    question: str = Field(description="One question to be spoken aloud, max 30 words")
    ideal_points: list[str] = Field(description="2-4 short key points a strong answer covers")


class QuestionPlan(BaseModel):
    questions: list[Question]


class Evaluation(BaseModel):
    relevance: int = Field(ge=1, le=5, description="Does it answer the question asked?")
    technical_accuracy: int = Field(ge=1, le=5, description="Are the technical statements correct?")
    communication: int = Field(ge=1, le=5, description="Clear, structured, concise?")
    jd_alignment: int = Field(ge=1, le=5, description="Shows skills the job needs?")
    feedback: str = Field(description="One sentence on the answer's main strength or weakness")
    evidence: str = Field(description="Short phrase quoted from the answer supporting the scores, or 'none'")
    needs_followup: bool
    followup_question: str = Field(description="One short follow-up question probing a vague or missing part, or empty")