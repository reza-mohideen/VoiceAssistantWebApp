import uvicorn
from fastapi import FastAPI, WebSocket
from VoiceRecognition.Wav2vecLive.engine import Engine


model = Engine("facebook/wav2vec2-base-960h")

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

            # convert bytes to float
            if "text" in data.keys():
                if data["text"] == "start":
                    print("starting transcription")
                    model.run()

                elif data["text"] == "stop":
                    print("stopping transcription")
                    model.set_audio_chunk(data["bytes"])

            if "bytes" in data.keys():
                model.set_audio_chunk(data["bytes"])

            # transcribe text
            text,sample_length,inference_time = model.get_last_text()                        
            print(f"{sample_length:.3f}s\t{inference_time:.3f}s\t{text}")
            # Send message to the client
            resp = {'value': text}
            await websocket.send_json(resp)
        except Exception as e:
            print('error:', e)
    
    print('Bye..')

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)