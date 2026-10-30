# Interview Report: Jane Doe
**Role:** AI Engineer - Applied ML Team  
**Experience:** 2.0 years  
**Overall score:** 3.47 / 5  
**Recommendation:** Recommended

## Summary
The candidate scored 3.47/5 overall, with strengths in prompt engineering and Python, and weaknesses in FastAPI and collaborating with product teams.

## Scores by criterion
| Criterion | Score |
|---|---|
| Relevance | 3.38 |
| Technical Accuracy | 3.5 |
| Communication | 3.62 |
| Jd Alignment | 3.38 |

## Scores by topic
| Topic | Score |
|---|---|
| FastAPI | 3.12 |
| prompt engineering | 4 |
| Python | 4 |
| LLMs | 3.5 |
| Resume Screener | 3.5 |
| collaborate with product | 3.25 |

## Strengths
- prompt engineering
- Python

## Weaknesses
- FastAPI
- collaborate with product

## Skill gaps
- FastAPI - weak evidence on resume; interview score 3.12/5
- speech technologies (STT/TTS) - missing on resume, not covered in the interview
- Kubernetes - missing on resume, not covered in the interview
- MLOps - weak evidence on resume, not covered in the interview

## Suggested next steps
- Focus on improving technical accuracy in FastAPI and developing collaboration skills with product teams.

## Appendix: transcript
**1. FastAPI**  
Q: How would you deploy a FastAPI app with Docker and manage its lifecycle?  
A: deploying a fastapi with docker requires building an aptimized, production ready container image,configuring servce orchestration  
Scores: R3 T3 C3 J3 - missing details on configuration and orchestration

**2. FastAPI (follow-up)**  
Q: How would you use docker-compose to manage the lifecycle of the app?  
A: It composes full lifecyle of an application by defining its multicontainer encironment including service,network and volumes in a single declarative file .eg yaml file  
Scores: R4 T3 C3 J3 - Weakest area: technical accuracy (3/5).

**3. prompt engineering**  
Q: How do you optimize prompt quality for a conversational AI model?  
A: I optimize prompts by using clear instructions, relevant context, examples, and output constraints, then testing and refining them to improve accuracy, relevance, consistency, and reduce hallucinations.  
Scores: R4 T4 C4 J4 - Weakest area: relevance (4/5).

**4. Python**  
Q: What's your favorite Python library for data manipulation and analysis?  
A: My favorite Python library is Pandas because it simplifies data cleaning, manipulation, analysis, and handling structured datasets using DataFrames, making data preprocessing efficient and straightforward.  
Scores: R4 T4 C4 J4 - Pandas is a popular choice for data manipulation and analysis

**5. LLMs**  
Q: How does the OpenAI API handle out-of-vocabulary words in a conversational chatbot?  
A: The OpenAI API uses tokenization to split unfamiliar words into smaller known text units, allowing the model to process rare or new words without relying on a single unknown-word token.  
Scores: R4 T3 C4 J3 - The answer provides a clear technical explanation of how the OpenAI API handles out-of-vocabulary words.

**6. Resume Screener**  
Q: What's the trade-off between using sentence embeddings and FAISS in your resume screener?  
A: Sentence embeddings capture semantic similarity between resumes and job descriptions, while FAISS enables fast vector search; together, they balance matching accuracy, retrieval speed, and computational cost.  
Scores: R4 T3 C4 J3 - The answer provides a clear trade-off between the two technologies, highlighting their respective strengths.

**7. collaborate with product**  
Q: Can you describe a time when you collaborated with a product team to inform a conversational AI feature?  
A: During my Enterprise AI Knowledge Platform project, I focused on understanding user needs and designing a RAG-based chatbot using FastAPI, embeddings, and vector search to deliver accurate, context-aware responses.  
Scores: R2 T4 C4 J4 - The answer seems to be more focused on the candidate's own project, rather than a collaboration with a product team.

**8. collaborate with product (follow-up)**  
Q: How did you ensure the product team's input influenced the conversational AI feature's design?  
A: I would gather product requirements, discuss user needs, incorporate feedback into prompt design and RAG retrieval, and test responses iteratively to ensure the chatbot meets user expectations  
Scores: R2 T4 C3 J3 - incorporate feedback into prompt design and RAG retrieval
