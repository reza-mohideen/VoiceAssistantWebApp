import pyaudio
import webrtcvad
from .inference import Wave2Vec2Inference
import numpy as np
import threading
import time
from sys import exit
import contextvars
from queue import  Queue
import os


class LiveWav2Vec2:
    exit_event = threading.Event()    
    def __init__(self, model_name, lm_path=None, device_name="default"):
        self.model_name = model_name
        self.device_name = device_name  
        self.lm_path = lm_path            

    def stop(self):
        """stop the asr process"""
        LiveWav2Vec2.exit_event.set()
        self.asr_input_queue.put("close")
        print("asr stopped")

    def start(self):
        """start the asr process"""
        self.wav2vec2_initialized = False
        self.asr_output_queue = Queue()
        self.asr_input_queue = Queue()
        self.asr_process = threading.Thread(target=LiveWav2Vec2.asr_process, args=(
            self, self.model_name, self.asr_input_queue, self.asr_output_queue,))
        self.asr_process.start()
        # time.sleep(5)  # start vad after asr model is loaded
        while not self.wav2vec2_initialized:
            pass

        if self.wav2vec2_initialized:
            print("starting VAD")
            self.start_time = time.time()
            self.vad_process = threading.Thread(target=LiveWav2Vec2.vad_process, args=(
                self, self.device_name, self.asr_input_queue,))
            self.vad_process.start()

    def vad_process(self, device_name, asr_input_queue):
        vad = webrtcvad.Vad()
        vad.set_mode(1)

        audio = pyaudio.PyAudio()
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        # A frame must be either 10, 20, or 30 ms in duration for webrtcvad
        FRAME_DURATION = 30
        CHUNK = int(RATE * FRAME_DURATION / 1000)
        RECORD_SECONDS = 50

        microphones = LiveWav2Vec2.list_microphones(audio)
        selected_input_device_id = LiveWav2Vec2.get_input_device_id(
            device_name, microphones)

        stream = audio.open(input_device_index=selected_input_device_id,
                            format=FORMAT,
                            channels=CHANNELS,
                            rate=RATE,
                            input=True,
                            frames_per_buffer=CHUNK)

        frames = b'' 
        frames_tag = [] # holds boolean of whether speech was detected
        end_frame = 0  
        exit_time = None
        while True:         
            if LiveWav2Vec2.exit_event.is_set():
                break            
            frame = stream.read(CHUNK)
            frames_tag.append(vad.is_speech(frame, RATE))
            
            # add frames only if voice is detected
            if frames_tag[-1]:
                frames += frame

            # add every 0.5 seconds of frames to queue
            frame_diff = len(frames) - end_frame
            if frame_diff > 8000:
                asr_input_queue.put(frames)
                end_frame = len(frames)

            # if time > 2 seconds and 90% of last 1 second of frames has no voice detected then listen for 2 more seconds then exit
            NUM_FRAMES = 100
            percent_silence = len([ele for ele in frames_tag[-NUM_FRAMES:] if ele == False]) / NUM_FRAMES
            elapsed_time = time.time() - self.start_time
            if elapsed_time > 2 and (percent_silence > 0.8 and len(frames_tag[-NUM_FRAMES:]) == NUM_FRAMES):
                if exit_time is None:
                    exit_time = time.time()
                elif time.time() - exit_time > 2:
                    break
                else:
                    pass

        stream.stop_stream()
        stream.close()
        audio.terminate()
        self.stop()


    def asr_process(self, model_name, in_queue, output_queue):
        wave2vec_asr = Wave2Vec2Inference(model_name, self.lm_path)
        self.wav2vec2_initialized = True

        print("\nlistening to your voice\n")
        while True:                        
            audio_frames = in_queue.get()       
            if audio_frames == "close":
                break

            float64_buffer = np.frombuffer(
                audio_frames, dtype=np.int16) / 32767
            start = time.perf_counter()
            text = wave2vec_asr.buffer_to_text(float64_buffer).lower()
            inference_time = time.perf_counter()-start
            sample_length = len(float64_buffer) / 16000  # length in sec
            if text != "":
                output_queue.put([text,sample_length,inference_time])                            

    def get_input_device_id(device_name, microphones):
        for device in microphones:
            if device_name in device[1]:
                return device[0]

    def list_microphones(pyaudio_instance):
        info = pyaudio_instance.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')

        result = []
        for i in range(0, numdevices):
            if (pyaudio_instance.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                name = pyaudio_instance.get_device_info_by_host_api_device_index(
                    0, i).get('name')
                result += [[i, name]]
        return result

    def get_last_text(self):
        """returns the text, sample length and inference time in seconds."""
        return self.asr_output_queue.get()           

if __name__ == "__main__":
    print("Live ASR")
    MODELS = {
        "large": "facebook/wav2vec2-large-960h",
        "base": "facebook/wav2vec2-base-960h",
        "distil": "OthmaneJ/distil-wav2vec2"
    }
    LM = "VoiceRecognition/4gram_big.arpa"

    asr = LiveWav2Vec2(model_name=MODELS["distil"], lm_path=LM)
    asr.start()

    try:        
        while True:
            text,sample_length,inference_time = asr.get_last_text()                        
            print(f"{sample_length:.3f}s\t{inference_time:.3f}s\t{text}")
            
    except KeyboardInterrupt:
        asr.stop()  
        exit()