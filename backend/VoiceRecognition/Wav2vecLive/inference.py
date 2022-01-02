import time
import soundfile as sf
import torch
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
from pyctcdecode import build_ctcdecoder
from tqdm import tqdm

# for testing
from datasets import load_dataset, load_metric
import re

class Wav2Vec2Inference():
    def __init__(self, model_name, lm_path=None):
        try:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        except:
            self.device = torch.device("cpu")
        self.model = (Wav2Vec2ForCTC.from_pretrained(model_name)).to(self.device)
        self.processor = Wav2Vec2Processor.from_pretrained(model_name)
        vocab_dict = self.processor.tokenizer.get_vocab()
        sorted_dict = {k.lower(): v for k, v in sorted(vocab_dict.items(), key=lambda item: item[1])}
        if lm_path:
            alpha=0
            beta=0
            beam_width = 1024
            self.decoder = build_ctcdecoder(list(sorted_dict.keys()), lm_path)
        else:
            self.decoder = None


    def buffer_to_text(self, audio_buffer):
        if(len(audio_buffer)==0):
            return ""

        inputs = self.processor(audio_buffer, sampling_rate=16000, return_tensors="pt").to(self.device)

        if self.decoder:
            with torch.no_grad():
                logits = self.model(inputs.input_values).logits.numpy()[0]
            transcription = self.decoder.decode(logits)
        else:
            with torch.no_grad():
                logits = self.model(inputs.input_values).logits
            predicted_ids = torch.argmax(logits, dim=-1)
            transcription = self.processor.batch_decode(predicted_ids)[0]

        return transcription.lower()

    def file_to_text(self,filename):
        audio_input, samplerate = sf.read(filename)
        assert samplerate == 16000
        return self.buffer_to_text(audio_input)

class TestWav2Vec2(Wav2Vec2Inference):
    def __init__(self, model_name, lm_path=None):
        super().__init__(model_name, lm_path=lm_path) 
        self.TEST_SIZE = 100   
        self.model_name = model_name

    def compute_wer(self):
        timit = load_dataset("timit_asr")
        timit = timit.map(self.remove_special_characters)
        timit_test = {
            "text": [item for item in timit["test"]["text"][0:self.TEST_SIZE]],
            "audio": [item["array"] for item in timit["test"]["audio"][0:self.TEST_SIZE]]
        }

        print("Getting predictions...")
        results = map(self.buffer_to_text, tqdm(timit_test["audio"]))
        wer_metric = load_metric("wer")
        print(f"Test WER for {self.model_name}: {wer_metric.compute(predictions=results, references=timit_test['text']):.3f}")

        return {"og": timit_test["text"], "pred": results}

    def remove_special_characters(self, batch):
        chars_to_ignore_regex = '[\,\?\.\!\-\;\:\"]'
        batch["text"] = re.sub(chars_to_ignore_regex, '', batch["text"]).lower() + " "
        return batch

if __name__ == "__main__":
    print("Model test")
    MODELS = {
        "large": "facebook/wav2vec2-large-960h",
        "base": "facebook/wav2vec2-base-960h",
        "distil": "OthmaneJ/distil-wav2vec2"
    }
    LM = "VoiceRecognition/4gram_big.arpa"
    start = time.time()
    asr = Wav2Vec2Inference(model_name=MODELS["distil"],lm_path=LM)
    print(f"time to initialize obect was {time.time()-start}")
    text = asr.file_to_text("resources/augmented_audio_files/noisy_harvard.wav")
    print(text)
    
    # distil_no_lm = TestWav2Vec2(model_name=MODELS["distil"],lm_path=None) # WER = 0.268 on 100 samples
    # distil_no_lm.compute_wer()
    # distil_with_lm = TestWav2Vec2(model_name=MODELS["distil"],lm_path=LM) # WER = 0.152 on 100 samples
    # distil_with_lm.compute_wer()

    # base_no_lm = TestWav2Vec2(model_name=MODELS["base"],lm_path=None) # WER = 0.120 on 100 samples
    # base_no_lm.compute_wer()
    # base_with_lm = TestWav2Vec2(model_name=MODELS["base"],lm_path=LM) # WER = 0.081 on 100 samples
    # base_with_lm.compute_wer()

    # large_no_lm = TestWav2Vec2(model_name=MODELS["large"],lm_path=None) # WER = 0.101 on 100 samples
    # large_no_lm.compute_wer()
    # large_with_lm = TestWav2Vec2(model_name=MODELS["large"],lm_path=LM) # WER = 0.068 on 100 samples
    # large_with_lm.compute_wer()