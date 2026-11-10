import os
import shutil
import tempfile
import threading
import uuid
from datetime import datetime
from pathlib import Path

import numpy as np
import soundcard as sc
import sounddevice as sd
import soundfile as sf
from PySide6.QtCore import QObject, Signal

from audio.transcriber import transcribe_local


class AudioController(QObject):
    recording_changed = Signal(bool)
    transcript_ready = Signal(str)
    window_visibility_toggle_requested = Signal()
    error = Signal(str)

    SAMPLE_RATE = 48000
    LOOPBACK_BLOCKSIZE = 8192
    LOOPBACK_READ_FRAMES = 2048

    def __init__(self, project_root=None):
        super().__init__()
        self.root = Path(project_root or Path(__file__).resolve().parents[1])
        self.temp_root = Path(tempfile.gettempdir())
        self._cleanup_stale_sessions()

        self._lock = threading.RLock()
        self._recording = False
        self._mic_stream = None
        self._mic_frames = []
        self._loopback_frames = []
        self._loopback_thread = None
        self._loopback_stop = threading.Event()
        self._loopback_ready = threading.Event()
        self._loopback_error = None
        self._session_dir = None
        self._mic_path = None
        self._system_path = None
        self._listener = None
        self.selected_input_device = None

    def _cleanup_stale_sessions(self):
        for folder in self.temp_root.glob("interview-copilot-audio-*"):
            try:
                owner_pid = int(folder.name.split("-")[3])
                if owner_pid == os.getpid():
                    continue
                try:
                    os.kill(owner_pid, 0)
                except ProcessLookupError:
                    shutil.rmtree(folder, ignore_errors=True)
                except PermissionError:
                    continue
            except (ValueError, IndexError, OSError):
                continue

    @property
    def is_recording(self):
        with self._lock:
            return self._recording

    def list_input_devices(self):
        devices = sd.query_devices()
        default_input = sd.default.device[0]
        available = []
        for index, device in enumerate(devices):
            if int(device.get("max_input_channels", 0)) > 0:
                available.append((index, device["name"], index == default_input))
        return available

    def set_input_device(self, device_index=None):
        if self.is_recording:
            raise RuntimeError("Stop recording before changing the microphone.")
        self.selected_input_device = device_index

    def start_hotkey_listener(self):
        try:
            from pynput import keyboard

            hotkeys = {
                "<ctrl>+<alt>+r": self.toggle_recording,
                "<ctrl>+<alt>+h": self.window_visibility_toggle_requested.emit,
            }
            self._listener = keyboard.GlobalHotKeys(hotkeys)
            self._listener.daemon = True
            self._listener.start()
        except Exception as exc:
            self.error.emit(
                "Global shortcuts are unavailable. Use the in-app buttons. " + str(exc)
            )

    def _capture_loopback(self, loopback_microphone):
        try:
            with loopback_microphone.recorder(
                samplerate=self.SAMPLE_RATE,
                channels=2,
                blocksize=self.LOOPBACK_BLOCKSIZE,
            ) as recorder:
                self._loopback_ready.set()
                while not self._loopback_stop.is_set():
                    data = recorder.record(numframes=self.LOOPBACK_READ_FRAMES)
                    if data is not None and len(data):
                        self._loopback_frames.append(
                            np.asarray(data, dtype=np.float32).copy()
                        )
        except Exception as exc:
            self._loopback_error = str(exc)
            self._loopback_ready.set()

    @staticmethod
    def _default_loopback_microphone():
        """Resolve the loopback endpoint using SoundCard's speaker mapping."""
        speaker = sc.default_speaker()
        if speaker is None:
            raise RuntimeError(
                "Windows has no default playback device. Select an output device "
                "in Settings > System > Sound, then retry."
            )

        # SoundCard associates loopback microphones with speaker IDs. Name
        # matching is retained as a fallback for drivers exposing different IDs.
        microphones = sc.all_microphones(include_loopback=True)
        speaker_id = str(getattr(speaker, "id", "") or "")
        candidates = []
        for microphone in microphones:
            if not getattr(microphone, "isloopback", False):
                continue
            microphone_id = str(getattr(microphone, "id", "") or "")
            if speaker_id and microphone_id == speaker_id:
                return microphone
            if getattr(microphone, "name", None) == getattr(speaker, "name", None):
                candidates.append(microphone)

        if candidates:
            return candidates[0]

        # Older SoundCard/driver combinations can expose the speaker name as
        # the loopback endpoint ID even when the ID fields do not match.
        try:
            return sc.get_microphone(
                id=str(speaker.name),
                include_loopback=True,
            )
        except Exception as exc:
            raise RuntimeError(
                "Could not find a WASAPI loopback endpoint for the default "
                f"speaker '{speaker.name}'. You can still record microphone audio. "
                "Check the Windows output device and try again. Details: " + str(exc)
            ) from exc

    def start_recording(self):
        with self._lock:
            if self._recording:
                return
            self._recording = True

        self._mic_frames = []
        self._loopback_frames = []
        self._loopback_error = None
        self._loopback_stop.clear()
        self._loopback_ready.clear()

        try:
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            self._session_dir = Path(tempfile.mkdtemp(
                prefix=f"interview-copilot-audio-{os.getpid()}-{uuid.uuid4().hex[:8]}-",
                dir=self.temp_root,
            ))
            self._mic_path = self._session_dir / (stamp + "-mic.wav")
            self._system_path = self._session_dir / (stamp + "-system.wav")

            # Start microphone capture first. A loopback problem must not prevent
            # the user from recording their own voice.
            try:
                self._mic_stream = sd.InputStream(
                    device=self.selected_input_device,
                    samplerate=self.SAMPLE_RATE,
                    channels=1,
                    dtype="int16",
                    callback=self._mic_callback,
                )
                self._mic_stream.start()
            except Exception as exc:
                raise RuntimeError(
                    "Could not start microphone capture. Check Windows microphone "
                    "privacy permissions and the selected input device. Details: "
                    + str(exc)
                ) from exc

            # System loopback is optional: keep recording the microphone if the
            # Windows audio driver does not expose a compatible WASAPI endpoint.
            try:
                loopback = self._default_loopback_microphone()
                self._loopback_thread = threading.Thread(
                    target=self._capture_loopback,
                    args=(loopback,),
                    name="WindowsSystemAudioCapture",
                    daemon=True,
                )
                self._loopback_thread.start()

                if not self._loopback_ready.wait(timeout=12):
                    raise RuntimeError(
                        "Timed out starting Windows system-audio capture. "
                        "Check that a default output device is selected."
                    )
                if self._loopback_error:
                    raise RuntimeError(self._loopback_error)
            except Exception as exc:
                self._loopback_error = str(exc)
                self._loopback_stop.set()
                if self._loopback_thread is not None:
                    self._loopback_thread.join(timeout=2)
                    self._loopback_thread = None
                self.error.emit(
                    "System audio is unavailable; microphone recording will continue. "
                    + self._loopback_error
                )

            self.recording_changed.emit(True)
        except Exception as exc:
            self._cleanup_capture()
            self._remove_session_files()
            with self._lock:
                self._recording = False
            self.error.emit(str(exc))

    def _mic_callback(self, indata, frames, timing, status):
        if status:
            pass
        self._mic_frames.append(indata.copy())

    def stop_recording(self):
        with self._lock:
            if not self._recording:
                return
            self._recording = False

        self._cleanup_capture()
        self.recording_changed.emit(False)

        mic_path = self._mic_path
        system_path = self._system_path
        session_dir = self._session_dir
        self._mic_path = None
        self._system_path = None
        self._session_dir = None

        threading.Thread(
            target=self._transcribe,
            args=(mic_path, system_path, session_dir, self._loopback_error),
            name="LocalWhisperTranscription",
            daemon=True,
        ).start()

    def _cleanup_capture(self):
        if self._mic_stream is not None:
            try:
                self._mic_stream.stop()
                self._mic_stream.close()
            except Exception:
                pass
            self._mic_stream = None

        self._loopback_stop.set()
        if self._loopback_thread is not None:
            self._loopback_thread.join(timeout=10)
            self._loopback_thread = None

        if self._mic_frames and self._mic_path:
            try:
                sf.write(
                    str(self._mic_path),
                    np.concatenate(self._mic_frames, axis=0),
                    self.SAMPLE_RATE,
                    subtype="PCM_16",
                )
            except Exception as exc:
                self.error.emit("Could not save microphone audio: " + str(exc))
        self._mic_frames = []

        if self._loopback_frames and self._system_path:
            try:
                sf.write(
                    str(self._system_path),
                    np.concatenate(self._loopback_frames, axis=0),
                    self.SAMPLE_RATE,
                    subtype="PCM_16",
                )
            except Exception as exc:
                self.error.emit("Could not save system audio: " + str(exc))
        self._loopback_frames = []

    def _remove_session_files(self):
        folder = self._session_dir
        self._session_dir = None
        self._mic_path = None
        self._system_path = None
        if folder is not None:
            shutil.rmtree(folder, ignore_errors=True)

    def _transcribe(self, mic_path, system_path, session_dir, loopback_error=None):
        try:
            results = []
            if mic_path and mic_path.exists() and mic_path.stat().st_size > 44:
                mic_text = transcribe_local(mic_path)
                if mic_text:
                    results.append("[YOU / MICROPHONE]\n" + mic_text)
            if system_path and system_path.exists() and system_path.stat().st_size > 44:
                system_text = transcribe_local(system_path)
                if system_text:
                    results.append("[OTHER PARTICIPANTS / SYSTEM AUDIO]\n" + system_text)

            transcript = "\n\n".join(results).strip()
            if not transcript:
                detail = (
                    " System-audio detail: " + loopback_error
                    if loopback_error else ""
                )
                raise RuntimeError(
                    "No speech was transcribed. Check Windows microphone privacy "
                    "settings, selected input/output devices and audio levels."
                    + detail
                )
            if loopback_error:
                self.error.emit(
                    "System audio capture was unavailable; the microphone transcript "
                    "is still available. " + loopback_error
                )
            self.transcript_ready.emit(transcript)
        except Exception as exc:
            self.error.emit("Local transcription failed: " + str(exc))
        finally:
            if session_dir is not None:
                shutil.rmtree(session_dir, ignore_errors=True)

    def toggle_recording(self):
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def shutdown(self):
        if self.is_recording:
            self.stop_recording()
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None
