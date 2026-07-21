import streamlit as st
import json
import os
import requests
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
from gtts import gTTS

from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

# -------------------------------------------------------
# Cache Gemini Client
# -------------------------------------------------------

@st.cache_resource
def load_client():
    return genai.Client(api_key=API_KEY)

client = load_client()

# -------------------------------------------------------
# Sidebar
# -------------------------------------------------------

st.sidebar.title("📖 Story Settings")

genre = st.sidebar.selectbox(
    "Story Genre",
    [
        "Fantasy",
        "Sci-Fi",
        "Mystery",
        "Horror",
        "Adventure"
    ]
)

art_style = st.sidebar.selectbox(
    "Art Style",
    [
        "Anime",
        "Realistic",
        "Pixel Art",
        "Watercolor",
        "Cyberpunk"
    ]
)

# -------------------------------------------------------
# Session State
# -------------------------------------------------------

if "history" not in st.session_state:
    st.session_state.history = []

if "started" not in st.session_state:
    st.session_state.started = False

# -------------------------------------------------------
# Gemini Function
# -------------------------------------------------------

def ask_gemini(user_choice):

    prompt = f"""
You are an AI Visual Novel Director.

Genre:
{genre}

Art Style:
{art_style}

Return ONLY valid JSON.

Format:

{{
"story_text":"...",
"image_prompt":"...",
"options":[
"...",
"...",
"..."
]
}}

Rules:

1. story_text must be short.
2. image_prompt must describe the scene.
3. options should contain 2-3 actions.
4. Do NOT write markdown.
5. Do NOT explain anything.
"""

    full_prompt = prompt + "\nPlayer Action: " + user_choice

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=full_prompt
    )

    return response.text

# -------------------------------------------------------
# Story Generator
# -------------------------------------------------------

def generate_story(action):

    try:

        raw = ask_gemini(action)

        # Sometimes Gemini returns ```json

        raw = raw.replace("```json", "")
        raw = raw.replace("```", "")

        data = json.loads(raw)

        return data

    except Exception as e:

        st.error("Failed to parse Gemini response")

        st.write(e)

        return None

# -------------------------------------------------------
# Start Story
# -------------------------------------------------------

st.title("🎮 AI Visual Novel")

st.write("Choose your own adventure!")

if not st.session_state.started:

    if st.button("Start Story"):

        st.session_state.started = True

        story = generate_story("Start the story")

        if story:
            st.session_state.history.append(story)

# -------------------------------------------------------
# Display History
# -------------------------------------------------------

for index, scene in enumerate(st.session_state.history):

    st.markdown("---")

    st.subheader(f"Scene {index+1}")

    # Story Text
    st.write(scene["story_text"])

    # -------------------------------
    # TTS
    # -------------------------------

    try:

        tts = gTTS(scene["story_text"])

        tts.save("narration.mp3")

        audio = open("narration.mp3", "rb")

        st.audio(audio.read())

    except:

        st.toast("Audio generation failed")

    # -------------------------------
    # Image
    # -------------------------------

    try:

        image_prompt = scene["image_prompt"]

        url = f"https://image.pollinations.ai/prompt/{image_prompt}"

        response = requests.get(url)

        img = Image.open(BytesIO(response.content))

        st.image(img)

    except:

        st.toast("Image server is busy, skipping visual...")

    # -------------------------------
    # Dynamic Buttons
    # -------------------------------

    if index == len(st.session_state.history)-1:

        st.write("### What do you do next?")

        for option in scene["options"]:

            if st.button(option):

                next_story = generate_story(option)

                if next_story:

                    st.session_state.history.append(next_story)

                    st.rerun()