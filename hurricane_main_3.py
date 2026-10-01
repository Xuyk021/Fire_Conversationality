import re
import time
from pathlib import Path

import streamlit as st
from openai import OpenAI

from conversation_config import CONVERSATIONS


# =========================================================
# Configuration
# =========================================================

APP_DIR = Path(__file__).parent

# EMPATHY_CONDITION = "empathic"

EMPATHY_CONDITION = "neutral"



# This is for low conversationality control condition. It is not used in the main chatbot app.
# SYSTEM_PROMPT = (
#     APP_DIR / "system_prompt_l_con.txt"
# ).read_text(encoding="utf-8").strip()

SYSTEM_PROMPT = (
    APP_DIR / "system_prompt_h_con.txt"
).read_text(encoding="utf-8").strip()

conversation = CONVERSATIONS[EMPATHY_CONDITION]

INTRODUCTION = conversation["introduction"]
ROUNDS = conversation["rounds"]
CLOSING = conversation["closing"]

MODEL = "gpt-4o-mini"

# Typing effect
FIXED_TYPING_DELAY_SECONDS = 0.015
GENERATED_TYPING_DELAY_SECONDS = 0.018

# Timing between stages
INTRO_TO_FIRST_QUESTION_DELAY_SECONDS = 1.0
NEXT_QUESTION_DELAY_SECONDS = 0.5

# Minimum amount of time the Thinking cue should remain visible.
# If the API itself takes longer than this, the cue simply remains
# visible until the API response arrives.
MIN_THINKING_TIME_SECONDS = 1.2

# Delay after the entire conversation has finished
END_DELAY_SECONDS = 4.0

END_MESSAGE = (
    "This is the end of the interaction. "
    "Please return to the Qualtrics survey to continue."
)


# =========================================================
# Page setup
# =========================================================

st.set_page_config(
    page_title="Hurricane Preparedness Chat",
    page_icon="💬",
)

st.title("Hurricane Preparedness Chat")


# =========================================================
# CSS
# =========================================================

