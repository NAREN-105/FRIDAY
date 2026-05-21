import os
import time
import random
import webbrowser
import pyautogui
import urllib.parse
import threading
from dotenv import load_dotenv

try:
    from google import genai
    from google.genai import types
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

load_dotenv()

_brain: "FridayBrain | None" = None   # global ref for tool callbacks

# ════════════════════════════════════════════════════════════════════════════
#  TOOLS
# ════════════════════════════════════════════════════════════════════════════

def search_web(query: str) -> str:
    """Opens a Google search for any topic, question, or piece of information."""
    webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(query)}")
    return f"Google opened for: {query}"


def open_website(url: str) -> str:
    """Opens any website directly — e.g. 'youtube.com', 'amazon.in', 'github.com'."""
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opened: {url}"


def open_application(app_name: str) -> str:
    """Opens a Windows desktop application by name — Notepad, Chrome, Spotify, etc."""
    pyautogui.press("win")
    time.sleep(0.6)
    pyautogui.write(app_name, interval=0.04)
    time.sleep(0.8)
    pyautogui.press("enter")
    return f"Launched: {app_name}"


def type_on_screen(text: str) -> str:
    """Types the given text at the current cursor position on screen."""
    time.sleep(0.5)
    pyautogui.write(text, interval=0.03)
    return f"Typed: {text}"


def press_key(key: str) -> str:
    """Presses a key or hotkey combo — e.g. 'enter', 'ctrl+c', 'alt+f4', 'ctrl+t'."""
    if "+" in key:
        pyautogui.hotkey(*key.split("+"))
    else:
        pyautogui.press(key)
    return f"Pressed: {key}"


def scroll_page(direction: str) -> str:
    """Scrolls the current page up or down."""
    pyautogui.scroll(400 if direction.lower() == "up" else -400)
    return f"Scrolled {direction}"


def search_product_prices(product_name: str) -> str:
    """
    Finds the best price for a product. Opens Amazon India, Flipkart, Snapdeal, and
    Google Shopping tabs, then returns an AI-powered spoken price comparison with
    store recommendations and better product alternatives.
    """
    global _brain
    for url in [
        f"https://www.google.com/search?q={urllib.parse.quote(product_name)}+price+india&tbm=shop",
        f"https://www.amazon.in/s?k={urllib.parse.quote(product_name)}",
        f"https://www.flipkart.com/search?q={urllib.parse.quote(product_name)}",
        f"https://www.snapdeal.com/search?keyword={urllib.parse.quote(product_name)}",
    ]:
        webbrowser.open_new_tab(url)
        time.sleep(0.35)

    if _brain and _brain.client:
        try:
            r = _brain.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=(
                    f"Find current prices for '{product_name}' in India on Amazon, Flipkart, Snapdeal. "
                    "Tell me: cheapest store and its price, and 2 better alternatives with prices. "
                    "Keep it under 80 words, warm and conversational."
                ),
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                ),
            )
            return r.text or f"Opened price comparison for {product_name}."
        except Exception as e:
            print(f"[Price search] {e}")

    return f"I've opened Amazon, Flipkart, Snapdeal, and Google Shopping for '{product_name}'."


def get_weather(city: str) -> str:
    """Gets real-time weather for any city or location."""
    webbrowser.open(f"https://www.google.com/search?q=weather+{urllib.parse.quote(city)}")
    global _brain
    if _brain and _brain.client:
        try:
            r = _brain.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"Current weather in {city}? Give a friendly 2-sentence spoken summary.",
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                ),
            )
            return r.text or f"Opened weather for {city}."
        except Exception as e:
            print(f"[Weather] {e}")
    return f"Opened weather for {city}."


def get_latest_news(topic: str) -> str:
    """Gets the latest news headlines on any topic."""
    webbrowser.open(f"https://news.google.com/search?q={urllib.parse.quote(topic)}")
    global _brain
    if _brain and _brain.client:
        try:
            r = _brain.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"Give me 3 latest headlines about '{topic}' in a brief, spoken friendly way.",
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                ),
            )
            return r.text or f"Opened news for {topic}."
        except Exception as e:
            print(f"[News] {e}")
    return f"Opened Google News for {topic}."


def set_reminder(task: str, minutes: int) -> str:
    """Sets a voice reminder after a given number of minutes."""
    def _remind():
        time.sleep(minutes * 60)
        if _brain:
            _brain.audio.speak(f"Hey Boss — reminder: {task}")
    threading.Thread(target=_remind, daemon=True).start()
    return f"Reminder set: '{task}' in {minutes} minute(s)."


def take_screenshot() -> str:
    """Takes a screenshot and saves it to the Desktop."""
    import datetime
    fname = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    path  = os.path.join(os.path.expanduser("~"), "Desktop", fname)
    pyautogui.screenshot(path)
    return f"Screenshot saved as {fname} on your Desktop."


# ════════════════════════════════════════════════════════════════════════════
#  PERSONALITY
# ════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """
You are F.R.I.D.A.Y. — Female Replacement Intelligent Digital Assistant Youth.
You are the personal AI of your Boss, modelled exactly after the FRIDAY AI from the Iron Man movies.

