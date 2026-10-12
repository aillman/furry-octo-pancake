import os
import urllib.request
import soundfile as sf
import streamlit as st
from pypdf import PdfReader
from docx import Document

st.set_page_config(page_title="Document Voice Studio", page_icon="🎙️", layout="wide")

MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/kokoro-v1.0.onnx"
VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin"

@st.cache_resource
def load_kokoro_engine():
    """Downloads weights once and caches the engine in memory."""
    if not os.path.exists("kokoro-v1.0.onnx"):
        with st.spinner("Initializing neural speech engine (one-time setup)..."):
            urllib.request.urlretrieve(MODEL_URL, "kokoro-v1.0.onnx")
            
    if not os.path.exists("voices-v1.0.bin"):
        with st.spinner("Loading natural voice models..."):
            urllib.request.urlretrieve(VOICES_URL, "voices-v1.0.bin")
            
    from kokoro_onnx import Kokoro
    return Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")

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

# App UI
st.title("🎙️ Open-Source Document Reader")
st.caption("100% Free, Local Neural Text-to-Speech Running on Streamlit Cloud")

kokoro = load_kokoro_engine()

VOICE_OPTIONS = {
    "US Female - Sarah": "af_sarah",
    "US Female - Heart": "af_heart",
    "US Female - Bella": "af_bella",
    "US Male - Adam": "am_adam",
    "US Male - Michael": "am_michael",
    "UK Female - Emma": "bf_emma",
    "UK Male - George": "bm_george",
}

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("1. Input Document")
    uploaded_file = st.file_uploader("Upload PDF, Word, or TXT", type=["pdf", "docx", "txt"])
    raw_text_input = st.text_area("Or paste text directly", height=150, placeholder="Paste text here...")

    st.subheader("2. Voice Settings")
    voice_label = st.selectbox("Select Voice Persona", options=list(VOICE_OPTIONS.keys()), index=0)
    speed_option = st.slider("Playback Speed", min_value=0.5, max_value=2.0, value=1.0, step=0.1)

    generate_btn = st.button("✨ Generate Recording", type="primary", use_container_width=True)

with col2:
    st.subheader("3. Audio Output")
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
            with st.spinner(f"Synthesizing {word_count} words..."):
                try:
                    voice_code = VOICE_OPTIONS[voice_label]
                    
                    # Generate speech audio directly
                    samples, sample_rate = kokoro.create(
                        final_text, 
                        voice=voice_code, 
                        speed=speed_option, 
                        lang="en-us"
                    )
                    
                    output_file = "recording.wav"
                    sf.write(output_file, samples, sample_rate)
                    
                    with open(output_file, "rb") as f:
                        audio_data = f.read()

                    st.success(f"Successfully converted {word_count} words!")
                    st.audio(audio_data, format="audio/wav")
                    st.download_button(
                        label="📥 Download Audio File (WAV)",
                        data=audio_data,
                        file_name="document_recording.wav",
                        mime="audio/wav",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Speech synthesis error: {str(e)}")
