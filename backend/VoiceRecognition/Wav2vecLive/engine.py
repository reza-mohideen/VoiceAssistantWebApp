from torch.cuda import _check_cubins
import webrtcvad
from .inference import Wav2Vec2Inference
import numpy as np
import threading
import time
from sys import exit
from queue import  Empty, Queue


class Engine:
    exit_event = threading.Event()    
    def __init__(self, model_name, lm_path=None):
        print('loading model')
        self.model = Wav2Vec2Inference(model_name, lm_path)
        self.vad = webrtcvad.Vad()
        self.input_queue = Queue()
        self.audio_chunks = Queue()
        self.transcription = ""
        """
        states -
        0: both threads stopped
        1: detect_silence && transcribe_audio threads running
        2: detect_silence thread stopped but transcribe_audio thread running
        3: final transcription ready
        """
        self.state = 0 

    def reset(self):
        Engine.exit_event.clear()

        # clear queues
        while not self.audio_chunks.empty():
            try:
                self.audio_chunks.get(False)
            except Empty:
                continue
        while not self.input_queue.empty():
            try:
                self.input_queue.get(False)
            except Empty:
                continue
        
        self.transcription = ""
        self.state = 0
            
    def stop_listening(self):
        """stop the asr process"""
        self.input_queue.put("close")
        while not self.audio_chunks.empty():
            try:
                self.audio_chunks.get(False)
            except Empty:
                continue
        self.state = 2
        print("asr stopped")

    def run(self):
        """start the asr process"""
        self.transcribe_audio = threading.Thread(target=Engine.transcribe_audio, args=(
            self, self.input_queue,))
        self.transcribe_audio.start()
        
        print("starting VAD")
        self.start_time = time.time()
        self.detect_silence = threading.Thread(target=Engine.detect_silence, args=(
            self, self.audio_chunks, self.input_queue,))
        self.detect_silence.start()

        self.state = 1

    def detect_silence(self, audio_chunks, asr_input_queue):
        self.vad.set_mode(3)
        
        NUM_FRAMES = 10
        RATE=16000
        CHUNK=960 #30ms
        FRAMES=20000

        frames = b""
        exit_time = None
        prev_frame = 0
        silence_tags = []
        while True:     
            if Engine.exit_event.is_set():
                break

            try:
                print('detecting silence')
                frame = audio_chunks.get()
                    
                # detect silince
                silence_tags.append(self.vad.is_speech(frame[:CHUNK], RATE))

                # if time > 2 seconds and 80% of last 3 second of frames has no voice detected then listen for 2 more seconds then exit
                percent_silence = len([ele for ele in silence_tags[-NUM_FRAMES:] if ele == False]) / NUM_FRAMES
                elapsed_time = time.time() - self.start_time
                print(f"percent silence is {percent_silence} and elapsed time is {elapsed_time}")
                if percent_silence > 0.5:
                    if exit_time is None:
                        exit_time = time.time()
                    elif time.time() - exit_time > 2:
                        break

                if silence_tags[-1]:
                    # add frames to queue
                    frames += frame
                
                frame_diff = len(frames) - prev_frame
                if frame_diff > FRAMES:
                    asr_input_queue.put(frames)
                    prev_frame = len(frames)

            except Empty:
                continue

        self.stop_listening()

    def transcribe_audio(self, in_queue):
        
        while True:  
            try:
                audio_frames = in_queue.get(block=False)       
                if audio_frames == "close" or Engine.exit_event.is_set():
                    break
                print("transcribing text")
                float64_buffer = np.frombuffer(audio_frames, dtype=np.int16) / 32767
                start = time.perf_counter()
                text = self.model.buffer_to_text(float64_buffer).lower()
                inference_time = time.perf_counter()-start
                sample_length = len(float64_buffer) / 16000  # length in sec
                if text != "":
                    # output_queue.put([text,sample_length,inference_time]) 
                    self.transcription = text 

            except Empty:
                continue

        self.state = 3

    def set_audio_chunk(self, chunk):
        self.audio_chunks.put(chunk[44:])

    def get_transcription(self):
        """returns the text, sample length and inference time in seconds."""
        return self.transcription

    def get_state(self):
        return self.state

    def set_state(self, state):
        self.state = state

if __name__ == "__main__":
    print("Live ASR")
    MODELS = {
        "large": "facebook/wav2vec2-large-960h",
        "base": "facebook/wav2vec2-base-960h",
        "distil": "OthmaneJ/distil-wav2vec2"
    }
    LM = "VoiceRecognition/4gram_big.arpa"

    asr = Engine(model_name=MODELS["distil"], lm_path=None)
    asr.run()

    try:        
        while True:
            text,sample_length,inference_time = asr.get_last_text()                        
            print(f"{sample_length:.3f}s\t{inference_time:.3f}s\t{text}")
            
    except KeyboardInterrupt:
        asr.stop()  
        exit()