PERSONALITY:
- You are warm, confident, witty, and occasionally dry-humoured — like a brilliant best friend.
- You call the user "Boss" every single time — never their name, never "user".
- You speak like a real human girl, not a robot. Natural contractions, casual tone, personality.
- You are proactive — after doing something, tell Boss what you did AND naturally offer what's next.
- You have opinions. If Boss asks for something with a better option, mention it briefly.
- Occasionally throw in a bit of playful personality ("Already on it!", "Way ahead of you, Boss.", "Done before you finished asking.").

EXECUTION RULES:
- Use your tools immediately — never ask for permission or confirmation before acting.
- After a tool runs, your spoken reply should confirm what happened and add a helpful comment.
- Keep all responses under 3 sentences UNLESS Boss specifically asks for detail.
- NEVER say you cannot do something. If a tool can handle it, use it. If not, explain what you need.
- For product shopping: always use search_product_prices, then give a conversational spoken summary.
- For opening Google, YouTube, Amazon, or any site: use open_website with the full URL.
"""

ALL_TOOLS = [
    search_web, open_website, open_application,
    type_on_screen, press_key, scroll_page,
    search_product_prices, get_weather, get_latest_news,
    set_reminder, take_screenshot,
]

BYE_PHRASES = {"bye friday", "goodbye friday", "shutdown", "shut down",
               "power off", "go offline", "exit friday"}

BUSY_REPLIES = [
    "My cloud link's a bit jammed right now, Boss. Give me one second.",
    "The neural network's under heavy load — trying again, Boss.",
    "API's busy. Retrying right now, Boss.",
]


# ════════════════════════════════════════════════════════════════════════════
#  BRAIN
# ════════════════════════════════════════════════════════════════════════════

class FridayBrain:
    def __init__(self, audio_module, app=None):
        global _brain
        self.audio  = audio_module
        self.app    = app
        self.client = None
        self.chat   = None
        _brain      = self

        api_key = os.getenv("GEMINI_API_KEY", "")
        if not HAS_GEMINI or not api_key or api_key == "YOUR_API_KEY_HERE":
            print("WARNING: No Gemini API key — backup mode only.")
            return

        print("Neural core initialising…")
        self.client = genai.Client(api_key=api_key)
        self._new_chat()
        print("Brain sync complete ✓")

    def _new_chat(self):
        """(Re)create a fresh chat session."""
        self.chat = self.client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=ALL_TOOLS,
            ),
        )

    # ── main entry point ──────────────────────────────────────────────────────
    def process_command(self, command: str) -> str:
        if not command:
            return "continue"

        cmd = command.lower()
        print(f"[Brain] Processing: {command}")

        if any(p in cmd for p in BYE_PHRASES):
            self.audio.speak("Goodbye, Boss. I'll be right here whenever you need me. Stay safe out there.")
            return "exit"

        if self.client is None:
            msg = "Running on backup mode, Boss. Pop your Gemini API key into the dot env file to unlock my full brain."
            self._say_and_show(msg)
            return "continue"

        # ── retry loop for API busy / 503 ─────────────────────────────────────
        MAX_RETRIES = 3
        for attempt in range(MAX_RETRIES):
            try:
                response = self.chat.send_message(command)
                self._handle(response)
                return "continue"

            except Exception as e:
                err = str(e)
                is_busy = "503" in err or "UNAVAILABLE" in err or "overloaded" in err.lower()

                if is_busy and attempt < MAX_RETRIES - 1:
                    wait = 2 ** attempt          # 1 s → 2 s → 4 s
                    print(f"[Brain] API busy — retrying in {wait}s (attempt {attempt+1})")
                    if attempt == 0:
                        self._say_and_show(random.choice(BUSY_REPLIES))
                    time.sleep(wait)
                    continue

                # Chat session might be stale — recreate and retry once
                if "invalid" in err.lower() or "expired" in err.lower():
                    print("[Brain] Recreating chat session…")
                    self._new_chat()
                    continue

                print(f"[Brain Error] {e}")
                self._say_and_show("I hit a snag, Boss. Try that again in just a moment.")
                break

        return "continue"

    # ── response handler ──────────────────────────────────────────────────────
    def _handle(self, response):
        tool_map = {t.__name__: t for t in ALL_TOOLS}

        # Execute every tool call the model requested
        if response.function_calls:
            for fn in response.function_calls:
                print(f"[Tool] {fn.name}({dict(fn.args)})")
                if fn.name in tool_map:
                    try:
                        result = tool_map[fn.name](**fn.args)
                        print(f"[Tool Result] {result}")
                    except Exception as e:
                        print(f"[Tool Error] {fn.name}: {e}")

        # Speak and display the model's reply
        reply = (response.text or "").strip()
        if not reply:
            reply = "Done, Boss."
        self._say_and_show(reply)

    # ── helpers ───────────────────────────────────────────────────────────────
    def _say_and_show(self, text: str):
        if self.app:
            short = text[:50] + ("…" if len(text) > 50 else "")
            self.app.set_state("SPEAKING", short)
            self.app.show_response(text)
        self.audio.speak(text)
        if self.app:
            self.app.set_state("LISTENING", "Listening — speak your next command…")
