import asyncio
import io
import os
import edge_tts
from gtts import gTTS
import streamlit as st
from pypdf import PdfReader
from docx import Document

st.set_page_config(page_title="Document Voice Studio", page_icon="🎙️", layout="wide")

VOICES = {
    "US English - Ava (Female)": "en-US-AvaNeural",
    "US English - Andrew (Male)": "en-US-AndrewNeural",
    "US English - Emma (Female)": "en-US-EmmaNeural",
    "UK English - Sonia (Female)": "en-GB-SoniaNeural",
    "UK English - Ryan (Male)": "en-GB-RyanNeural",
}

def extract_text_from_file(uploaded_file):
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    text = ""
    if ext == ".txt":
        text = uploaded_file.read().decode("utf-8", errors="ignore")
    elif ext == ".pdf":
        reader = PdfReader(uploaded_file)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    elif ext == ".docx":
        doc = Document(uploaded_file)
        for p in doc.paragraphs:
            text += p.text + "\n"
    return text

async def generate_edge_tts(text, voice_id, rate_str):
    communicate = edge_tts.Communicate(text, voice_id, rate=rate_str)
    buffer = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buffer.extend(chunk["data"])
    return bytes(buffer)

def generate_gtts_fallback(text):
    tts = gTTS(text=text, lang='en')
    buffer = io.BytesIO()
    tts.write_to_fp(buffer)
    buffer.seek(0)
    return buffer.getvalue()

st.title("🎙️ Open-Source Document Reader")
st.caption("Lightweight Document-to-Speech Converter")

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("1. Input Document or Text")
    uploaded_file = st.file_uploader("Upload a document", type=["pdf", "docx", "txt"])
    raw_text_input = st.text_area("Or paste text directly", height=150, placeholder="Paste text here...")

    st.subheader("2. Voice Settings")
    selected_voice_label = st.selectbox("Select Voice Persona", options=list(VOICES.keys()), index=0)
    speed = st.slider("Playback Speed", min_value=0.5, max_value=2.0, value=1.0, step=0.1)
    
    rate_percentage = int((speed - 1.0) * 100)
    rate_str = f"{'+' if rate_percentage >= 0 else ''}{rate_percentage}%"

    generate_btn = st.button("✨ Generate Recording", type="primary", use_container_width=True)

with col2:
    st.subheader("3. Output Audio")
    if generate_btn:
        final_text = ""
        if uploaded_file is not None:
            final_text = extract_text_from_file(uploaded_file)
        elif raw_text_input.strip():
            final_text = raw_text_input.strip()

        if not final_text:
            st.error("Please upload a file or enter text before generating audio.")
        else:
            word_count = len(final_text.split())
            with st.spinner(f"Converting {word_count} words to speech..."):
                audio_bytes = None
                
                # Primary Attempt: Edge-TTS
                try:
                    voice_id = VOICES[selected_voice_label]
                    audio_bytes = asyncio.run(generate_edge_tts(final_text, voice_id, rate_str))
                except Exception as e:
                    st.warning("Primary speech server returned a 403 block. Switching to fallback TTS engine...")
                    
                    # Secondary Attempt: Google TTS Fallback
                    try:
                        audio_bytes = generate_gtts_fallback(final_text)
                    except Exception as fallback_err:
                        st.error(f"Speech generation failed: {str(fallback_err)}")

                if audio_bytes:
                    st.success(f"Successfully processed {word_count} words!")
                    st.audio(audio_bytes, format="audio/mp3")
                    st.download_button(
                        label="📥 Download MP3 File",
                        data=audio_bytes,
                        file_name="document_recording.mp3",
                        mime="audio/mp3",
                        use_container_width=True
                    )
