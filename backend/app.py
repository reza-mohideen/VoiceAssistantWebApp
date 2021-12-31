from fastapi import FastAPI, WebSocket
import random
import json
from scipy.io.wavfile import write
import numpy as np
from VoiceRecognition.Wav2vecLive.inference import Wave2Vec2Inference


app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print('Accepting client connection...')
    audio = np.array([], dtype=np.int16)
    wav2vec2 = Wave2Vec2Inference("OthmaneJ/distil-wav2vec2")
    await websocket.accept()
    while True:
        try:
            # Wait for any message from the client
            data = await websocket.receive()

            # convert bytes to float
            buffer = np.frombuffer(data["bytes"], dtype=np.int16) / 32000
            audio = np.concatenate([audio, buffer])

            # transcribe text
            text = wav2vec2.buffer_to_text(audio).lower()
            
            # Send message to the client
            resp = {'value': text}
            await websocket.send_json(resp)
        except Exception as e:
            print('error:', e)
    
    print('Bye..')