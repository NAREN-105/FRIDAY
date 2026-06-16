# F.R.I.D.A.Y. - AI Assistant

![FRIDAY](https://img.shields.io/badge/AI-F.R.I.D.A.Y.-00d4ff?style=for-the-badge&logo=python&logoColor=white)

F.R.I.D.A.Y. (Female Replacement Intelligent Digital Assistant Youth) is a fully autonomous, voice-controlled desktop AI assistant built in Python. Inspired by the Iron Man movies, it features a beautifully animated, transparent HUD (Heads-Up Display) built with Tkinter, advanced voice activity detection (VAD), and system-level automation powered by Google Gemini 2.5 Flash.

## ✨ Features

- **Voice Activation:** Always listening for the wake word **"Friday"** using a custom VAD loop.
- **Conversational AI:** Powered by Google's `gemini-2.5-flash` model for intelligent, natural, and highly contextual responses with a custom personality.
- **System Automation:** Can open Windows applications, type on the screen, press hotkeys, scroll, and take screenshots using `pyautogui`.
- **Web Navigation & Research:** Searches the web, opens specific URLs, fetches the latest news, and retrieves real-time weather updates.
- **Smart Shopping:** Automatically searches and compares product prices across Amazon India, Flipkart, Snapdeal, and Google Shopping.
- **Animated HUD:** A custom, frameless Tkinter UI with dynamic visual states (`STANDBY`, `LISTENING`, `PROCESSING`, `SPEAKING`), a rotating radar, and a conversation log.
- **Task Management:** Set voice-based reminders that alert you automatically.


## 🛠️ Technology Stack
- **Core AI:** `google-genai` (Gemini API)
- **Speech-to-Text:** `SpeechRecognition`, `sounddevice`, `soundfile`, `numpy`
- **Text-to-Speech:** `pyttsx3`
- **Automation:** `pyautogui`, `webbrowser`
- **UI:** `tkinter`

## ⚙️ Installation & Setup


1. **Clone the repository:**
   ```bash
   git clone https://github.com/NAREN-105/FRIDAY.git
   cd FRIDAY
   ```

2. **Create a virtual environment (Optional but recommended):**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your API Key:**
   Create a `.env` file in the root directory and add your Google Gemini API key:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

## 🚀 Usage

Run the main application script to boot up F.R.I.D.A.Y.:

```bash
python main.py
```

 
- **Activation:** The UI will launch in the bottom right corner of your screen. Wait for the "Awaiting Boss..." status, then say **"Friday"** (or "Hi Friday") to wake her up.
- **Commands:** Once active, you can issue commands like:
  - *"Open Chrome"*
  - *"What's the weather in London?"*
  - *"Find the best price for a MacBook Pro"*
  - *"Take a screenshot"*
  - *"Set a reminder to check the oven in 10 minutes"*
- **Exit:** Say **"Bye Friday"** / **"Shutdown"**, or simply right-click anywhere on the UI to close the application.

## 📝 License
This project is created for educational and personal use.
