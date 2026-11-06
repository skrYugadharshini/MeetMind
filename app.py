import streamlit as st
import pandas as pd
from pathlib import Path
from meetmind_core import MeetMind
import os


st.set_page_config(page_title="MeetMind", page_icon="🎙️", layout="wide")

# load our custom styles (works from any folder)
css_path = Path(__file__).parent / "style.css"
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# hero banner
st.markdown("""
<div class="hero">
  <h1><span class="emoji">🎙️</span> MeetMind</h1>
  <p>Turn any meeting recording into notes, tasks and answers in seconds.</p>
  <span class="pill">Whisper</span>
  <span class="pill">LangGraph agents</span>
  <span class="pill">Hybrid RAG</span>
  <span class="pill">GPT-OSS 120B</span>
</div>
""", unsafe_allow_html=True)

# feature cards
features = [
    ("📝", "Transcript", "Every word with timestamps."),
    ("✅", "Action items", "Who does what, and by when."),
    ("🔍", "Self-checking", "A checker agent verifies the notes."),
    ("💬", "Chat", "Ask questions and get cited answers."),
]
cols = st.columns(4)
for col, (icon, title, text) in zip(cols, features):
    col.markdown(f"""
    <div class="card">
      <div class="icon">{icon}</div>
      <h3>{title}</h3>
      <p>{text}</p>
    </div>""", unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    api_key = os.getenv("GROQ_API_KEY") or st.text_input("Groq API key", type="password", help="Free at console.groq.com")
    hints = st.text_area("Names & key words (optional)",
                         placeholder="e.g. Priya, Kevin, Nimal, iOS, sprint")
    st.markdown("---")
    st.caption("Built by Yugadharshini · Whisper · LangGraph · Hybrid RAG")

# ---------- Upload ----------
st.markdown('<div class="section-title">Upload your meeting</div>', unsafe_allow_html=True)
audio = st.file_uploader("Drop a recording here",
                         type=["mp3", "m4a", "wav", "mp4"],
                         label_visibility="collapsed")

if audio:
    size_mb = audio.size / 1_000_000
    st.markdown(f"""
    <div class="file-chip">🎧 <b>{audio.name}</b> · {size_mb:.1f} MB</div>
    """, unsafe_allow_html=True)
    st.audio(audio)

    if st.button("✨ Analyze meeting"):
        if not api_key:
            st.warning("Add your Groq API key in the sidebar first.")
        else:
            try:
                with st.status("Working on your meeting...", expanded=True) as status:
                    mm = MeetMind(api_key)
                    st.write("🎧 Transcribing with Whisper...")
                    mm.transcribe(audio.name, audio.getvalue(), hints)
                    st.write("🤖 Agents writing and checking the notes...")
                    st.session_state.result = mm.analyze()
                    st.session_state.mm = mm
                    status.update(label="Done ✅", state="complete", expanded=False)
            except Exception as e:
                st.error(f"Something went wrong: {e}")

# ---------- Results ----------
if "result" in st.session_state:
    result = st.session_state.result
    notes = result["notes"]
    mm = st.session_state.mm
    st.session_state.chat = []

    # stat tiles
    duration = mm.segments[-1]["end"] if mm.segments else 0
    stats = [
        ("⏱️", f"{int(duration // 60)}:{int(duration % 60):02d}", "Duration"),
        ("🎯", len(notes["decisions"]), "Decisions"),
        ("✅", len(notes["action_items"]), "Action items"),
        ("🔍", result["attempts"], "Checker passes"),
    ]
    cols = st.columns(4)
    for col, (icon, value, label) in zip(cols, stats):
        col.markdown(f"""
        <div class="stat">
          <div class="stat-value">{icon} {value}</div>
          <div class="stat-label">{label}</div>
        </div>""", unsafe_allow_html=True)

    # summary
    st.markdown('<div class="section-title">📋 Summary</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="summary">{notes["summary"]}</div>', unsafe_allow_html=True)

    # decisions + action items side by side
    left, right = st.columns([1, 2])
    with left:
        st.markdown('<div class="section-title">🎯 Decisions</div>', unsafe_allow_html=True)
        for d in notes["decisions"]:
            st.markdown(f'<div class="decision">{d}</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="section-title">✅ Action items</div>', unsafe_allow_html=True)
        df = pd.DataFrame(notes["action_items"]).rename(
            columns={"owner": "Owner", "task": "Task", "due": "Due", "timestamp": "Time"})
        df["Due"] = df["Due"].fillna("—")
        st.dataframe(df, hide_index=True, use_container_width=True)

    if result["issues"]:
        st.warning("Checker still found: " + "; ".join(result["issues"]))
    else:
        st.success("🔍 Checker agent verified these notes against the transcript.")



        # ---------- Email + Transcript tabs ----------
    st.write("")
    tab_email, tab_transcript = st.tabs(["📧 Follow-up email", "📝 Transcript"])
    with tab_email:
        st.markdown(result["email"])
        st.download_button("⬇️ Download email", result["email"], file_name="follow_up_email.md")
    with tab_transcript:
        st.text(mm.transcript)
        st.download_button("⬇️ Download transcript", mm.transcript, file_name="transcript.txt")

    # ---------- Chat ----------
    st.markdown('<div class="section-title">💬 Chat with your meeting</div>', unsafe_allow_html=True)
    if "chat" not in st.session_state:
        st.session_state.chat = []

    for role, msg in st.session_state.chat:
        st.chat_message(role).markdown(msg)

    question = st.chat_input("Ask about the meeting, e.g. Why was the launch delayed?")
    if question:
        st.session_state.chat.append(("user", question))
        st.chat_message("user").markdown(question)
        with st.spinner("Thinking..."):
            answer = mm.ask(question)
        st.session_state.chat.append(("assistant", answer))
        st.chat_message("assistant").markdown(answer)