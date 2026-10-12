import io
import os
import numpy as np
import soundfile as sf
import streamlit as st
from pypdf import PdfReader
from docx import Document
from kokoro import KPipeline

st.set_page_config(page_title="Document Voice Studio", page_icon="🎙️", layout="wide")

@st.cache_resource
def load_tts_pipeline():
    return KPipeline(lang_code='a')

pipeline = load_tts_pipeline()

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

def text_to_audio_bytes(text, voice, speed):
    generator = pipeline(text, voice=voice, speed=speed, split_pattern=r'\n+')
    audio_segments = []
    for _, _, audio in generator:
        audio_segments.append(audio)
    if not audio_segments:
        return None
    full_audio = np.concatenate(audio_segments)
    buffer = io.BytesIO()
    sf.write(buffer, full_audio, 24000, format='WAV')
    buffer.seek(0)
    return buffer

st.title("🎙️ Open-Source Document Reader")
st.caption("Convert PDFs, Word files, or raw text into natural audio recordings online.")

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("1. Input Document or Text")
    uploaded_file = st.file_uploader("Upload a document", type=["pdf", "docx", "txt"])
    raw_text_input = st.text_area("Or paste text directly", height=150, placeholder="Paste text here...")

    st.subheader("2. Voice Settings")
    voice_option = st.selectbox(
        "Select Voice Persona",
        options=["af_heart", "af_bella", "af_sarah", "am_adam", "am_michael", "bf_emma", "bm_george"],
        index=0
    )
    speed_option = st.slider("Playback Speed", min_value=0.5, max_value=2.0, value=1.0, step=0.1)
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
                try:
                    audio_buffer = text_to_audio_bytes(final_text, voice_option, speed_option)
                    if audio_buffer:
                        st.success(f"Successfully processed {word_count} words!")
                        st.audio(audio_buffer, format="audio/wav")
                        st.download_button(
                            label="📥 Download WAV File",
                            data=audio_buffer,
                            file_name="document_recording.wav",
                            mime="audio/wav",
                            use_container_width=True
                        )
                    else:
                        st.error("Failed to generate audio. Please check your text input.")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
