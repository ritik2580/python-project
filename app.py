# app.py

import streamlit as st
from moviepy.editor import VideoFileClip
import tempfile
import os
from google.cloud import speech
import openai
from dotenv import load_dotenv
import json

# Function to set up Google credentials from Streamlit secrets
def setup_google_credentials():
    # Load Google credentials JSON from secrets
    google_credentials_json = st.secrets["GOOGLE_APPLICATION_CREDENTIALS"]
    
    # Write the credentials to a temporary file
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as temp_google_credentials:
        temp_google_credentials.write(google_credentials_json)
        temp_google_credentials_path = temp_google_credentials.name

    # Set the environment variable
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_google_credentials_path

# Initialize OpenAI API using secrets
openai.api_key = st.secrets[" 22ec84421ec24230a3638d1b51e3a7dc"]

# Initialize Google Speech-to-Text Client
def initialize_google_client():
    client = speech.SpeechClient()
    return client

google_client = initialize_google_client()

# Function to extract audio from video
def extract_audio(video_path):
    video = VideoFileClip(video_path)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio:
        video.audio.write_audiofile(tmp_audio.name, codec='pcm_s16le')
        return tmp_audio.name

# Function to transcribe audio using Google Speech-to-Text
def transcribe_audio(audio_path):
    with open(audio_path, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        language_code="en-US",
        enable_automatic_punctuation=True,
    )

    response = google_client.recognize(config=config, audio=audio)

    transcript = ""
    for result in response.results:
        transcript += result.alternatives[0].transcript + " "

    return transcript.strip()

# Function to clean transcription using GPT-4
def clean_transcription(transcript):
    prompt = f"Please correct any grammatical mistakes in the following transcription:\n\n{transcript}"
    
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",  # Ensure you're using a GPT-4 engine if available
            prompt=prompt,
            max_tokens=1000,
            temperature=0.5,
        )
        cleaned_text = response.choices[0].text.strip()
        return cleaned_text
    except Exception as e:
        st.error(f"Error with OpenAI GPT-4: {e}")
        return transcript  # Return original if error occurs

def main():
    # Set up Google credentials
    setup_google_credentials()
    
    st.title("Video Transcription and Cleaning App")
    st.write("Upload a video file, transcribe its audio using Google's Speech-to-Text, and clean the transcription with GPT-4.")

    uploaded_file = st.file_uploader("Choose a video file", type=["mp4", "mov", "avi", "mkv"])

    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_video:
            tmp_video.write(uploaded_file.read())
            video_path = tmp_video.name

        st.video(video_path)

        if st.button("Transcribe and Clean"):
            with st.spinner("Extracting audio from video..."):
                try:
                    audio_path = extract_audio(video_path)
                    st.success("Audio extracted successfully!")
                except Exception as e:
                    st.error(f"Error extracting audio: {e}")
                    return

            with st.spinner("Transcribing audio using Google Speech-to-Text..."):
                try:
                    transcription = transcribe_audio(audio_path)
                    st.success("Transcription completed!")
                except Exception as e:
                    st.error(f"Error transcribing audio: {e}")
                    return

            with st.spinner("Cleaning transcription using OpenAI GPT-4..."):
                try:
                    cleaned_transcription = clean_transcription(transcription)
                    st.success("Transcription cleaned successfully!")
                except Exception as e:
                    st.error(f"Error cleaning transcription: {e}")
                    cleaned_transcription = transcription  # Fallback to original

            st.subheader("Original Transcription:")
            st.write(transcription)

            st.subheader("Cleaned Transcription:")
            st.write(cleaned_transcription)

            # Optionally, allow users to download the cleaned transcription
            st.download_button(
                label="Download Cleaned Transcription",
                data=cleaned_transcription,
                file_name="cleaned_transcription.txt",
                mime="text/plain"
            )

            # Clean up temporary files
            os.remove(video_path)
            os.remove(audio_path)

if __name__ == "__main__":
    main()
