import os
import time
import html
import textwrap
import streamlit as st
from dotenv import load_dotenv

# Load .env BEFORE importing project modules.
load_dotenv()

from utlis.audio_processor import process_input
from core.transcriber import (
    transcribe_all,
    LanguageMismatchError
)
from core.sammarize import summarize, generate_title
from core.extractor import (
    extract_action_items,
    extract_key_decisions,
    extract_questions,
)
from core.rag_engine import build_rag_chain, ask_question


# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="AI Video Assistant",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =============================================================================
# CUSTOM UI
# =============================================================================

st.markdown(
    """
<style>
/* ---------- Theme ---------- */
:root {
    --bg: #08080d;
    --surface: #11111a;
    --surface-2: #171722;
    --surface-3: #1d1d2a;
    --border: #29293a;
    --border-soft: #20202e;
    --accent: #8b5cf6;
    --accent-2: #22d3ee;
    --text: #f4f4f7;
    --muted: #8b8ba3;
    --success: #34d399;
    --warning: #fbbf24;
    --danger: #fb7185;
}

/* ---------- App ---------- */
.stApp {
    background:
        radial-gradient(circle at 75% 5%, rgba(139, 92, 246, 0.10), transparent 30%),
        radial-gradient(circle at 15% 85%, rgba(34, 211, 238, 0.05), transparent 25%),
        var(--bg);
}

[data-testid="stSidebar"] {
    background: #0d0d14 !important;
    border-right: 1px solid var(--border) !important;
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.4rem;
}

/* ---------- Typography ---------- */
html, body, [class*="css"] {
    color: var(--text);
}

h1, h2, h3, h4 {
    letter-spacing: -0.02em;
}

/* ---------- Hero ---------- */
.hero {
    padding: 0.4rem 0 1.2rem 0;
}

.hero-title {
    font-size: clamp(2.4rem, 5vw, 4.5rem);
    line-height: 0.98;
    font-weight: 800;
    letter-spacing: -0.055em;
    background: linear-gradient(
        100deg,
        #ffffff 0%,
        #c4b5fd 42%,
        #8b5cf6 65%,
        #22d3ee 100%
    );
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero-subtitle {
    margin-top: 0.7rem;
    color: var(--muted);
    font-size: 0.76rem;
    letter-spacing: 0.22em;
    text-transform: uppercase;
}

/* ---------- Sidebar Brand ---------- */
.brand-title {
    font-size: 1.65rem;
    line-height: 0.95;
    font-weight: 800;
    letter-spacing: -0.04em;
    background: linear-gradient(120deg, #ffffff, #a78bfa, #22d3ee);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.brand-sub {
    color: var(--muted);
    font-size: 0.62rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-top: 0.65rem;
}

/* ---------- Labels / Badges ---------- */
.section-label {
    color: #a78bfa;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    margin-bottom: 0.7rem;
}

.badge {
    display: inline-block;
    padding: 0.24rem 0.62rem;
    border-radius: 999px;
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.badge-purple {
    color: #c4b5fd;
    background: rgba(139, 92, 246, 0.14);
    border: 1px solid rgba(139, 92, 246, 0.28);
}

.badge-green {
    color: #6ee7b7;
    background: rgba(52, 211, 153, 0.10);
    border: 1px solid rgba(52, 211, 153, 0.25);
}

.badge-blue {
    color: #67e8f9;
    background: rgba(34, 211, 238, 0.09);
    border: 1px solid rgba(34, 211, 238, 0.22);
}

/* ---------- Cards ---------- */
.card {
    background: linear-gradient(145deg, rgba(23, 23, 34, 0.96), rgba(13, 13, 20, 0.96));
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.25rem 1.35rem;
    margin-bottom: 1rem;
    box-shadow: 0 10px 35px rgba(0, 0, 0, 0.16);
}

.card-title {
    color: var(--muted);
    font-size: 0.66rem;
    font-weight: 800;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
}

.card-text {
    color: var(--text);
    font-size: 0.9rem;
    line-height: 1.75;
}

/* ---------- Status ---------- */
.status-wrap {
    margin-top: 0.8rem;
}

.status-row {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    padding: 0.55rem 0.65rem;
    margin-bottom: 0.35rem;
    border-radius: 8px;
    border: 1px solid var(--border-soft);
    background: rgba(23, 23, 34, 0.75);
    font-size: 0.72rem;
}

.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}

.dot-active {
    background: #a78bfa;
    box-shadow: 0 0 10px rgba(167, 139, 250, 0.9);
    animation: pulse 1.3s infinite;
}

.dot-done {
    background: var(--success);
    box-shadow: 0 0 7px rgba(52, 211, 153, 0.5);
}

.dot-pending {
    background: #454559;
}

.dot-error {
    background: var(--danger);
    box-shadow: 0 0 8px rgba(251, 113, 133, 0.55);
}

@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.45; transform: scale(0.85); }
}

/* ---------- Live Pipeline Progress ---------- */
.pipeline-progress {
    height: 6px;
    width: 100%;
    background: #252536;
    border-radius: 999px;
    overflow: hidden;
    margin: 0.65rem 0 0.85rem 0;
}
.pipeline-progress-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, #8b5cf6, #22d3ee);
    transition: width 0.25s ease;
}
.pipeline-current {
    color: #8b8ba3;
    font-size: 0.66rem;
    line-height: 1.4;
    margin-bottom: 0.65rem;
}


/* ---------- Inputs ---------- */
.stTextInput > div > div > input,
.stSelectbox > div > div {
    background: var(--surface-2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 9px !important;
}

.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.14) !important;
}

/* ---------- Buttons ---------- */
.stButton > button {
    border-radius: 9px !important;
    border: 1px solid var(--border) !important;
    font-weight: 700 !important;
    transition: all 0.18s ease !important;
}

.stButton > button:hover {
    transform: translateY(-1px);
    border-color: rgba(139, 92, 246, 0.65) !important;
}

.analyse-btn {
    background: linear-gradient(135deg, #8b5cf6, #6d28d9) !important;
    color: white !important;
}

/* ---------- Transcript ---------- */
.transcript-box {
    background: #0c0c13;
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem;
    max-height: 360px;
    overflow-y: auto;
    color: #b5b5c7;
    font-size: 0.8rem;
    line-height: 1.75;
    white-space: pre-wrap;
    word-break: break-word;
}

/* ---------- Empty state ---------- */
.empty-state {
    border: 1px dashed var(--border);
    border-radius: 16px;
    padding: 4rem 1.5rem;
    text-align: center;
    background: rgba(17, 17, 26, 0.55);
}

.empty-icon {
    font-size: 3.4rem;
    margin-bottom: 0.7rem;
}

.empty-title {
    font-size: 1.45rem;
    font-weight: 800;
    margin-bottom: 0.45rem;
}

.empty-sub {
    color: var(--muted);
    max-width: 520px;
    margin: 0 auto;
    line-height: 1.7;
    font-size: 0.82rem;
}

/* ---------- Chat ---------- */
.chat-container {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1rem;
    margin-bottom: 0.8rem;
}

.chat-user {
    background: rgba(139, 92, 246, 0.12);
    border: 1px solid rgba(139, 92, 246, 0.20);
    border-radius: 10px;
    padding: 0.75rem 0.9rem;
    margin: 0.6rem 0;
}

.chat-assistant {
    background: rgba(34, 211, 238, 0.07);
    border: 1px solid rgba(34, 211, 238, 0.16);
    border-radius: 10px;
    padding: 0.75rem 0.9rem;
    margin: 0.6rem 0;
}

.chat-label {
    font-size: 0.62rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.3rem;
}

.chat-user .chat-label { color: #c4b5fd; }
.chat-assistant .chat-label { color: #67e8f9; }

.chat-content {
    font-size: 0.84rem;
    line-height: 1.65;
}

/* ---------- Streamlit cleanup ---------- */
[data-testid="stMarkdownContainer"] p {
    color: var(--text);
}

label {
    color: var(--muted) !important;
    font-size: 0.78rem !important;
}

hr {
    border-color: var(--border) !important;
}

footer {
    visibility: hidden;
}
</style>
""",
    unsafe_allow_html=True,
)


