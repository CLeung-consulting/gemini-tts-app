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
                    prompt_prefix = f"Please translate and read out the following content clearly in {target_language}:\n\n"
                else:
                    prompt_prefix = "Please read out the following content clearly:\n\n"
                
                full_prompt = prompt_prefix + transcript_text

                # Request AUDIO output using gemini-2.0-flash
                response = client.models.generate_content(
                    model='gemini-3.6-flash',
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

                # Extract audio bytes and MIME type from response parts
                audio_bytes = None
                mime_type = "audio/wav"  # Default fallback

                if response.candidates and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if part.inline_data and part.inline_data.mime_type.startswith("audio/"):
                            audio_bytes = part.inline_data.data
                            mime_type = part.inline_data.mime_type
                            break

                if audio_bytes:
                    st.success("Audio soundtrack generated successfully!")
                    
                    # Determine file extension based on MIME type returned by the API
                    file_ext = "pcm" if "pcm" in mime_type else ("wav" if "wav" in mime_type else "mp3")
                    file_name = f"gemini_soundtrack.{file_ext}"

                    # Web app Audio Player
                    st.audio(audio_bytes, format=mime_type)

                    # Download button
                    st.download_button(
                        label=f"📥 Download Audio (.{file_ext})",
                        data=audio_bytes,
                        file_name=file_name,
                        mime=mime_type
                    )
                else:
                    st.error("Model responded, but no raw audio data was returned. Ensure the prompt content is valid.")

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
