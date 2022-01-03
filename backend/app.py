import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from VoiceRecognition.Wav2vecLive.engine import Engine
from VoiceRecognition.nlu.actions import Action

model = Engine("facebook/wav2vec2-base-960h", "backend/resources/4gram_big.arpa")
nlu = Action()

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
    print(data.text)
    return {"text": nlu.take_action(data.text)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print('Accepting client connection...')
    await websocket.accept()
    while True:
        try:
            # Wait for any message from the client
            data = await websocket.receive()
            model_state = model.get_state()


            # receiving data
            if "text" in data.keys():
                if data["text"] == "start" and model_state == 0:
                    print("starting transcription")
                    model.run()

                elif data["text"] == "stop" and model_state !=0:
                    print("stopping transcription")
                    resp = {'value': model.get_transcription(), 'state': 3}
                    print(resp)
                    await websocket.send_json(resp)
                    
            # actions while model is running
            if model_state == 1 or model_state == 2:
                if "bytes" in data.keys():
                    model.set_audio_chunk(data["bytes"])

                # sending data
                text = model.get_transcription() 
                resp = {'value': text, 'state': model_state}
                print(resp)
                await websocket.send_json(resp)
            
            # actions after model has finished transcribing
            if model_state == 3:
                resp = {'value': model.get_transcription(), 'state': 3}
                print(resp)
                await websocket.send_json(resp)
                model.reset()


        except Exception as e:
            print('error:', e)
    
    print('Bye..')

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)