# =============================================================================
# SESSION STATE
# =============================================================================

defaults = {
    "result": None,
    "chat_history": [],
    "processing": False,
    "pipeline_done": False,
    "pipeline_steps": {},
}

for key, default in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default


# =============================================================================
# HELPERS
# =============================================================================

PIPELINE_STEPS = [
    ("audio", "🔊", "Audio Processing"),
    ("transcript", "📝", "Transcription"),
    ("title", "🏷️", "Title Generation"),
    ("summary", "📋", "Summarisation"),
    ("extract", "🔍", "Extraction"),
    ("rag", "🧠", "RAG Engine"),
]


def step_status(key: str) -> str:
    return st.session_state.pipeline_steps.get(key, "pending")


def render_sidebar_status(container):
    """Render the complete live pipeline inside one replaceable container.

    IMPORTANT:
    `st.empty()` represents a single element. Calling markdown(), progress(),
    caption(), etc. directly on it replaces the previous element. That was
    why only the last stage (RAG Engine) was visible.

    We therefore create one nested container on every refresh and render the
    entire pipeline inside it. Each refresh replaces the whole status panel,
    so all six stages remain visible and their states update live.
    """
    states = {
        key: step_status(key)
        for key, _, _ in PIPELINE_STEPS
    }

    total = len(PIPELINE_STEPS)
    done_count = sum(1 for state in states.values() if state == "done")

    active_key = next(
        (key for key, _, _ in PIPELINE_STEPS if states[key] == "active"),
        None,
    )
    error_key = next(
        (key for key, _, _ in PIPELINE_STEPS if states[key] == "error"),
        None,
    )

    # Replace the whole status panel, not individual elements in st.empty().
    container.empty()

    with container.container():
        if st.session_state.processing:
            st.markdown("🟣 **PIPELINE RUNNING**")
        elif st.session_state.pipeline_done:
            st.markdown("🟢 **PIPELINE COMPLETE**")
        else:
            st.markdown("🔵 **READY**")

        progress = done_count / total if total else 0
        st.progress(progress, text=f"Pipeline progress: {done_count}/{total}")

        if active_key:
            current_label = next(
                label
                for key, _, label in PIPELINE_STEPS
                if key == active_key
            )
            st.caption(f"Currently running: **{current_label}**")
        elif error_key:
            error_label = next(
                label
                for key, _, label in PIPELINE_STEPS
                if key == error_key
            )
            st.caption(f"Stopped at: **{error_label}**")
        elif st.session_state.pipeline_done:
            st.caption("All pipeline stages completed.")
        else:
            st.caption("Waiting for Analyse Video.")

        for key, icon, label in PIPELINE_STEPS:
            state = states[key]

            if state == "done":
                indicator = "🟢"
                status_text = "DONE"
            elif state == "active":
                indicator = "🟣"
                status_text = "RUNNING"
            elif state == "error":
                indicator = "🔴"
                status_text = "ERROR"
            else:
                indicator = "⚪"
                status_text = "WAITING"

            st.markdown(
                f"{indicator} {icon} **{label}** — {status_text}"
            )

