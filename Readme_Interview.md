# AI Interview Voice Agent

A local, voice-based AI interviewer. It reads a candidate's resume and a job description, plans personalised questions, conducts a spoken interview with live follow-ups, scores every answer on a fixed rubric, and writes a final report.

Everything runs locally: LLM via **Ollama**, speech-to-text via **faster-whisper**, text-to-speech via **pyttsx3**, UI via **Streamlit**. No API keys or cloud services.

## Features

| Requirement | Implementation |
|---|---|
| Resume and JD analysis | Structured extraction plus a per-skill gap check (`app/core/analyzer.py`) |
| Dynamic question generation | Gap-driven question plan (`app/core/planner.py`) |
| Voice interaction | Spoken questions, recorded answers, editable transcript (`app_ui.py`) |
| Dynamic follow-ups | Generated from each answer, max one per question (`app/core/interviewer.py`) |
| Response evaluation | 4-criterion rubric with deterministic score calibration (`app/core/evaluator.py`) |
| Interview summary | Scored report with strengths, weaknesses, skill gaps and recommendation (`app/core/reporter.py`) |
| Interview history (optional) | Not implemented; design described in `docs/ARCHITECTURE.md` |

## Prerequisites

- Python 3.10 or newer
- [Ollama](https://ollama.com) installed and running
- Chrome or Edge (for the microphone widget) and a working microphone
- About 8 GB RAM. A GPU is optional; on CPU only, expect 10-40 s per LLM call with a 3B model.

## Setup (Windows PowerShell)

```powershell
git clone <your-repo-url> interview-agent    # or unzip the project
cd interview-agent
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt

ollama pull llama3.2:3b      # fast model: live scoring
ollama pull llama3.1:8b      # optional: better quality for the final report
```

macOS/Linux: activate with `source venv/bin/activate`.

The first spoken answer downloads the Whisper model (about 150 MB for `base`, 480 MB for `small`), so an internet connection is needed once.

## Run

```powershell
$env:OLLAMA_MODEL = "llama3.2:3b"
$env:OLLAMA_EVAL_MODEL = "llama3.2:3b"
python -m streamlit run app_ui.py
```

Always launch with `python -m streamlit` so the virtual environment's Python is used. Open the address Streamlit prints (usually http://localhost:8501).

### Using the app

1. **Demo mode:** press **Start interview** with no uploads to load the saved sample analysis and question plan (`samples/analysis.json`, `samples/plan.json`). It starts instantly.
2. **Your own files:** upload a resume and a job description (PDF, DOCX or TXT), then press **Start interview**. Analysis and planning take several minutes on CPU. Results are cached in `samples/cache/`, so the same pair starts instantly next time.
3. Listen to each question, record your answer, and **check the transcript**. Fix any recognition errors, then press **Submit answer**. You can also just type.
4. After the last question, or **End interview and get report**, the report is shown, downloadable, and saved to `reports/`.

Click Start only once and do not refresh while a spinner is running; a refresh launches a duplicate job.

### Command-line tools

Each stage also runs on its own:

```powershell
python -m app.core.analyzer samples/resume.txt samples/jd.txt -o samples/analysis.json
python -m app.core.planner samples/analysis.json -o samples/plan.json
python -m app.core.interviewer samples/plan.json samples/analysis.json     # text-only interview
python -m app.core.reporter samples/session.json samples/analysis.json -o samples/report.md
```

## Configuration

| Environment variable | Default | Purpose |
|---|---|---|
| `OLLAMA_MODEL` | `llama3.1:8b` | Model for analysis, planning and reports |
| `OLLAMA_EVAL_MODEL` | same as `OLLAMA_MODEL` | Model for scoring answers |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server |
| `OLLAMA_NUM_CTX` | `8192` | Context window (Ollama's default of 2048 would truncate resumes) |

Recommended: the 3B model for live scoring (speed) and the 8B model for the final report (quality).

## Project structure

```
app/
  config.py            model names and settings
  llm.py               Ollama wrapper: schema-constrained JSON, validation, retries
  models.py            Pydantic schemas shared by all modules
  parsing/extractor.py PDF / DOCX / TXT to text
  core/
    analyzer.py        resume + JD -> profile, per-skill gap analysis, probe topics
    planner.py         probe topics -> question plan
    evaluator.py       rubric scoring, score calibration, follow-up suggestion
    interviewer.py     interview state machine (follow-up vs next question)
    reporter.py        statistics, verdict, report writer
app_ui.py              Streamlit UI with voice input and output
samples/               sample resume, JD, analysis, plan, report
docs/ARCHITECTURE.md   architecture, methodology and limitations
```

## Known limitations

- **Speed:** on CPU, each LLM call takes 10-40 s. Mitigated by small models, cached preparation and a spinner with progress text.
- **Speech recognition:** Whisper makes mistakes on accents and technical terms. Mitigated by an editable transcript, a technical-vocabulary prompt, and a scoring prompt told to ignore recognition errors.
- **Judge quality:** a 3B model is an approximate scorer. Mitigated by a fixed rubric, deterministic score caps and evidence quotes. Treat scores as decision support, not a final verdict.
- **Voice quality:** pyttsx3 uses offline system voices, which sound robotic.
- **History:** not implemented (see the architecture document for the planned design).

## Troubleshooting

| Problem | Fix |
|---|---|
| `No module named 'ollama'` when running Streamlit | Use `python -m streamlit run app_ui.py` inside the activated venv |
| Waveform is flat or "No speech detected" | Allow the microphone for the page, check the Windows input device and privacy settings |
| Code changes have no effect | Stop Streamlit fully with Ctrl+C and relaunch |
| Preparation seems stuck | Check the terminal for `1/3 ... 3/3` progress; only one job should run at a time |
| `AttributeError: audio_input` | `python -m pip install -U streamlit` |
