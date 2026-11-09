# AI Meeting Assistant — Windows

A Windows desktop port of the AI Meeting Assistant. It combines resume-grounded question answering with microphone and system-audio recording.

The Windows repository is maintained separately from the [macOS application](https://github.com/danishshirsangi/ai-assistant). The two versions share the Gemini client, resume RAG, answer-generation logic and main Qt interface where practical. Their operating-system integrations and local audio/transcription dependencies are separate.

## Features

- PySide6 desktop interface.
- Upload resumes in PDF, DOCX, TXT and Markdown formats.
- Gemini Embedding API creates resume embeddings; local SQLite stores text chunks and vectors.
- Typed questions use semantic retrieval to ground Gemini answers in the uploaded resume.
- Record microphone and Windows speaker output using WASAPI loopback.
- Transcribe both tracks locally with faster-whisper.
- Stream generated answers into the UI and revisit previous questions during the current session.
- Global shortcuts: `Ctrl + Alt + R` to record/stop and `Ctrl + Alt + H` to hide/restore the window.
- Best-effort Windows capture exclusion using `SetWindowDisplayAffinity`.

## Audio workflow and limitations

The current workflow is **record → stop → transcribe locally → send transcript/context to Gemini → display answer**. It does not continuously detect each interviewer question during an active recording. One recording session creates one transcript and one generated answer; long recordings are not yet segmented into individual question/answer entries.

The default Windows playback device is used for system-audio loopback. Select the intended Windows output device before recording. Microphone and system audio are written to temporary WAV files and deleted after transcription. The transcript, typed question, conversation context and retrieved resume excerpts are sent to Gemini for answer generation. Review Google's current API terms and your organisation's data policy before sending sensitive information.

Capture exclusion is best-effort and is not a security boundary. Some recording and screen-sharing applications may behave differently.

## Requirements

- Windows 10 (Windows 10 version 2004 or later recommended for capture exclusion) or Windows 11, 64-bit.
- Python 3.12, 64-bit.
- Internet access for dependency installation, Gemini requests and the first Whisper model download.
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/api-keys).
- A working microphone and audio output device for audio capture.

Xcode, Swift, Homebrew, MLX, Ollama, ChromaDB, ONNX Runtime and a separately installed FFmpeg are not required for this Windows build.

## Installation

Open **PowerShell** and run the following commands.

### 1. Install Python 3.12