def set_step(key: str, state: str, status_container=None):
    st.session_state.pipeline_steps[key] = state
    if status_container is not None:
        render_sidebar_status(status_container)


def safe_html(value: str) -> str:
    return html.escape(str(value)).replace("\n", "<br>")


# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.markdown(
        '<div class="brand-title">🎬 AI<br>Video</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="brand-sub">Meeting Intelligence</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    st.markdown(
        '<div class="section-label">Input</div>',
        unsafe_allow_html=True,
    )

    source = st.text_input(
        "YouTube URL or File Path",
        placeholder="https://youtube.com/watch?v=... or /path/to/file.mp4",
    )

    language = st.selectbox(
        "Language",
        ["english", "hinglish"],
        index=0,
    )

    run_btn = st.button(
        "⚡  Analyse Video",
        use_container_width=True,
        type="primary",
    )

    status_placeholder = st.empty()

    if st.session_state.processing or st.session_state.pipeline_done:
        st.markdown("---")

        st.markdown(
            '<div class="section-label">Pipeline Status</div>',
            unsafe_allow_html=True,
        )

        render_sidebar_status(status_placeholder)

    # Safe configuration indicators — never show actual API keys.
    openrouter_ready = bool(os.getenv("OPENROUTER_API_KEY"))
    sarvam_ready = bool(os.getenv("SARVAM_API_KEY"))

    st.markdown(textwrap.dedent(
        f"""
        <div style="font-size:0.65rem;color:#70708a;line-height:1.9">
            <div>OPENROUTER &nbsp;
                <span style="color:{'#34d399' if openrouter_ready else '#fb7185'}">
                    {'● READY' if openrouter_ready else '● MISSING'}
                </span>
            </div>
            <div>SARVAM &nbsp;
                <span style="color:{'#34d399' if sarvam_ready else '#fb7185'}">
                    {'● READY' if sarvam_ready else '● MISSING'}
                </span>
            </div>
        </div>
        """),
        unsafe_allow_html=True,
    )


    badge_cols = st.columns(4)
    badge_cols[0].markdown("📝 **Transcription**")
    badge_cols[1].markdown("📋 **Summarisation**")
    badge_cols[2].markdown("💡 **Meeting Insights**")
    badge_cols[3].markdown("🧠 **RAG Chat**")
