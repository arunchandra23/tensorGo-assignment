import streamlit as st
from streamlit_chat import message
import base64
from moviepy.video.io.VideoFileClip import VideoFileClip
import os
import io
import tempfile
import json

from llama_index import StorageContext,load_index_from_storage
from llama_index.llms import OpenAI
from dotenv import load_dotenv
load_dotenv()
import openai
openai.api_key=os.environ.get('OPENAI_API_KEY')
import requests
# =============================+SeamlessM4T Utilities+=========================================


def generateS2TT(extension,audio_buffer):
    try:
        print("started S2TT")
        api_endpoint = os.environ.get('S2TT_API')
        files = {'file': (f'file.{extension}', audio_buffer, 'application/octet-stream')}
        headers = {
            'accept': 'application/json'
        }


        # Make an HTTP POST request to the API
        response = requests.post(api_endpoint, files=files,headers=headers)

        # Handle the response as needed
        if response.status_code == 200:
            print("API request successful")
            print(response.json())
            return response.json()
        else:
            print(f"Error in API request. Status code: {response.status_code}")
            return {"m4t_lang":None}

    except Exception as e:
        print(f"Error sending to API: {e}")
    

def generateT2ST(text,src_lng="eng",tgt_lang="tel"):
    pass

def generateT2TT(text,src_lng="eng",tgt_lang="tel"):
    try:
        api_endpoint = os.environ.get('T2TT_API')
        data={
        "text": text,
        "src_lang": src_lng,
        "tgt_lang": tgt_lang
        }
        print("",data)
        headers = {
            'accept': 'application/json'
        }

        # Make an HTTP POST request to the API
        response = requests.post(api_endpoint, data=json.dumps(data),headers=headers)
        # Handle the response as needed
        if response.status_code == 200:
            print("API request successful")
            return json.loads(json.dumps(response.json()))
        else:
            print(f"Error in API request. Status code: {response.status_code}")
            return {"m4t_lang":None}

    except Exception as e:
        print(f"Error sending to API: {e}")
# =============================+SeamlessM4T Utilities end+=========================================


def ask_question(question:str=""):
    print("loading index")
    storage_context  = StorageContext .from_defaults(persist_dir="./namo_openAi/")
    llm = OpenAI(model='gpt-3.5-turbo', temperature=0, max_tokens=256)
    index = load_index_from_storage(storage_context)
    print("loaded index")
    query_engine=index.as_query_engine(llm=llm)
    response=query_engine.query(question)
    return response.response


def convert_video_to_mp3(video_path):
    try:
        clip = VideoFileClip(video_path)
        audio = clip.audio
        print(">>>",type(audio))
        # Use io.BytesIO to write the audio to an in-memory buffer
        audio.write_audiofile('./video_audio.wav')
        audio.close()
        return
    except Exception as e:
        print(f"Error converting video to audio: {e}")
        return None
def send_to_detect_language_api(extension,audio_buffer):
    try:
        print(type(audio_buffer))
        api_endpoint = os.environ.get('DETECT_LANG_API')
        files = {'file': (f'file.{extension}', io.BytesIO(audio_buffer), 'application/octet-stream')}
        headers = {
            'accept': 'application/json'
        }
        print(api_endpoint)

        # Make an HTTP POST request to the API
        response = requests.post(api_endpoint, files=files,headers=headers)

        # Handle the response as needed
        if response.status_code == 200:
            print("API request successful")
            print(response.json())
            return response.json()
        else:
            print(f"Error in API request. Status code: {response.status_code}")
            return {"m4t_lang":None}

    except Exception as e:
        print(f"Error sending to API: {e}")


def displayPDF(file):
    # Opening file from file path
    with open(file, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')

    # Embedding PDF in HTML
    pdf_display = F'<embed src="data:application/pdf;base64,{base64_pdf}" width="512px" height="512" type="application/pdf">'

    # Displaying File
    st.markdown(pdf_display, unsafe_allow_html=True)
    
def process_uploaded_file(uploaded_file):
    fileExtension=uploaded_file.name.split(".")[-1]
    end_result={}

    audio_buffer=uploaded_file.getvalue()
    speech_translated_text=generateS2TT(fileExtension,audio_buffer)   
    response=send_to_detect_language_api(fileExtension,audio_buffer)
    detected_language=response['m4t_lang']

    end_result['question_text_eng']=speech_translated_text['text']
    # ask question

    answer=ask_question(speech_translated_text['text'])
    print(answer)
    end_result["response_text_eng"]=answer
    native_text=generateT2TT(answer,tgt_lang=detected_language)
    end_result["response_text_native"]=native_text['text']
    return end_result
        
        
def main():
    st.set_page_config(layout="wide")
    col1, col2 = st.columns(2)
    with col1:
        
        st.title("Multilingual : AI chatBot 🤖 - By Arunchandra B")
        uploaded_file = st.file_uploader("Upload audio or video file (Max 10MB)", type=["mp3", "wav"],accept_multiple_files=False)

        if 'generated' not in st.session_state:
            st.session_state['generated'] = []
        if 'past' not in st.session_state:
            st.session_state['past'] = []


        if st.button("Submit") and uploaded_file:
            output=process_uploaded_file(uploaded_file)
            st.session_state.past.append(output['question_text_eng'])
            st.session_state.generated.append(output['response_text_native'])

        if st.session_state['generated']:

            for i in range(0,len(st.session_state['generated'])):
                message(st.session_state['past'][i], is_user=True, key=str(i) + '_user')
                message(st.session_state["generated"][i], key=str(i))
    with col2:
        pdf_path = "./namo.pdf"
        try:
            # Use Google Docs Viewer for embedding PDF
            displayPDF(pdf_path)
        except Exception as e:
            col2.error(f"Error embedding PDF: {e}")

if __name__ == "__main__":
    main()
