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


# ---------------------------------------------------------
# Experimental condition
#
# Use ONLY:
#     "empathic"
#     "neutral"
#
# Change this value when deploying the two study conditions.
# ---------------------------------------------------------

EMPATHY_CONDITION = "neutral"

# EMPATHY_CONDITION = "empathic"


# ---------------------------------------------------------
# System prompt
# ---------------------------------------------------------

SYSTEM_PROMPT = (
    APP_DIR / "system_prompt_empathy.txt"
).read_text(encoding="utf-8").strip()


# ---------------------------------------------------------
# Load fixed conversation stimuli
# ---------------------------------------------------------

conversation = CONVERSATIONS["neutral"]

INTRODUCTION = conversation["introduction"]
ROUNDS = conversation["rounds"]
CLOSING = conversation["closing"]


# ---------------------------------------------------------
# Model
# ---------------------------------------------------------

MODEL = "gpt-4o-mini"


# ---------------------------------------------------------
# AlertFlorida URL
# ---------------------------------------------------------

ALERT_FLORIDA_URL = (
    "https://apps.floridadisaster.org/alertflorida/"
)


# ---------------------------------------------------------
# Typing effect
# ---------------------------------------------------------

FIXED_TYPING_DELAY_SECONDS = 0.015
GENERATED_TYPING_DELAY_SECONDS = 0.018


# ---------------------------------------------------------
# Timing between stages
# ---------------------------------------------------------

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
    "Please return the code 6289 to the Qualtrics survey to continue."
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
        prior dynamic responses

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
    Generate exactly one brief response to the participant's
    most recent answer.

    The response follows one of two experimental conditions:
        - empathic
        - neutral

    Round 1 (AlertFlorida) is handled separately so that participants
    who indicate that they have not signed up can receive the
    AlertFlorida registration link.

    GPT does NOT generate the study's next question.
    The next question always comes from conversation_config.py.
    """

    client = OpenAI(
        api_key=st.secrets["OPENAI_API_KEY"]
    )

    current_round = ROUNDS[
        st.session_state.round_index
    ]

    current_round_id = current_round["id"]

    current_round_label = current_round["label"]

    current_round_prompt = current_round["prompt"]


    # -----------------------------------------------------
    # Condition-specific response instructions
    # -----------------------------------------------------

    if EMPATHY_CONDITION == "empathic":

        condition_instruction = """
The current experimental condition is EMPATHIC.

Your response should communicate empathy toward what the participant
has shared.

Naturally use language such as:
- "I understand..."
- "I can see..."
- "I can imagine..."

when appropriate.

The empathetic language must be connected to the participant's actual
response. Do not invent feelings, concerns, circumstances, or personal
information that the participant did not express or imply.

Keep the response concise and natural.
""".strip()

    else:

        condition_instruction = """
The current experimental condition is NEUTRAL.

Respond in a neutral, factual, and concise manner.

Do NOT use empathetic or emotionally validating language such as:
- "I understand..."
- "I can see..."
- "I can imagine..."
- "That sounds stressful..."
- "That must be difficult..."
- "I'm glad..."

Do not infer or comment on the participant's emotions.

Briefly acknowledge the information the participant provided without
adding empathy.
""".strip()


    # -----------------------------------------------------
    # Special handling for Round 1: AlertFlorida
    # -----------------------------------------------------

    if current_round_id == "alerts_and_risk":

        round_specific_instruction = f"""
SPECIAL RULE FOR THIS ROUND:

This question asks whether the participant has signed up for
AlertFlorida.

Carefully interpret the participant's latest response.

If the participant clearly indicates that they HAVE ALREADY signed up
for AlertFlorida:
- Briefly acknowledge that they are already signed up.
- Do NOT provide the AlertFlorida registration link.

If the participant indicates that they HAVE NOT signed up, have NOT
done it yet, are unsure whether they are signed up, or otherwise
indicate that they still need to register:
- Briefly respond according to the assigned experimental condition.
- Tell them that they can sign up for AlertFlorida using this link:
{ALERT_FLORIDA_URL}
- Include the URL exactly as written above.

Do not ask a follow-up question.

Do not introduce evacuation, supplies, home preparation, household
needs, or any later study topic.
""".strip()

    else:

        round_specific_instruction = """
There are no additional round-specific instructions.

Respond only to the participant's latest answer according to the
assigned experimental condition.

Do not introduce additional hurricane-preparedness recommendations
beyond the content already provided in the fixed study stimulus.
""".strip()


    # -----------------------------------------------------
    # User prompt sent to GPT
    # -----------------------------------------------------

    prompt = f"""
Current experimental condition:
{EMPATHY_CONDITION}

Current fixed study round:
{current_round_label}

Current fixed study question:
{current_round_prompt}

Conversation so far:
{transcript_for_model()}

Condition-specific instructions:
{condition_instruction}

Round-specific instructions:
{round_specific_instruction}


Write Maya's single brief response to the participant's latest answer.

Important:
- Respond specifically to what the participant just said.
- Follow the assigned EMPATHIC or NEUTRAL condition exactly.
- You may naturally use relevant information the participant shared
  earlier in the conversation.
- Do not invent information about the participant.
- Do not ask any question.
- Do not introduce the next topic.
- Do not preview the next fixed question.
- Do not provide the next study question.
- Do not mention experimental conditions or study design.
- Output only Maya's response.
- Do not include "Maya:" or "Chatbot:".
- The application will display the next fixed question separately.
""".strip()


    response = client.responses.create(
        model=MODEL,
        instructions=SYSTEM_PROMPT,
        input=prompt,
        max_output_tokens=160,
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

    1. Remove the visual 'Chatbot:' prefix.
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
        # Generate response
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

                # Remove participant answer because the round
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