# =============================================================================
# MAIN HEADER
# =============================================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-title">AI Video Assistant</div>
        <div class="hero-subtitle">
            Transcribe · Summarise · Extract · Chat with your meetings
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")


# =============================================================================
# RUN PIPELINE
# =============================================================================

if run_btn:
    if not source.strip():
        st.error("Please enter a YouTube URL or local file path.")
    else:
        st.session_state.processing = True
        st.session_state.pipeline_done = False
        st.session_state.result = None
        st.session_state.chat_history = []
        st.session_state.pipeline_steps = {}

        progress_placeholder = st.empty()

        def update_step(key, state):
            set_step(key, state, status_placeholder)
            # Give Streamlit a brief opportunity to flush the updated
            # sidebar state before the next long-running stage starts.
            time.sleep(0.05)

        try:
            progress_placeholder.info(
                "⚙️ Pipeline running — progress is shown live in the sidebar."
            )

            # -------------------------------------------------------------
            # 1. Audio
            # -------------------------------------------------------------
            update_step("audio", "active")
            chunks = process_input(source)
            update_step("audio", "done")

            # -------------------------------------------------------------
            # 2. Transcription
            # -------------------------------------------------------------
            update_step("transcript", "active")
            transcript = transcribe_all(chunks, language)
            update_step("transcript", "done")

            # -------------------------------------------------------------
            # 3. Title
            # -------------------------------------------------------------
            update_step("title", "active")
            title = generate_title(transcript)
            update_step("title", "done")

            # -------------------------------------------------------------
            # 4. Summary
            # -------------------------------------------------------------
            update_step("summary", "active")
            summary = summarize(transcript)
            update_step("summary", "done")

            # -------------------------------------------------------------
            # 5. Extraction
            # -------------------------------------------------------------
            update_step("extract", "active")

            action_items = extract_action_items(transcript)
            decisions = extract_key_decisions(transcript)
            questions = extract_questions(transcript)

            update_step("extract", "done")

            # -------------------------------------------------------------
            # 6. RAG
            # -------------------------------------------------------------
            update_step("rag", "active")
            rag_chain = build_rag_chain(transcript)
            update_step("rag", "done")

            # -------------------------------------------------------------
            # Store results
            # -------------------------------------------------------------
            st.session_state.result = {
                "title": title,
                "transcript": transcript,
                "summary": summary,
                "action_items": action_items,
                "key_decisions": decisions,
                "open_questions": questions,
                "rag_chain": rag_chain,
            }

            st.session_state.processing = False
            st.session_state.pipeline_done = True
            render_sidebar_status(status_placeholder)

            progress_placeholder.success("✅ Analysis complete!")
            time.sleep(0.6)
            progress_placeholder.empty()

            st.rerun()

        except LanguageMismatchError as e:
            st.session_state.processing = False
            st.session_state.pipeline_done = False

            # Keep the failed stage visible as ERROR.
            for key, _, _ in PIPELINE_STEPS:
                if st.session_state.pipeline_steps.get(key) == "active":
                    st.session_state.pipeline_steps[key] = "error"

            render_sidebar_status(status_placeholder)

            progress_placeholder.error(
                f"⚠️ {e}"
            )

        except Exception as e:
            st.session_state.processing = False
            st.session_state.pipeline_done = False

            # Keep the failed stage visible as ERROR.
            for key, _, _ in PIPELINE_STEPS:
                if st.session_state.pipeline_steps.get(key) == "active":
                    st.session_state.pipeline_steps[key] = "error"

            render_sidebar_status(status_placeholder)

            progress_placeholder.error(
                f"❌ Pipeline error: {e}"
            )


# =============================================================================
# RESULTS
# =============================================================================

