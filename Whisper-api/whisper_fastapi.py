from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import whisper
from pydantic import BaseModel
import tempfile
import os
import shutil
app = FastAPI()

class AudioInput(BaseModel):
    audio_file: UploadFile


    
LANGUAGE_EXTENSION_MAP = {
    "en": "eng",
    "es": "spa",
    "fr": "fra",
    "de": "deu",
    "it": "ita",
    "hi": "hin",
    "te": "tel",
    "bn": "ben",
    "ta": "tam",
    "kn": "kan",
    "ar":"arb",
}

@app.post("/detectLanguage")
async def process_audio(file: UploadFile):
    try:
        with tempfile.NamedTemporaryFile(delete=False,dir="./",mode='wb') as tmp:
            # Load the pre-trained model
            tmp.write(await file.read())
            model = whisper.load_model("base")
            file_path=tmp.name
            print(os.path.normpath(file_path))

            # Load and process the audio file
            audio = whisper.load_audio(os.path.normpath(file_path))
            audio = whisper.pad_or_trim(audio)
            mel = whisper.log_mel_spectrogram(audio).to(model.device)

            # Detect the spoken language
            _, probs = model.detect_language(mel)
            detected_language = max(probs, key=probs.get)
            return JSONResponse(content={"m4t_lang": LANGUAGE_EXTENSION_MAP[detected_language]})

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
