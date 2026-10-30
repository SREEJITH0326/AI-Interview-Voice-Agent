import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import streamlit as st

import wave
import numpy as np

from app.core.analyzer import analyze
from app.core.interviewer import Interview
from app.core.planner import plan
from app.core.reporter import build_report
from app.models import QuestionPlan
from app.parsing.extractor import extract_text

st.set_page_config(page_title="AI Interview Agent", page_icon="🎙️")
Path("reports").mkdir(exist_ok=True)


# ---------- voice helpers ----------
@st.cache_resource(show_spinner="Loading speech-to-text model (first run downloads it)...")
def load_whisper():
    from faster_whisper import WhisperModel
    return WhisperModel("base", device="cpu", compute_type="int8")


def transcribe(audio_bytes: bytes) -> tuple[str, str]:
    with wave.open(io.BytesIO(audio_bytes), "rb") as w:
        rate, channels, width = w.getframerate(), w.getnchannels(), w.getsampwidth()
        raw = w.readframes(w.getnframes())
    if width != 2:
        raise ValueError(f"Expected 16-bit WAV, got {width * 8}-bit")
    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if channels > 1:
        audio = audio.reshape(-1, channels).mean(axis=1)

    seconds = len(audio) / rate
    peak = float(np.abs(audio).max()) if len(audio) else 0.0
    info = f"Recorded {seconds:.1f}s at {rate} Hz, loudest level {peak:.3f}"
    if peak < 0.01:
        return "", info + " (essentially silent: check your microphone)"

    # Downsample to 16 kHz. Average blocks when the ratio is whole (48000 -> 16000),
    # which avoids the harsh aliasing of simple interpolation.
    if rate % 16000 == 0 and rate != 16000:
        k = rate // 16000
        audio = audio[: len(audio) // k * k].reshape(-1, k).mean(axis=1)
    elif rate != 16000:
        n = int(len(audio) * 16000 / rate)
        audio = np.interp(np.linspace(0, len(audio) - 1, n), np.arange(len(audio)), audio)

    if peak < 0.5:                                    # quiet recording: normalise
        audio = audio / peak * 0.9

    segments, _ = load_whisper().transcribe(
        audio.astype(np.float32), language="en", beam_size=1,
        vad_filter=False, condition_on_previous_text=False,
    )
    return " ".join(s.text.strip() for s in segments).strip(), info


def synthesize(text: str) -> bytes | None:
    """Text to speech with pyttsx3. Runs in a subprocess because pyttsx3 is unreliable
    inside Streamlit's worker threads on Windows."""
    out = Path(tempfile.gettempdir()) / f"tts_{abs(hash(text))}.wav"
    code = (
        "import sys, pyttsx3\n"
        "e = pyttsx3.init(); e.setProperty('rate', 165)\n"
        "e.save_to_file(sys.argv[1], sys.argv[2]); e.runAndWait()\n"
    )
    try:
        subprocess.run([sys.executable, "-c", code, text, str(out)], timeout=60, check=True)
        return out.read_bytes()
    except Exception:
        return None


# ---------- session state ----------
S = st.session_state
S.setdefault("iv", None)
S.setdefault("analysis", None)
S.setdefault("turn", 0)
S.setdefault("last_scores", "")
S.setdefault("report", None)


def start_interview(analysis, qplan):
    S.analysis = analysis
    S.iv = Interview(qplan, analysis["job"]["title"])
    S.turn = 0
    S.report = None
    S.last_scores = ""


def finish():
    with st.spinner("Writing the report..."):
        S.report = build_report(S.iv.turns, S.analysis)
        Path("reports/latest_report.md").write_text(S.report, encoding="utf-8")


# ---------- sidebar: setup ----------
st.title("🎙️ AI Interview Voice Agent")

with st.sidebar:
    st.header("Setup")
    resume = st.file_uploader("Resume (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"])
    jd = st.file_uploader("Job description (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"])
    voice_out = st.checkbox("Speak questions aloud", value=True)

    if st.button("Start interview", type="primary"):
        try:
            if resume and jd:
                with st.spinner("Analysing resume and job, then planning questions. This takes minutes on CPU..."):
                    def to_text(f):
                        p = Path(tempfile.gettempdir()) / f.name
                        p.write_bytes(f.getvalue())
                        return extract_text(str(p))
                    analysis = analyze(to_text(resume), to_text(jd))
                    qplan = plan(analysis)
            else:
                st.info("No files uploaded, using the saved sample.")
                analysis = json.loads(Path("samples/analysis.json").read_text(encoding="utf-8"))
                qplan = QuestionPlan.model_validate_json(
                    Path("samples/plan.json").read_text(encoding="utf-8"))
            start_interview(analysis, qplan)
            st.rerun()
        except Exception as e:
            st.error(f"Could not start: {e}")

iv: Interview | None = S.iv
if iv is None:
    st.write("Upload a resume and job description in the sidebar, or just press **Start interview** to use the sample.")
    st.stop()

# ---------- finished: show report ----------
if S.report:
    st.success("Interview complete.")
    st.markdown(S.report)
    st.download_button("Download report (.md)", S.report, file_name="interview_report.md")
    st.stop()

if iv.done:
    finish()
    st.rerun()

# ---------- interview turn ----------

turn = S.turn
question = iv.current_text
st.caption(f"Question {min(iv.idx + 1, len(iv.questions))} of {len(iv.questions)}")
st.subheader(f"🤖 {question}")

if voice_out:
    key = f"tts_{turn}"
    if key not in S:
        with st.spinner("Preparing voice..."):
            S[key] = synthesize(question)
    if S[key]:
        first_play = f"played_{turn}" not in S
        S[f"played_{turn}"] = True
        st.audio(S[key], format="audio/wav", autoplay=first_play)
    else:
        st.warning("Text-to-speech failed. Read the question above.")

audio = st.audio_input("🎤 Record your answer", key=f"rec_{turn}")
if audio is not None:
    data = audio.getvalue()
    tx_key = f"tx_{turn}_{len(data)}"          # a new recording gets a fresh attempt
    if tx_key not in S:
        S[tx_key] = True
        try:
            with st.spinner("Transcribing..."):
                heard, info = transcribe(data)
            S[f"info_{turn}"] = info
            if heard:
                S[f"ans_{turn}"] = heard
            else:
                st.warning("No speech detected. Record again, or type your answer.")
        except Exception as e:
            st.error(f"Transcription failed: {e!r}")
    if f"info_{turn}" in S:
        st.caption(S[f"info_{turn}"])

# A form sends the text and the click together, so Submit always sees the latest text.
with st.form(key=f"form_{turn}"):
    st.text_area("Your answer (edit the transcript if needed, or just type)",
                 key=f"ans_{turn}", height=130)
    submitted = st.form_submit_button("Submit answer", type="primary")
    ended = st.form_submit_button("End interview and get report")

if submitted:
    answer_text = (S.get(f"ans_{turn}") or "").strip()
    if len(answer_text.split()) < 2:
        st.warning("Please record or type an answer first.")
    else:
        with st.spinner("Scoring your answer... this can take up to a minute on CPU."):
            ev = iv.submit(answer_text)
        S.last_scores = f"R{ev.relevance} T{ev.technical_accuracy} C{ev.communication} J{ev.jd_alignment}"
        S.turn += 1
        st.rerun()

if ended:
    finish()
    st.rerun()

if S.last_scores:
    st.caption(f"Previous answer scored {S.last_scores}")