# Circular Thinking cue
st.markdown(
    """
    <style>
    .thinking-container {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-top: 3px;
        margin-bottom: 6px;
        color: #777;
        font-style: italic;
        font-size: 0.95rem;
    }

    .thinking-spinner {
        width: 18px;
        height: 18px;
        border: 2.5px solid rgba(128, 128, 128, 0.25);
        border-top-color: #777;
        border-radius: 50%;
        animation: thinking-spin 0.8s linear infinite;
        flex-shrink: 0;
    }

    @keyframes thinking-spin {
        from {
            transform: rotate(0deg);
        }
        to {
            transform: rotate(360deg);
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# Session state
# =========================================================

def initialize_state() -> None:
    """
    Initialize one participant session.
    """

    defaults = {
        "messages": [],
        "round_index": 0,
        "started": False,
        "finished": False,
        "waiting_for_answer": False,
        "api_error": None,
        "end_shown": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            if isinstance(value, list):
                st.session_state[key] = value.copy()
            else:
                st.session_state[key] = value


# =========================================================
# Text helpers
# =========================================================

def clean_chatbot_prefix(text: str) -> str:
    """
    Remove the leading 'Chatbot:' label from fixed stimuli.

    The original text in conversation_config.py is left untouched.
    This only changes how the stimulus is displayed in the UI.
    """

    return re.sub(
        r"^\s*Chatbot:\s*",
        "",
        text.strip(),
        count=1,
        flags=re.IGNORECASE,
    )


def add_message(
    role: str,
    content: str,
    kind: str,
) -> None:
    """
    Save one message to the conversation history.
    """

    st.session_state.messages.append(
        {
            "role": role,
            "content": content,
            "kind": kind,
        }
    )


# =========================================================
# Rendering helpers
# =========================================================

def render_history() -> None:
    """
    Render messages that have already appeared.

    Previously displayed messages are rendered normally rather than
    replaying the typing animation every time Streamlit reruns.
    """

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def typing_stream(
    text: str,
    delay_seconds: float,
):
    """
    Character-by-character typing illusion.
    """

    for char in text:
        yield char
        time.sleep(delay_seconds)


def stream_assistant_message(
    text: str,
    delay_seconds: float,
) -> None:
    """
    Display a newly appearing assistant message using a typing effect.
    """

    with st.chat_message("assistant"):
        st.write_stream(
            typing_stream(
                text,
                delay_seconds,
            )
        )


def show_thinking_cue(placeholder) -> None:
    """
    Display an animated circular Thinking indicator.
    """

    placeholder.markdown(
        """
        <div class="thinking-container">
            <span class="thinking-spinner"></span>
            <span>Thinking...</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# Model context
# =========================================================

def transcript_for_model() -> str:
    """
    Build conversation context for GPT.

    The introduction is omitted because the model mainly needs:
        fixed question
        participant answer
        prior contingent responses

    This allows the model to remember previous participant information
    while keeping the experimental prompts controlled.
    """

    lines = []

    for message in st.session_state.messages:

        if message["kind"] == "introduction":
            continue

        speaker = (
            "Maya"
            if message["role"] == "assistant"
            else "Participant"
        )

        lines.append(
            f"{speaker}: {message['content']}"
        )

    return "\n".join(lines)


# =========================================================
# OpenAI response
# =========================================================

def generate_contingent_response() -> str:
    """
    Generate exactly one brief conversational response
    to the participant's most recent answer.

    GPT does NOT generate the study's next question.
    The next question always comes from conversation_config.py.
    """

    client = OpenAI(
        api_key=st.secrets["OPENAI_API_KEY"]
    )

    current_round = ROUNDS[
        st.session_state.round_index
    ]

    prompt = f"""
Current fixed study round:
{current_round["label"]}

Conversation so far:
{transcript_for_model()}

Write Maya's single brief contingent response to the
participant's latest answer.

Important:
- Respond specifically to what the participant just said.
- You may naturally acknowledge relevant information they
  shared earlier in the conversation.
- Do not ask any question.
- Do not introduce the next topic.
- Do not provide the next study question.
- The application will display the next fixed question separately.
""".strip()

    response = client.responses.create(
        model=MODEL,
        instructions=SYSTEM_PROMPT,
        input=prompt,
        max_output_tokens=120,
    )

    return response.output_text.strip()


# =========================================================
# Fixed stimuli
# =========================================================

def show_fixed_message(
    raw_text: str,
    kind: str,
) -> None:
    """
    Show a new controlled study stimulus.

    1. Remove the meaningless visual 'Chatbot:' prefix.
    2. Stream the fixed message.
    3. Save the cleaned text to message history.
    """

    text = clean_chatbot_prefix(raw_text)

    stream_assistant_message(
        text,
        FIXED_TYPING_DELAY_SECONDS,
    )

    add_message(
        "assistant",
        text,
        kind,
    )


def advance_conversation() -> None:
    """
    Move to the next fixed question.

    After the final participant response:
        1. show the fixed closing;
        2. mark the interaction complete;
        3. wait;
        4. show the final completion notice.
    """

    st.session_state.round_index += 1

    # -----------------------------------------------------
    # More fixed questions remain
    # -----------------------------------------------------

    if st.session_state.round_index < len(ROUNDS):

        time.sleep(
            NEXT_QUESTION_DELAY_SECONDS
        )

        show_fixed_message(
            ROUNDS[
                st.session_state.round_index
            ]["prompt"],
            "fixed_question",
        )

        st.session_state.waiting_for_answer = True

        # Rerun so chat_input appears cleanly under the new question.
        st.rerun()

    # -----------------------------------------------------
    # No more questions: show closing
    # -----------------------------------------------------

    else:

        time.sleep(
            NEXT_QUESTION_DELAY_SECONDS
        )

        show_fixed_message(
            CLOSING,
            "closing",
        )

        st.session_state.waiting_for_answer = False
        st.session_state.finished = True

        # Pause after the ENTIRE conversation has finished.
        time.sleep(
            END_DELAY_SECONDS
        )

        st.session_state.end_shown = True

        # Show the final notice directly without rerunning the page.
        st.info(
            END_MESSAGE
        )

        # Stop this run so the participant remains at the bottom.
        st.stop()


# =========================================================
# Start app
# =========================================================

initialize_state()


# =========================================================
# First visit
# =========================================================

if not st.session_state.started:

    # Mark as started before animation to protect against
    # accidental duplicate initialization.
    st.session_state.started = True

    # -----------------------------------------------------
    # Introduction
    # -----------------------------------------------------

    show_fixed_message(
        INTRODUCTION,
        "introduction",
    )

    # -----------------------------------------------------
    # Pause before Question 1
    # -----------------------------------------------------

    time.sleep(
        INTRO_TO_FIRST_QUESTION_DELAY_SECONDS
    )

    # -----------------------------------------------------
    # Question 1
    # -----------------------------------------------------

    show_fixed_message(
        ROUNDS[0]["prompt"],
        "fixed_question",
    )

    st.session_state.waiting_for_answer = True

    # Rerun to render the completed history normally
    # and activate chat_input.
    st.rerun()


# =========================================================
# Existing conversation
# =========================================================

render_history()


# =========================================================
# API error
# =========================================================

if st.session_state.api_error:

    st.error(
        st.session_state.api_error
    )


# =========================================================
# Participant input
# =========================================================

if (
    st.session_state.waiting_for_answer
    and not st.session_state.finished
):

    user_answer = st.chat_input(
        "Type your response..."
    )

    if user_answer:

        # Immediately lock the current round.
        # This guarantees exactly one response per fixed question.
        st.session_state.waiting_for_answer = False
        st.session_state.api_error = None

        add_message(
            "user",
            user_answer,
            "participant_answer",
        )

        # -------------------------------------------------
        # Show participant response immediately
        # -------------------------------------------------

        with st.chat_message("user"):
            st.markdown(user_answer)

        # -------------------------------------------------
        # Generate conversational response
        # -------------------------------------------------

        with st.chat_message("assistant"):

            response_placeholder = st.empty()

            # Show the circular Thinking cue BEFORE GPT responds.
            show_thinking_cue(
                response_placeholder
            )

            thinking_started_at = time.time()

            try:

                dynamic_reply = (
                    generate_contingent_response()
                )

            except Exception as exc:

                # Remove the participant answer because the round
                # was not successfully completed.
                st.session_state.messages.pop()

                st.session_state.waiting_for_answer = True

                st.session_state.api_error = (
                    "The response service could not be reached. "
                    "Please try submitting your answer again."
                )

                st.rerun()

            # -------------------------------------------------
            # Keep the Thinking cue visible for a minimum time
            # -------------------------------------------------

            thinking_elapsed = (
                time.time()
                - thinking_started_at
            )

            if (
                thinking_elapsed
                < MIN_THINKING_TIME_SECONDS
            ):

                time.sleep(
                    MIN_THINKING_TIME_SECONDS
                    - thinking_elapsed
                )

            # Remove Thinking cue
            response_placeholder.empty()

            # -------------------------------------------------
            # Stream GPT response
            # -------------------------------------------------

            st.write_stream(
                typing_stream(
                    dynamic_reply,
                    GENERATED_TYPING_DELAY_SECONDS,
                )
            )

        # Save GPT response
        add_message(
            "assistant",
            dynamic_reply,
            "generated_response",
        )

        # -------------------------------------------------
        # Continue to next fixed stimulus
        # -------------------------------------------------

        advance_conversation()


# =========================================================
# End of interaction
# =========================================================

if (
    st.session_state.finished
    and st.session_state.end_shown
):

    st.info(
        END_MESSAGE
    )