Install 64-bit Python 3.12 from [python.org](https://www.python.org/downloads/windows/). During setup, enable **Add Python to PATH**.

Verify:

```powershell
py -3.12 --version
```

### 2. Clone the Windows repository

```powershell
git clone https://github.com/danishshirsangi/ai-meeting-assistant-windows.git
cd ai-meeting-assistant-windows
```

The active development branch is currently `mybranch`. Switch to it when required:

```powershell
git checkout mybranch
```

### 3. Create and activate a virtual environment

```powershell
py -3.12 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python --version
```

If PowerShell activation is blocked by your organisation's policy, use Command Prompt instead:

```bat
.venv\Scripts\activate.bat
```

### 4. Install dependencies

```powershell
python -m pip install --upgrade pip wheel setuptools
python -m pip install -r requirements.txt
python -m pip install -r requirements-audio-windows.txt
```

The audio dependencies include faster-whisper and CTranslate2, so installation may download sizeable packages.

### 5. Configure Gemini

Create the local environment file:

```powershell
Copy-Item .env.example .env
notepad .env
```

Replace `your_google_ai_studio_api_key` with your own Gemini API key. Keep the configured model names unless you intentionally want to use another model supported by your API project.

**Never commit or share `.env`.** It is excluded by `.gitignore`. If a key is exposed, revoke it in Google AI Studio and create a new one.

### 6. Test the Gemini connection

```powershell
python diagnostics\gemini_smoke_test.py
```

The diagnostic checks API-key loading, chat-model access, embeddings and a short generation request. Resolve API or quota errors before troubleshooting audio.

### 7. Launch

```powershell
python main.py
```

The first transcription downloads the `base` faster-whisper model from Hugging Face and caches it locally. Internet access is required for the first download; subsequent runs use the cached model.

## Windows permissions and audio setup

Open **Settings → Privacy & security → Microphone** and enable microphone access for desktop apps. Check that the correct devices are selected:

- **Input:** Windows Settings → System → Sound → Input.
- **Output:** Windows Settings → System → Sound → Output.

The app records the default output device using WASAPI loopback. If system audio is silent, confirm that the intended output device is selected and that audio is playing through it. Some virtual audio devices, Bluetooth routes and exclusive-mode configurations may behave differently.

Global shortcuts may be blocked by security software or another app that has registered the same combination. The on-screen buttons remain available.

## How to use it

### Ask a typed question

1. Click **Upload resume** and select a PDF, DOCX, TXT or MD file.
2. Wait for the resume-indexing confirmation.
3. Type a question in the composer.
4. Click **Generate answer** or press Enter.
5. Select an earlier question in the left panel to revisit its answer.

The local index is stored at:

```text
vector_db_gemini/resume_vectors.sqlite3
```

The database contains extracted text chunks and their embeddings, not a copy of the original resume. Resume text is sent to Gemini when embeddings are created.

### Record a meeting

- Press `Ctrl + Alt + R` or click **Start recording**.
- Speak into the selected microphone while meeting participants speak through the default Windows output device.
- Press `Ctrl + Alt + R` again or click **Stop recording**.
- Wait for local transcription and Gemini answer generation.

### Hide and restore the window

- Press `Ctrl + Alt + H` or click **Hide window**.
- Press `Ctrl + Alt + H` again to restore it.

Hiding the window does not stop an active recording.

### Capture privacy

Use **Capture privacy** to request Windows display-affinity exclusion for the main window. This feature depends on Windows version and capture API support. It is not guaranteed in every app; do not treat it as a security control.

### Clear a session

**Clear session** removes the visible question list, generated answers and in-memory conversation context. It does not delete the saved resume index or API key.

## Project structure

```text
ai-meeting-assistant-windows/
├── audio/
│   ├── controller.py
│   └── transcriber.py
├── assets/
├── core/
│   ├── answer_generator.py
│   ├── document_loader.py
│   ├── gemini_client.py
│   ├── prompts.py
│   └── resume_rag.py
├── diagnostics/
│   └── gemini_smoke_test.py
├── tests/
├── ui/
│   ├── main_window.py
│   ├── rich_text.py
│   ├── windows_window_privacy.py
│   └── worker.py
├── .env.example
├── main.py
├── requirements.txt
└── requirements-audio-windows.txt
```

## Troubleshooting

**Gemini API key missing**

Check that `.env` is in the repository root and contains a valid `GEMINI_API_KEY=...` value. Restart the app after editing it.

**Gemini unavailable**

Run `python diagnostics\gemini_smoke_test.py`. Check internet access, API-key validity, model availability and project quotas.

**No microphone listed**

Check Windows microphone privacy settings, reconnect the input device, and click **Refresh** in the app.

**System audio did not start**

Check that Windows has a default output device. Play audio through that device and retry. As a comparison, test with built-in speakers if you are using Bluetooth or a virtual audio driver.

**Transcription dependency/model error**

Activate the project virtual environment and run:

```powershell
python -m pip install -r requirements-audio-windows.txt
```

Ensure the first model download can reach Hugging Face. The model cache normally does not need to be cleared.

**Global shortcuts do not work**

Use the on-screen controls and check whether another application or security tool is intercepting `Ctrl + Alt + R` or `Ctrl + Alt + H`.

## Development checks

Run from the repository root:

```powershell
python -m pytest
python -m compileall -q .
```

A Windows GitHub Actions workflow runs these checks on pushes and pull requests.

## Privacy notes

- Audio transcription runs locally with faster-whisper.
- Temporary WAV files are removed after transcription.
- Resume text is sent to Gemini when embeddings are created.
- Typed questions, transcripts, conversation context and retrieved resume excerpts are sent to Gemini to generate answers.
- The SQLite resume index stays on the local machine.
- Review Google's current Gemini API pricing, data-use terms and your organisation's requirements before using confidential or personal information.

## Roadmap

- Validate audio devices and capture behavior on Windows 10/11 hardware.
- Add an installer and signed Windows executable.
- Improve long-recording segmentation and question-level audio processing.
- Add selection for system loopback sources.
- Expand Windows hardware integration tests.
