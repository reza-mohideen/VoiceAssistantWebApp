from fastapi import FastAPI, WebSocket
import random
import json
from scipy.io.wavfile import write
import numpy as np


app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print('Accepting client connection...')
    await websocket.accept()
    while True:
        try:
            # Wait for any message from the client
            data = await websocket.receive()
            buffer = np.frombuffer(data["bytes"], dtype=np.int16) / 32000
            # Send message to the client
            val = random.randint(1,5)
            print(val)
            resp = {'value': val}
            await websocket.send_json(resp)
        except Exception as e:
            print('error:', e)
            break
    print('Bye..')