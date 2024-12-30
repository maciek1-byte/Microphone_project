import sys
import os
import wave
import time

from threading import Thread, Event, Timer
import pyaudio
from PyQt6 import QtCore, QtWidgets, uic
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer, QTime
from PyQt6.QtWidgets import QMessageBox, QFileDialog
from funkcje import recording, list_audio_devices, playing_recorded

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), './recording_app.ui'))

class RecordingApp(QtWidgets.QMainWindow, FORM_CLASS):
    def __init__(self, parent=None):
        super(RecordingApp, self).__init__(parent)
        self.setupUi(self)

        self.progressBar.setValue(0)
        self.timer = QTimer(self)
        self.progress_timer = QTimer(self)
        self.playback_timer = QTimer(self)  # Timer for countdown during playback

        self.replay_stopped = False
        self.recording_stopped = False
        self.recording_active = False
        self.playback_active = False
        self.stop_flag = False
        self.rec_time = QTime(0, 0, 0)

        self.audio_devices = list_audio_devices()
        self.frames = []

        # Button connections
        self.pushButtonNagrywaj.clicked.connect(self.start_recording)
        self.pushButtonNagrywaj.clicked.connect(self.changing_icon_record)
        
        self.pushButtonWstrzymaj.clicked.connect(self.stop_recording)
        self.pushButtonWstrzymaj.clicked.connect(self.stop_playback)
        
        self.pushButtonZapisz.clicked.connect(self.save_recording)
        self.pushButtonOdtworz.clicked.connect(self.start_playback)

        # Timer connections
        self.timer.timeout.connect(self.update_timer_display)
        self.progress_timer.timeout.connect(self.update_bar_display)
        self.playback_timer.timeout.connect(self.update_playback_timer)

        
    def start_recording(self):
        if not self.recording_active:
            self.recording_active = True
            self.stop_flag = False
            self.rec_time = QTime(0, 0, 0)
            self.frames = []

            self.timer.start(1000)
            self.progress_timer.start(100)

            self.record_thread = Thread(target=self.run_recording, daemon=True)
            self.record_thread.start()

    def run_recording(self):
        try:
            recording(self.frames, self.check_flag)
        except Exception as e:
            self.show_error_message(f"Error during recording: {e}")

    def check_flag(self):
        return self.stop_flag

    def check_stopped(self):
        return self.recording_stopped
    def return_time(self):
        return self.timer
    def return_progress_timer(self):
        return self.progress_timer
    def stop_recording(self):
        if self.recording_active:
            self.time = self.return_time()
            self.progress_timer = self.return_progress_timer()
            self.recording_stopped = True
            self.recording_active = False
            self.stop_flag = True
            self.timer.stop()
            self.progress_timer.stop()
            self.thread = Thread(target=self.stop_recording, daemon= True)
            self.thread.start()
            if self.record_thread and self.record_thread.is_alive():
                #while self.recording_stopped:
                    self.record_thread.join(timeout=1)
                    #self.timer_interval = Thread.Timer(1, self.check_stopped)
                    #self.timer_interval.start()
                    #self.record_thread.join
        #else:
            #self.timer_interval.cancel()            
            #self.recording_stopped = False
            #self.stop_flag = False
            
                    

    def save_recording(self):
        if not self.frames:
            self.show_error_message("No recording data available to save.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, 'Save File', '', 'WAV files (*.wav)')
        if file_path:
            if not file_path.endswith('.wav'):
                file_path += '.wav'

            try:
                with wave.open(file_path, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
                    wf.setframerate(44100)
                    wf.writeframes(b''.join(self.frames))
                self.show_info_message(f"Recording saved to {file_path}")
            except Exception as e:
                self.show_error_message(f"Error saving file: {e}")

    def start_playback(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Open File', '', 'WAV files (*.wav)')
        if file_path:
            try:
                duration = playing_recorded(file_path) 
                self.rec_time = QTime(0, 0, 0).addSecs(duration)    
                self.labelTime.setText(self.rec_time.toString("hh:mm:ss"))
            
                self.playback_active = True
                self.playback_timer.start(1000)  # Updating

                self.play_audio(file_path)
                
            except Exception as e:
                self.show_error_message(f"Playback error: {e}")
    def play_audio(self, file_path):
        try:
            CHUNK = 1024
            with wave.open(file_path, 'rb') as wf:
                p = pyaudio.PyAudio()
                stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                                channels=wf.getnchannels(),
                                rate=wf.getframerate(),
                                output=True)

                data = wf.readframes(CHUNK)

                self.playback_active = True
                self.rec_time = QTime(0, 0, 0).addSecs(int(wf.getnframes() / wf.getframerate()))
                self.labelTime.setText(self.rec_time.toString("hh:mm:ss"))
                self.playback_timer.start(1000)

                while data and self.playback_active:
                    stream.write(data)
                    data = wf.readframes(CHUNK)
                    QtCore.QCoreApplication.processEvents()

                self.playback_active = False
                self.playback_timer.stop()
                self.labelTime.setText(QTime(0, 0, 0).toString("hh:mm:ss"))

                stream.stop_stream()
                stream.close()
                p.terminate()

        except Exception as e:
            self.show_error_message(f"Error during playback: {e}")


    def update_timer_display(self):
        if self.recording_active:
            self.rec_time = self.rec_time.addSecs(1)
            self.labelTime.setText(self.rec_time.toString("hh:mm:ss"))

    def update_playback_timer(self):
        if self.rec_time > QTime(0, 0, 0):
            self.rec_time = self.rec_time.addSecs(-1)
            self.labelTime.setText(self.rec_time.toString("hh:mm:ss"))
        else:
            self.playback_timer.stop()
            self.playback_active = False

    def update_bar_display(self):
        if self.recording_active:
            current_value = self.progressBar.value()
            self.progressBar.setValue((current_value + 1) % 100)

    def show_error_message(self, message):
        QMessageBox.critical(self, "Error", message)

    def show_info_message(self, message):
        QMessageBox.information(self, "Information", message)
        
    def changing_icon_record(self):
        self.pushButtonNagrywaj.setIcon(QIcon("./images/buttoRecordOn.png"))
    def stop_playback(self):
        if self.playback_active and not self.replay_stopped: 
            self.playback_timer.stop()
            self.playback_active = False
            self.rec_time = QTime(0, 0, 0)
            self.labelTime.setText(QTime(0, 0, 0).toString("hh:mm:ss"))
            self.replay_stopped = True
            self.pushButtonWstrzymaj.setIcon(QIcon("./images/buttoStop.png"))
        elif self.replay_stopped:
            self.replay_stopped = False
            self.pushButtonWstrzymaj.setIcon(QIcon("./images/buttonstart.png"))

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = RecordingApp()
    window.show()
    sys.exit(app.exec())
