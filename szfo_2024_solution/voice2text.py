import json
import os
import sys
from pathlib import Path

import nltk
from rnnoise_wrapper import RNNoise
from vosk import KaldiRecognizer, Model

from .label2id import _id2label, _label2id


class VoskASR:
    def __init__(self, model_path: Path, chunk_size=4000, frame_rate=16000):
        if not os.path.exists(model_path):
            print("Model not found at:", model_path)
            sys.exit(1)
        model = Model(str(model_path))
        self.recognizer = KaldiRecognizer(model, frame_rate)
        self.denoiser = RNNoise()
        self.chunk_size = chunk_size

    def read_audio(self, audio_path: Path) -> None:
        self.audio = self.denoiser.read_wav(audio_path)

    def denoise_audio(self) -> None:
        self.audio = self.denoiser.filter(self.audio)

    def recognize_audio(self) -> str:
        transcription = ""

        for start in range(0, len(self.audio), self.chunk_size):
            end = min(start + self.chunk_size, len(self.audio))
            chunk = self.audio[start:end]

            raw_data = chunk.raw_data

            if self.recognizer.AcceptWaveform(raw_data):
                result = self.recognizer.Result()
                transcription += json.loads(result)["text"] + " "

        transcription += json.loads(self.recognizer.FinalResult())["text"]
        self.transcription = transcription
        return transcription

    @property
    def get_transcription(self):
        return self.transcription

    @property
    def get_pred_label(self):
        return self.predict_label_from_text(self.transcription)

    @property
    def get_pred_attr(self):
        return -1

    def predict_label_from_text(self, text):
        pred_id = None
        try:
            pred_id = self.label2id(text)
        except KeyError:
            pred_id = -1
        return pred_id

    @staticmethod
    def label2id(label: str) -> int:
        return _label2id[label]

    @staticmethod
    def id2label(id: int) -> str:
        return _id2label[id]


class MetricsCalculator:
    def __init__(self):
        pass

    def wer(test, pred):
        test_words = test.split()
        pred_words = pred.split()
        matcher = nltk.edit_distance(test_words, pred_words)
        return matcher / len(test_words)