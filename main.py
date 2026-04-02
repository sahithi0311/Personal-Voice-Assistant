import streamlit as st

# Configure streamlit front page
st.set_page_config(
    page_title = "Personal Voice Assistant",
    layout  = 'wide'
)

# import other libraries
import os      # to get path of env variable
import time    # set the timer for listen
import pyttsx3  # convert text to speech
import speech_recognition as sr  # convert speech to text
from groq import Groq   # API key to use LLM service
from dotenv import load_dotenv  # to load API key from system

# load the API key inside code
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Checking if API key is set or not
if not GROQ_API_KEY:
    st.error("Missing API key")
    st.stop()

# Configure the LLM
client = Groq(api_key = GROQ_API_KEY)
MODEL = "llama-3.3-70b-versatile"

# Initialize speech to text recognizer
recognizer = sr.Recognizer()

# Inititalize Text to Speech engine
def get_tts_engine():
    try:
        engine = pyttsx3.init()
        return engine
    except Exception as e:
        st.error("Failed to initialize TTS engine")
        return None

def listen_to_speech():
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration = 1)
            audio = recognizer.listen(source, phrase_time_limit= 10 )
        
        text = recognizer.recognize_google(audio)
        return text.lower()
    except sr.UnknownValueError:
        return "Sorry, I don't catch you"
    except sr.RequestError:
        return "Speech service not available"
    except Exception as e:
        return f"ERROR: {e}"

# send the request to LLM with the help of GROQ API key
def get_ai_response(messages):
    try:
        response = client.chat.completions.create(
            model = MODEL,
            messages = messages,
            temperature = 0.7
        )

        # out of many responses by LLM we are taking 0th response
        result = response.choices[0].message.content
        return result.strip() if result else "Sorry, I could not generate a reponse"
    except Exception as e:
        return f"Error getting AI response: {e}"
        
def speak(text, voice_gender = "girl"):
    try:
        engine = get_tts_engine()
        if engine is None:
            return
        
        # get the list of available voices
        voices = engine.getProperty('voices')

        if voices:
            if voice_gender == "boy":
                for voice in voices:
                    if "male" in voice.name.lower():
                        engine.setProperty('voice', voice.id)
                        break
            else:
                # set the girl voice
                for voice in voices:
                    if 'female' in voice.name.lower() or "zira" in voice.name.lower():
                        engine.setProperty('voice', voice.id)
                        break
        engine.setProperty('rate', 150)  # speed of speech
        engine.setProperty('volume', 0.8) # volume level
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        st.error(f"TTS Error: {e}")




def main():
    st.title("Personal Voice Assistant")
    st.markdown("---")

    # initialize session state for chatting
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "system", "content" : "You are a helpful voice assistant. Respond in 3 to 4 well-structured lines, not a single sentence."}
        ]

    # initialize the session messages
    if "messages" not in st.session_state:
        st.session_state.messages = []

    with st.sidebar:
        st.header("Controls")

        tts_enabled = st.checkbox("Enable Text to Speech", value = True)

        # voice selection
        voice_gender = st.selectbox(
            "Voice Gender",
            options = ['Girl', 'Boy'],
            index = 0,
            help = "Choose Voice Type"
        )

        if st.button("Start Voice Input", type = "primary", use_container_width= True):
            with st.spinner("Listening..."):
                user_input = listen_to_speech()

                # user_input is not empty empty and don't get error then if statement will execute
                if user_input and user_input not in ["Sorry, I don't catch you","Speech service not available"]:
                    # storing user message in messages[], so that we can display it on screen
                    st.session_state.messages.append({"role" : "user", "content" :  user_input }) 
                    st.session_state.chat_history.append({"role": "user", "content" :  user_input}) # to pass to LLM

                    # Get LLM reply
                    with st.spinner("thinking..."):
                        ai_response  = get_ai_response(st.session_state.chat_history)
                        st.session_state.messages.append({"role" : "assistant", "content" :  ai_response }) 
                        st.session_state.chat_history.append({"role": "assistant", "content" :  ai_response}) # to pass to LLM

                    # speak the ai reply
                    if tts_enabled:
                        speak(ai_response, voice_gender.lower())

                    # refresh the display
                    st.rerun()

        st.markdown("---")

        # code to receive text input rather than voice input
        st.subheader("Text Input")
        user_text = st.text_input("Type your message:", key = "text_input" )
        if st.button("send", use_container_width=True) and user_text:
            st.session_state.messages.append({"role" : "user", "content" :  user_text }) 
            st.session_state.chat_history.append({"role": "user", "content" :  user_text}) # to pass to LLM

            with st.spinner("Thinking..."):
                ai_response  = get_ai_response(st.session_state.chat_history)
                st.session_state.messages.append({"role" : "assistant", "content" :  ai_response }) 
                st.session_state.chat_history.append({"role": "assistant", "content" :  ai_response}) # to pass to LLM
            
            # speak the ai reply
            if tts_enabled:
                speak(ai_response, voice_gender.lower())

            # refresh the display
            st.rerun()

        st.markdown("---")

        # button to clear our chat
        if st.button("Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.chat_history = [
            {"role": "system", "content" : "You are a helpful voice assitant. Reply just one line"}
        ]
            st.rerun()

    # display conversation on right side
    st.subheader("CONVERSATION")

    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])
        else:
            with st.chat_message("assistant"):
                st.write(message["content"])

    # Starting message
    if not st.session_state.messages:
        st.info("Welcome: Click on voice input button to start")

if __name__ == "__main__":
    main()