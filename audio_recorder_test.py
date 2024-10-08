import sys
import os
import time
import sounddevice as sd
import numpy as np
from scipy.io import wavfile
import whisper
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QVBoxLayout,
    QTextEdit,
    QProgressDialog,
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt


class AudioRecorder(QThread):
    finished = pyqtSignal(str, float)

    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        self.is_recording = False
        self.start_time = None

    def run(self):
        RATE = 16000  # 16kHz to match Whisper's expected input
        self.is_recording = True
        self.start_time = time.time()
        with sd.InputStream(samplerate=RATE, channels=1) as stream:
            frames = []
            while self.is_recording:
                data, overflowed = stream.read(RATE)
                if not overflowed:
                    frames.append(data)

        audio_data = np.concatenate(frames, axis=0)
        print(f"Raw audio data shape: {audio_data.shape}")
        print(f"Raw audio data range: {audio_data.min()} to {audio_data.max()}")

        # Ensure audio data is in the correct range for int16
        audio_data = np.clip(audio_data * 32768, -32768, 32767).astype(np.int16)

        wavfile.write(self.filename, RATE, audio_data)
        end_time = time.time()
        self.finished.emit(self.filename, end_time - self.start_time)

    def stop(self):
        self.is_recording = False


class AudioRecorderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.recorder = None
        self.is_recording = False
        print("Loading Whisper model...")
        self.whisper_model = whisper.load_model("tiny")
        print("Whisper model loaded.")

    def initUI(self):
        layout = QVBoxLayout()

        # Record button
        self.record_button = QPushButton("Record", self)
        self.record_button.clicked.connect(self.toggle_recording)
        self.record_button.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                font-size: 16px;
                margin: 4px 2px;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """
        )
        layout.addWidget(self.record_button)

        # Text entry field
        self.text_entry = QTextEdit(self)
        self.text_entry.setPlaceholderText("Transcribed text will appear here...")
        layout.addWidget(self.text_entry)

        self.setLayout(layout)
        self.setGeometry(300, 300, 300, 200)
        self.setWindowTitle("Audio Recorder")
        self.show()

    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        self.is_recording = True
        self.record_button.setText("Stop Recording")
        self.record_button.setStyleSheet(
            """
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                font-size: 16px;
                margin: 4px 2px;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """
        )
        filename = os.path.expanduser("~/recorded_audio.wav")
        self.recorder = AudioRecorder(filename)
        self.recorder.finished.connect(self.on_recording_finished)
        self.recorder.start()

    def stop_recording(self):
        if self.recorder:
            print(f"Stop recording clicked at: {time.time():.2f}")
            self.recorder.stop()
        self.is_recording = False
        self.record_button.setText("Record")
        self.record_button.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                font-size: 16px;
                margin: 4px 2px;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """
        )

    def on_recording_finished(self, filename, recording_duration):
        print(f"Recording saved to: {filename}")
        print(f"Total recording time: {recording_duration:.2f} seconds")
        transcription_start = time.time()
        self.transcribe_audio(filename)
        transcription_end = time.time()
        print(
            f"Total time from recording stop to transcription complete: {transcription_end - transcription_start:.2f} seconds"
        )

    def transcribe_audio(self, filename):
        progress = QProgressDialog("Transcribing audio...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("Please Wait")
        progress.setCancelButton(None)
        progress.setMinimumDuration(0)
        progress.show()

        QApplication.processEvents()

        print("Transcribing audio...")
        read_start = time.time()
        # Read the WAV file
        sample_rate, audio_data = wavfile.read(filename)
        read_end = time.time()
        print(f"Time to read WAV file: {read_end - read_start:.2f} seconds")

        print(f"Audio shape: {audio_data.shape}, Sample rate: {sample_rate}")
        print(f"Audio duration: {len(audio_data) / sample_rate:.2f} seconds")

        # Convert to float32 and normalize
        audio_data = audio_data.astype(np.float32) / 32768.0

        print(f"Audio data range: {audio_data.min()} to {audio_data.max()}")

        # Transcribe
        transcribe_start = time.time()
        result = self.whisper_model.transcribe(audio_data)
        transcribe_end = time.time()
        transcribed_text = result["text"].strip()  # Remove leading/trailing whitespace
        print(f"Transcription: {transcribed_text}")
        print(
            f"Time for Whisper to transcribe: {transcribe_end - transcribe_start:.2f} seconds"
        )
        print("Transcription complete.")

        # Insert transcribed text into the text entry field
        current_text = self.text_entry.toPlainText()
        if current_text:
            new_text = current_text + " " + transcribed_text
        else:
            new_text = transcribed_text
        self.text_entry.setPlainText(new_text)

        # Move cursor to the end of the text
        cursor = self.text_entry.textCursor()
        cursor.movePosition(cursor.End)
        self.text_entry.setTextCursor(cursor)

        progress.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = AudioRecorderApp()
    sys.exit(app.exec_())
