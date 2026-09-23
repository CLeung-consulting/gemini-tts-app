import os
import streamlit as st
from google import genai
from google.genai import types

# Page setup
st.set_page_config(
    page_title="Gemini Article Audio Generator",
    page_icon="🎙️",
    layout="centered"
)

st.title("🎙️ Article to Verbal Soundtrack")
st.markdown("Upload or paste an article to generate a spoken audio soundtrack using Google Gemini.")

# Sidebar for configuration & API key handling
st.sidebar.header("Configuration")

# Check environment variable first, otherwise prompt user in sidebar
env_api_key = os.environ.get("GEMINI_API_KEY", "")

if env_api_key:
    api_key = env_api_key
    st.sidebar.success("Gemini API Key detected from Environment.")
else:
    api_key = st.sidebar.text_input(
        "Enter your Gemini API Key:", 
        type="password",
        help="Get your key from Google AI Studio"
    )

voice_choice = st.sidebar.selectbox(
    "Select Voice:",
    options=["Puck", "Charon", "Kore", "Fenrir", "Aoede"],
    index=0,
    help="Select the TTS voice configuration."
)

target_language = st.sidebar.selectbox(
    "Translate / Adapt To:",
    options=["Keep Original Language", "English", "Traditional Chinese", "Simplified Chinese", "Spanish", "French", "German", "Japanese"],
    index=0
)

# Text Input Methods
st.subheader("1. Input Text")
input_method = st.radio("Choose input mode:", ["Upload File (.txt)", "Paste Text Direct"])

transcript_text = ""

if input_method == "Upload File (.txt)":
    uploaded_file = st.file_uploader("Upload a text file", type=["txt"])
    if uploaded_file is not None:
        transcript_text = uploaded_file.read().decode("utf-8")
        st.text_area("File Preview", transcript_text, height=150, disabled=True)
else:
    transcript_text = st.text_area("Paste your article text here:", height=200)

st.subheader("2. Generate Audio")

if st.button("Generate Soundtrack", type="primary"):
    if not api_key:
        st.error("Please provide a valid Gemini API Key in the sidebar or via environment variables.")
    elif not transcript_text.strip():
        st.warning("Please provide some text to process.")
    else:
        try:
            with st.spinner("Connecting to Gemini and generating speech..."):
                # Initialize Gemini Client
                client = genai.Client(api_key=api_key)

                # Prepare translation context if requested
                prompt_prefix = ""
                if target_language != "Keep Original Language":
                    prompt_prefix = f"Please read out the following content clearly in {target_language}:\n\n"
                
                full_prompt = prompt_prefix + transcript_text

                # Request TTS output audio (PCM / WAV stream format)
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        response_modalities=["AUDIO"],
                        speech_config=types.SpeechConfig(
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                    voice_name=voice_choice
                                )
                            )
                        )
                    )
                )

                # Extract audio bytes from response
                audio_bytes = None
                for part in response.candidates[0].content.parts:
                    if part.inline_data and part.inline_data.mime_type.startswith("audio/"):
                        audio_bytes = part.inline_data.data
                        break

                if audio_bytes:
                    st.success("Audio soundtrack generated successfully!")
                    
                    # Web app Audio Player
                    st.audio(audio_bytes, format="audio/mp3")

                    # Download button
                    st.download_button(
                        label="📥 Download Audio (.mp3)",
                        data=audio_bytes,
                        file_name="gemini_soundtrack.mp3",
                        mime="audio/mp3"
                    )
                else:
                    st.error("Model responded, but no raw audio data was returned. Check model TTS compatibility.")

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
