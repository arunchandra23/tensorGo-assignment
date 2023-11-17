from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import whisper
from pydantic import BaseModel
import tempfile
app = FastAPI()

class AudioInput(BaseModel):
    audio_file: UploadFile


def _save_temp_file(data: bytes) -> str:
    """Saves data to a temporary file and returns the path to the file."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(data)
        return tmp.name
    
LANGUAGE_EXTENSION_MAP = {
    "en": "eng",
    "es": "spa",
    "fr": "fra",
    "de": "deu",
    "it": "ita",
    "hi": "hin",
    "te": "tel",
    "bn": "ben",
    "ml": "mal", 
    "ta": "tam",
    "kn": "kan",
    "mr": "mar",
    "ar":"arb",
}

@app.post("/detectLanguage")
async def process_audio(file: UploadFile):
    try:
        # Load the pre-trained model
        model = whisper.load_model("base")
        file_path=_save_temp_file(await file.read())

        # Load and process the audio file
        audio = whisper.load_audio(file_path)
        audio = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(audio).to(model.device)

        # Detect the spoken language
        _, probs = model.detect_language(mel)
        detected_language = max(probs, key=probs.get)
        
        return JSONResponse(content={"m4t_lang": LANGUAGE_EXTENSION_MAP[detected_language]})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