if st.session_state.result and not st.session_state.processing:
    result = st.session_state.result

    # ---------- Title ----------
    st.markdown(textwrap.dedent(
        f"""
        <div class="card">
            <div class="card-title">📌 Session Title</div>
            <div style="
                font-size:1.45rem;
                font-weight:800;
                line-height:1.35;
            ">
                {safe_html(result["title"])}
            </div>
        </div>
        """),
        unsafe_allow_html=True,
    )

    # ---------- Summary + Transcript ----------
    col1, col2 = st.columns([3, 2], gap="medium")

    with col1:
        st.markdown(
            f"""
            <div class="card">
                <div class="card-title">📋 Summary</div>
                <div class="card-text">
                    {safe_html(result["summary"])}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        with st.expander("📝 Full Transcript", expanded=False):
            st.markdown(
                f'<div class="transcript-box">{safe_html(result["transcript"])}</div>',
                unsafe_allow_html=True,
            )

    # ---------- Analysis ----------
    st.markdown(
        '<div class="section-label" style="margin-top:1.2rem">Meeting Intelligence</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3, gap="medium")

    with c1:
        st.markdown(
            f"""
            <div class="card">
                <div class="card-title">✅ Action Items</div>
                <div class="card-text">
                    {safe_html(result["action_items"])}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="card">
                <div class="card-title">🔑 Key Decisions</div>
                <div class="card-text">
                    {safe_html(result["key_decisions"])}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"""
            <div class="card">
                <div class="card-title">❓ Open Questions</div>
                <div class="card-text">
                    {safe_html(result["open_questions"])}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ---------- RAG Chat ----------
    st.markdown(textwrap.dedent(
        """
        <div style="
            font-size:1.25rem;
            font-weight:800;
            margin-bottom:0.25rem;
        ">
            💬 Chat with your Meeting
        </div>
        <div style="
            color:#70708a;
            font-size:0.78rem;
            margin-bottom:1rem;
        ">
            Ask questions about the analysed transcript.
        </div>
        """),
        unsafe_allow_html=True,
    )

    if st.session_state.chat_history:
        chat_html = '<div class="chat-container">'

        for msg in st.session_state.chat_history:
            content = safe_html(msg["content"])

            if msg["role"] == "user":
                chat_html += textwrap.dedent(f"""
                    <div class="chat-user">
                        <div class="chat-label">You</div>
                        <div class="chat-content">{content}</div>
                    </div>
                """)
            else:
                chat_html += textwrap.dedent(f"""
                    <div class="chat-assistant">
                        <div class="chat-label">🤖 Assistant</div>
                        <div class="chat-content">{content}</div>
                    </div>
                """)

        chat_html += "</div>"
        st.markdown(chat_html, unsafe_allow_html=True)

    else:
        st.markdown(
            """
            <div class="empty-state" style="padding:2rem;margin-bottom:1rem">
                <div style="font-size:2rem">💬</div>
                <div style="font-weight:700;margin-top:0.4rem">
                    Ask anything about your meeting
                </div>
                <div class="empty-sub">
                    Try: “What were the main decisions?”
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    chat_col1, chat_col2 = st.columns([5, 1], gap="small")

    with chat_col1:
        user_input = st.text_input(
            "Your question",
            placeholder="What were the main decisions made?",
            label_visibility="collapsed",
            key="chat_input",
        )

    with chat_col2:
        send_btn = st.button(
            "Send →",
            use_container_width=True,
        )

    if send_btn and user_input.strip():
        with st.spinner("Thinking…"):
            answer = ask_question(
                result["rag_chain"],
                user_input.strip(),
            )

        st.session_state.chat_history.append(
            {
                "role": "user",
                "content": user_input.strip(),
            }
        )

        st.session_state.chat_history.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        st.rerun()

    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat", type="secondary"):
            st.session_state.chat_history = []
            st.rerun()

else:
    # ---------- Empty State ----------
    st.markdown(textwrap.dedent(
        """
        <div class="empty-state">
            <div class="empty-icon">🎬</div>
            <div class="empty-title">Ready to Analyse</div>
            <div class="empty-sub">
                Paste a YouTube URL or local file path in the sidebar,
                choose the language, and click <strong>Analyse</strong>.
                Your video will be transcribed, summarised, analysed,
                and made searchable through RAG chat.
            </div>


        </div>
        """),
        unsafe_allow_html=True,
    )
