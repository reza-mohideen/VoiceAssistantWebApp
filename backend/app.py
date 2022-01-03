import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from VoiceRecognition.Wav2vecLive.engine import Engine


model = Engine("facebook/wav2vec2-base-960h")

class Item(BaseModel):
    text: str


app = FastAPI()

origins = [
    "http://localhost:3000",
    "localhost:3000"
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.post("/transcribe")
async def transcribe(data: Item):
    print(data)
    return {"text": "Hello World"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print('Accepting client connection...')
    final_text = ""
    await websocket.accept()
    while True:
        try:
            # Wait for any message from the client
            data = await websocket.receive()

            # receiving data
            if "text" in data.keys():
                if data["text"] == "start":
                    print("starting transcription")
                    model.run()

                elif data["text"] == "stop":
                    print("stopping transcription")
                    resp = {'value': final_text, 'state': 3}
                    print(resp)
                    await websocket.send_json(resp)
                    final_text = ""
                    model.stop_listening()
                    model.set_state(0)
                    

            # actions while model is running
            if model.get_state() == 1 or model.get_state() == 2:
                if "bytes" in data.keys():
                    model.set_audio_chunk(data["bytes"])

                # sending data
                text,sample_length,inference_time = model.get_last_text() 
                final_text = text                       
                resp = {'value': text, 'state': model.get_state()}
                print(resp)
                await websocket.send_json(resp)
            
            # actions after model has finished transcribing
            if model.get_state() == 3:
                resp = {'value': final_text, 'state': model.get_state()}
                print(resp)
                await websocket.send_json(resp)
                final_text = ""
                model.set_state(0)

        except Exception as e:
            print('error:', e)
    
    print('Bye..')

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)