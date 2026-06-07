import threading
import tkinter as tk
import math
import time
import datetime
import random
from friday_audio import FridayAudio
from friday_brain import FridayBrain

# ── Color palettes per state ───────────────────────────────────────────────
PALETTES = {
    "STANDBY":    {"pri": "#00d4ff", "sec": "#0077aa", "glow": "#001a33", "dot": "#ff8800"},
    "LISTENING":  {"pri": "#00ff99", "sec": "#00aa55", "glow": "#002211", "dot": "#00ff99"},
    "PROCESSING": {"pri": "#ff9900", "sec": "#cc5500", "glow": "#221100", "dot": "#ff9900"},
    "SPEAKING":   {"pri": "#cc44ff", "sec": "#7700cc", "glow": "#1a0033", "dot": "#cc44ff"},
    "ERROR":      {"pri": "#ff3344", "sec": "#aa1122", "glow": "#220011", "dot": "#ff3344"},
}

W, H       = 480, 600   # extra 120px at bottom for conversation panel
CIRCLE_H   = 460
CX, CY     = 240, 230


class FridayApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("F.R.I.D.A.Y.")
        self.overrideredirect(True)
        self.configure(bg="#000000")
        self.wm_attributes("-transparentcolor", "#000000")
        self.wm_attributes("-topmost", True)
        self.geometry(f"{W}x{H}")

        # Position bottom-right
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{W}x{H}+{sw - W - 20}+{sh - H - 50}")

        # ── Canvas (circle animation)
        self.canvas = tk.Canvas(self, width=W, height=CIRCLE_H,
                                bg="#000000", highlightthickness=0)
        self.canvas.pack(side="top")

        # ── Conversation panel (bottom)
        panel = tk.Frame(self, bg="#04090f", width=W, height=140)
        panel.pack(side="top", fill="x")
        panel.pack_propagate(False)

        tk.Label(panel, text="◈  CONVERSATION LOG",
                 font=("Consolas", 8, "bold"), fg="#0077aa", bg="#04090f").pack(anchor="w", padx=10, pady=(6, 0))

        self.you_var    = tk.StringVar(value="You  ›  —")
        self.fri_var    = tk.StringVar(value="FRIDAY  ›  Awaiting Boss…")

        tk.Label(panel, textvariable=self.you_var,
                 font=("Consolas", 9), fg="#00ff99", bg="#04090f",
                 wraplength=460, justify="left", anchor="w").pack(fill="x", padx=10)

        tk.Label(panel, textvariable=self.fri_var,
                 font=("Consolas", 9), fg="#00d4ff", bg="#04090f",
                 wraplength=460, justify="left", anchor="w").pack(fill="x", padx=10, pady=(2, 0))

        # Divider line
        tk.Frame(panel, bg="#0077aa", height=1).pack(fill="x", padx=10, pady=6)
        tk.Label(panel, text="Right-click anywhere to exit  ●  Say 'Hi Friday' to activate",
                 font=("Consolas", 7), fg="#0077aa", bg="#04090f").pack()

        # Drag bindings
        for widget in (self.canvas, panel):
            widget.bind("<Button-1>",  self._drag_start)
            widget.bind("<B1-Motion>", self._drag_move)
            widget.bind("<Button-3>",  lambda e: self.quit())

        # Animation state
        self.state      = "STANDBY"
        self.status_txt = "Awaiting Boss…"
        self.is_active  = False
        self.angle      = 0.0
        self.pulse      = 1.0
        self.pulse_dir  = 1
        self.wave_bars  = [random.randint(2, 12) for _ in range(22)]

        # Init systems
        print("Initialising F.R.I.D.A.Y. systems…")
        self.audio = FridayAudio()
        self.brain = FridayBrain(self.audio, self)

        # Boot greeting — then start listener AFTER greeting finishes
        self._stop = False
        def _boot_then_listen():
            self.audio.speak(
                "F.R.I.D.A.Y. systems online. Good evening, Boss. "
                "Say Hi Friday whenever you need me."
            )
            # greeting is done (speak() is synchronous), now start listener
            self._listen_loop()

        threading.Thread(target=_boot_then_listen, daemon=True).start()

        self._animate()

    # ── drag ─────────────────────────────────────────────────────────────────
    def _drag_start(self, e):
        self._dx, self._dy = e.x_root - self.winfo_x(), e.y_root - self.winfo_y()

    def _drag_move(self, e):
        self.geometry(f"+{e.x_root - self._dx}+{e.y_root - self._dy}")

    # ── thread-safe state setters ─────────────────────────────────────────────
    def set_state(self, state: str, text: str = ""):
        self.after(0, self._apply_state, state, text or state.capitalize())

    def _apply_state(self, state, text):
        self.state      = state
        self.status_txt = text
        self.is_active  = state in ("LISTENING", "PROCESSING", "SPEAKING")

    def show_command(self, text: str):
        self.after(0, lambda: self.you_var.set(f"You  ›  {text}"))

    def show_response(self, text: str):
        # Wrap long responses for display
        short = text if len(text) <= 200 else text[:197] + "…"
        self.after(0, lambda: self.fri_var.set(f"FRIDAY  ›  {short}"))

    # ── animation ─────────────────────────────────────────────────────────────
    def _animate(self):
        c   = self.canvas
        cx  = CX
        cy  = CY
        p   = PALETTES.get(self.state, PALETTES["STANDBY"])
        pri = p["pri"]
        sec = p["sec"]
        glow = p["glow"]

        c.delete("all")

        # outer glow halos
        for i in range(7, 0, -1):
            r = 160 + i * 5
            c.create_oval(cx-r, cy-r, cx+r, cy+r, outline=glow, width=2)

        # static outermost ring
        c.create_oval(cx-160, cy-160, cx+160, cy+160, outline=pri, width=2)

        # rotating outer arc ring
        self._draw_ring(c, cx, cy, 150, self.angle,       15, 2, pri, skip=3)
        # counter-rotating middle ring
        self._draw_ring(c, cx, cy, 130, -self.angle*0.6,  20, 1, sec, skip=4)

        # tick marks
        for deg in range(0, 360, 6):
            rad = math.radians(deg)
            r1  = 157 if deg % 30 == 0 else 153
            c.create_line(cx + r1*math.cos(rad), cy + r1*math.sin(rad),
                          cx + 162*math.cos(rad), cy + 162*math.sin(rad),
                          fill=pri if deg % 30 == 0 else sec,
                          width=2 if deg % 30 == 0 else 1)

        # pulsing inner circle
        ir = 105 * self.pulse
        c.create_oval(cx-ir, cy-ir, cx+ir, cy+ir, fill="#03070d", outline=pri, width=3)
        for r in (90, 77):
            sr = r * self.pulse
            c.create_oval(cx-sr, cy-sr, cx+sr, cy+sr, outline=sec, width=1)

        # spinning radar arm
        rad = math.radians(self.angle * 2.1)
        c.create_line(cx, cy, cx+62*math.cos(rad), cy+62*math.sin(rad), fill=pri, width=2)

        # center text
        c.create_text(cx, cy-18, text="F.R.I.D.A.Y.", font=("Consolas", 17, "bold"), fill=pri)
        c.create_text(cx, cy+ 4, text="─" * 13,       font=("Consolas", 8),            fill=sec)
        c.create_text(cx, cy+20, text=self.state,      font=("Consolas", 9, "bold"),    fill=pri)

        short = self.status_txt[:36] + "…" if len(self.status_txt) > 36 else self.status_txt
        c.create_text(cx, cy+36, text=short, font=("Consolas", 8), fill=sec)

        # status dot
        c.create_oval(cx-5, cy+50, cx+5, cy+60, fill=p["dot"], outline="")

        # HUD top
        now = datetime.datetime.now()
        c.create_text(cx, 26, text=now.strftime("%H:%M:%S"),  font=("Consolas", 13, "bold"), fill=pri)
        c.create_text(cx, 44, text=now.strftime("%d %b %Y"), font=("Consolas", 9),            fill=sec)

        # corner brackets
        for bx, by, dx, dy in [(52,52,1,1),(428,52,-1,1),(52,408,1,-1),(428,408,-1,-1)]:
            c.create_line(bx, by, bx+dx*20, by,        fill=sec, width=2)
            c.create_line(bx, by, bx,        by+dy*20, fill=sec, width=2)

        # side HUD labels
        c.create_text(52, CY,  text="NEURAL\nONLINE", font=("Consolas", 7), fill=sec, justify="center")
        c.create_text(428, CY, text="VOICE\nACTIVE",  font=("Consolas", 7), fill=sec, justify="center")

        # waveform bars (only when active)
        if self.is_active:
            bw, sp  = 8, 3
            total   = len(self.wave_bars) * (bw + sp)
            sx      = cx - total // 2
            bar_y   = cy + 175
            for i, h in enumerate(self.wave_bars):
                bx = sx + i * (bw + sp)
                c.create_rectangle(bx, bar_y - h, bx + bw, bar_y, fill=pri, outline="")
            for i in range(len(self.wave_bars)):
                self.wave_bars[i] = max(3, min(30, self.wave_bars[i] + random.randint(-5, 5)))

        # bottom HUD strip
        c.create_text(cx, 445, text="BOSS-LINKED  ●  GEMINI-2.5-FLASH  ●  AI CORE",
                      font=("Consolas", 7), fill=sec)

        # update vars
        self.angle    = (self.angle + 1.8) % 360
        self.pulse   += 0.004 * self.pulse_dir
        if self.pulse > 1.04: self.pulse_dir = -1
        if self.pulse < 0.96: self.pulse_dir =  1

        self.after(33, self._animate)

    def _draw_ring(self, c, cx, cy, r, offset, step, width, color, skip=3):
        segs = list(range(0, 360, step))
        for idx, deg in enumerate(segs):
            if idx % skip == skip - 1:
                continue
            a1 = math.radians(deg + offset)
            a2 = math.radians(deg + step * 0.75 + offset)
            c.create_line(cx + r*math.cos(a1), cy + r*math.sin(a1),
                          cx + r*math.cos(a2), cy + r*math.sin(a2),
                          fill=color, width=width)

    # ── voice listener loop ───────────────────────────────────────────────────
    def _listen_loop(self):
        """
        Two-phase loop:
          PHASE 1 → STANDBY  : listen until 'friday' is detected.
          PHASE 2 → ACTIVE   : stay in conversation, keep taking commands,
                               until 'bye friday' / 'exit' / 'shutdown'.
        """
        while not self._stop:
            # ── PHASE 1: wait for wake word ───────────────────────────────
            self.set_state("STANDBY", "Awaiting wake word…")
            cmd = self.audio.listen(max_duration=15)

            if "friday" not in cmd:
                time.sleep(0.8)   # brief cooldown before next listen attempt
                continue

            # ── PHASE 2: conversation mode ────────────────────────────────
            self.set_state("LISTENING", "Activated — I'm listening, Boss!")
            self.audio.speak("Yes Boss? I'm fully active and listening. What can I do for you?")

            BYE_WORDS = {"bye friday", "goodbye friday", "exit", "shutdown",
                         "shut down", "power off", "go offline", "goodbye"}

            while not self._stop:
                self.set_state("LISTENING", "Listening — speak your command…")
                command = self.audio.listen(max_duration=15)

                if not command:
                    self.set_state("LISTENING", "Still here Boss — speak anytime…")
                    time.sleep(0.5)
                    continue

                self.show_command(command)
                print(f"[Command received] {command}")

                # Check for shutdown
                if any(bye in command for bye in BYE_WORDS):
                    self.set_state("STANDBY", "Goodbye, Boss.")
                    self.show_response("Going back to standby. Say 'Hi Friday' to wake me again.")
                    self.audio.speak("Goodbye Boss. I'll be right here whenever you need me.")
                    break   # exit conversation mode → back to PHASE 1

                # Process the command
                self.set_state("PROCESSING", f"Working on: {command[:40]}…")
                result = self.brain.process_command(command)

                if result == "exit":
                    self.quit()
                    return


if __name__ == "__main__":
    app = FridayApp()
    print("F.R.I.D.A.Y. running. Say 'Hi FRIDAY' to activate. Right-click to quit.")
    app.mainloop()