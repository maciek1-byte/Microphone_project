import wave
import pyaudio
import contextlib
from  PyQt6 import QtWidgets
from PyQt6.QtCore import QTime
from PyQt6.QtWidgets import QFileDialog, QMessageBox



def playing_recorded(file_path):
    try:
        with contextlib.closing(wave.open(file_path, 'r')) as file:
            frames = file.getnframes()
            rate = file.getframerate()
            duration = int(frames / float(rate))  # Return duration in seconds
            return duration
    except Exception as e:
        raise Exception(f"Error calculating duration: {e}")



def recording(frames, stop_callback):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    DEVICE_INDEX = 1

    p = pyaudio.PyAudio()

    try:
        if DEVICE_INDEX >= p.get_device_count() or DEVICE_INDEX < 0:
            raise ValueError(f"Invalid DEVICE_INDEX: {DEVICE_INDEX}")

        stream = p.open(format=FORMAT, 
                        channels=CHANNELS, 
                        rate=RATE, 
                        input=True, 
                        input_device_index=DEVICE_INDEX, 
                        frames_per_buffer=CHUNK)

        print(f"Recording started on device {DEVICE_INDEX}")

        while not stop_callback():
            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)
            except Exception as e:
                print(f"Error reading audio data: {e}")
                break

        print("Recording finished")

    except Exception as e:
        print(f"Error during recording setup or processing: {e}")

    finally:
        try:
            stream.stop_stream()
            stream.close()
        except Exception as e:
            print(f"Error closing stream: {e}")

        p.terminate()
        print("Audio resources released.")

def open_from_dektop(parent):
    file_path, _ = QFileDialog.getOpenFileName(parent, 'Open File', '', 'WAV files (*.wav)')
    if file_path:
        playing_recorded(file_path)

def reset(parent, element):
    time_reset = QTime(0, 0, 0)
    element.setText(time_reset.toString("hh:mm:ss"))

def update_time(parent, element):
    parent.rec_time = parent.rec_time.addSecs(1)
    element.setText(parent.rec_time.toString("hh:mm:ss"))

def list_audio_devices():
    p = pyaudio.PyAudio()
    print("Available audio devices:")
    devices = []
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        devices.append(info['name'])
        print(f"Index {i}: {info['name']} (Input Channels: {info['maxInputChannels']})")
    p.terminate()
    return devices