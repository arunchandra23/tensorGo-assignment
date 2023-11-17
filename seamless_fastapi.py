from fastapi import FastAPI, File, UploadFile, Depends
import transformers as transformers
import torchaudio
from pydantic import BaseModel
from fastapi.responses import StreamingResponse

app = FastAPI()

processor = transformers.AutoProcessor.from_pretrained("facebook/hf-seamless-m4t-medium")
model = transformers.SeamlessM4TModel.from_pretrained("facebook/hf-seamless-m4t-medium")
# Dependency to ensure the model is loaded only once
def get_model():
    return model

def process_audio(audio_file_path):
    waveform, sample_rate = torchaudio.load(audio_file_path)

    # Ensure the audio is 16 kHz
    if sample_rate != 16000:
        resampler = torchaudio.transforms.Resample(sample_rate, 16000)
        waveform = resampler(waveform)
    return waveform, sample_rate

# Endpoint to generate speech-to-text
@app.post("/generate_s2t")
def generate_s2t(file: UploadFile = File(...), model: transformers.SeamlessM4TModel = Depends(get_model)):
    waveform, sample_rate = process_audio(file.file)
    audio_inputs = processor(audios=waveform.numpy(), return_tensors="pt")
    text_array_from_audio = model.generate(**audio_inputs, tgt_lang="eng", generate_speech=False)[0].cpu().numpy().squeeze()
    translated_text_from_audio = processor.decode(text_array_from_audio, skip_special_tokens=True )
    return {"text": translated_text_from_audio}


class T2TT_Request(BaseModel):
    text:str
    src_lang: str = "eng"
    tgt_lang: str = "tel"
    
    
# Endpoint to generate text-to-speech
@app.post("/generate_t2s")
def generate_t2s(body:T2TT_Request, model: transformers.SeamlessM4TModel = Depends(get_model)):
    text_inputs = processor(text=body.text, src_lang=body.src_lang, return_tensors="pt")
    audio_array_from_text = model.generate(**text_inputs, tgt_lang=body.tgt_lang)[0].cpu().numpy().squeeze()
    sample_rate = model.config.sampling_rate
    return StreamingResponse(iter(audio_array_from_text), media_type="audio/wav", headers={"Content-Disposition": "inline"})

# Endpoint to generate text-to-text
@app.post("/generate_t2t")
def generate_t2t(body:T2TT_Request, model: transformers.SeamlessM4TModel = Depends(get_model)):
    text_inputs = processor(text=body.text, src_lang=body.src_lang, return_tensors="pt")
    output_tokens = model.generate(**text_inputs, tgt_lang=body.tgt_lang, generate_speech=False)
    translated_text_from_text = processor.decode(output_tokens[0].tolist()[0], skip_special_tokens=True)
    return {"text": str(translated_text_from_text)}
