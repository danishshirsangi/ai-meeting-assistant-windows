# Windows audio capture

The Windows build captures two separate sources:

- Microphone input with PortAudio through `sounddevice`.
- Default speaker output through Windows WASAPI loopback with `SoundCard`.

Both tracks are written to temporary WAV files and transcribed locally with `faster-whisper`. Temporary recordings are deleted after transcription. Only the resulting text transcript is passed to the Gemini answer-generation workflow.

The current workflow is record → stop → local transcription → answer generation. It is not continuous live question detection. The default system output device is used for loopback capture when available; microphone recording does not depend on loopback.

Shortcuts: `Ctrl + Alt + R` to start/stop recording and `Ctrl + Alt + H` to hide/restore the window.
