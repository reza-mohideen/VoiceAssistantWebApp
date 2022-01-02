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

    def stop(self):
        """stop the asr process"""
        Engine.exit_event.set()
        self.input_queue.put("close")
        print("asr stopped")

    def run(self):
        """start the asr process"""
        self.output_queue = Queue()
        self.input_queue = Queue()
        self.audio_chunks = Queue()
        self.asr_process = threading.Thread(target=Engine.asr_process, args=(
            self, self.input_queue, self.output_queue,))
        self.asr_process.start()
        # time.sleep(5)  # start vad after asr model is loaded
        
        print("starting VAD")
        self.start_time = time.time()
        self.vad_process = threading.Thread(target=Engine.vad_process, args=(
            self, self.audio_chunks, self.input_queue,))
        self.vad_process.start()

    def vad_process(self, audio_chunks, asr_input_queue):

        RATE=16000

        frames = b""
        vad_tags = [] # holds boolean of whether speech was detected
        end_frame = 0  
        exit_time = None
        while True:     
            print("frame length:", len(frames))
            if Engine.exit_event.is_set():
                break

            try:
                frame = audio_chunks.get()
            
                # add frames only if voice is detected
                if True:
                    frames += frame

                # add every 0.5 seconds of frames to queue
                frame_diff = len(frames) - end_frame
                if True:
                    asr_input_queue.put(frames)
                    end_frame = len(frames)
            except Empty:
                continue

                # if time > 2 seconds and 90% of last 1 second of frames has no voice detected then listen for 2 more seconds then exit
                # NUM_FRAMES = 100
                # percent_silence = len([ele for ele in vad_tags[-NUM_FRAMES:] if ele == False]) / NUM_FRAMES
                # elapsed_time = time.time() - self.start_time
                # if elapsed_time > 2 and (percent_silence > 0.8 and len(vad_tags[-NUM_FRAMES:]) == NUM_FRAMES):
                #     if exit_time is None:
                #         exit_time = time.time()
                #     elif time.time() - exit_time > 2:
                #         break
                #     else:
                #         pass

    def asr_process(self, in_queue, output_queue):
        
        while True:  
            try:
                audio_frames = in_queue.get(block=False)       
                if audio_frames == "close":
                    break
                print("transcribing text")
                float64_buffer = np.frombuffer(audio_frames, dtype=np.int16) / 32767
                start = time.perf_counter()
                text = self.model.buffer_to_text(float64_buffer).lower()
                inference_time = time.perf_counter()-start
                sample_length = len(float64_buffer) / 16000  # length in sec
                if text != "":
                    output_queue.put([text,sample_length,inference_time])  

            except Empty:
                continue

    def set_audio_chunk(self, chunk):
        self.audio_chunks.put(chunk[44:])

    def get_last_text(self):
        """returns the text, sample length and inference time in seconds."""
        try:
            return self.output_queue.get(block=False)
        except Empty:
            pass

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