"""
NEURO CINEMA — Flask Server
============================
Bridges the EEG Python script to the HTML video player.

Usage:
  1. Put your videos in the /videos subfolder:
     - calm_clip.mp4      (30s calm content)
     - excited_clip.mp4   (30s exciting content)
     - calm_ending.mp4    (ending video for calm)
     - excited_ending.mp4 (ending video for excited)

  2. Run this server:
     python server.py

  3. Open http://localhost:5000 in Chrome (fullscreen it!)

  4. Your EEG script sends the decision:
     import requests
     requests.post("http://localhost:5000/api/decide", json={"choice": "calm"})
     # or
     requests.post("http://localhost:5000/api/decide", json={"choice": "excited"})

  5. The page will reveal the result and play the ending.
"""

from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
import os
import json
import time
import socket
import threading
import math

app = Flask(__name__)
CORS(app)

# ---------- EEG CONFIG ----------
BAND_BASES = [0, 8, 16, 24, 32, 40, 48]        # delta, theta, alpha, beta_low, beta_mid, beta_high, gamma
BAND_AVG_INDICES = [57, 58, 59, 60, 61, 62, 63]  # all-channel avg for each band
BAND_NAMES = ['delta', 'theta', 'alpha', 'beta_low', 'beta_mid', 'beta_high', 'gamma']
UDP_PORT    = 1000        # port the Unicorn Suite sends bandpower on
DECISION_LEAD_TIME = 0.5  # send decision this many seconds before clip 2 ends

# ---------- STATE ----------
state = {
    "decision": None,        # "calm" or "excited"
    "timestamp": None,       # when the decision was made
    "eeg_live": {},          # optional: live EEG data for visualization
    "clips": {               # video clip info reported by the frontend
        1: {"started": False, "start_time": None, "duration": None},
        2: {"started": False, "start_time": None, "duration": None},
    },
    "eeg_thread": None,      # reference to the background EEG thread
    "eeg_status": "idle",    # idle | collecting | done | error
    "eeg_index": 20,         # which payload index to read (default: alpha ch5)
}


# ---------- EEG BACKGROUND THREAD ----------
def collect_alpha_for_duration(sock, duration_limit, clip_label):
    """Collect band power samples from UDP for up to `duration_limit` seconds."""
    eeg_index = state["eeg_index"]
    alpha_sum, count = 0.0, 0
    t0 = time.monotonic()

    # Keep a rolling history for the live graph
    live_history = list(state["eeg_live"].get("history", []))

    while True:
        elapsed = time.monotonic() - t0
        if elapsed >= duration_limit:
            break

        remaining = duration_limit - elapsed
        sock.settimeout(min(remaining, 1.0))

        try:
            data, _ = sock.recvfrom(1024)
        except socket.timeout:
            continue

        message = data.decode("ascii", errors="ignore").strip()
        parts = message.split(",")
        if len(parts) <= eeg_index:
            continue
        try:
            alpha_val = float(parts[eeg_index].strip())
        except ValueError:
            continue

        alpha_sum += alpha_val
        count += 1

        # Update live visualization data
        live_history.append(alpha_val)
        if len(live_history) > 80:
            live_history = live_history[-80:]
        state["eeg_live"] = {
            "value": alpha_val,
            "history": live_history[-80:],
            "status": state["eeg_status"],
        }

        if count % 10 == 1:  # print every 10th sample to reduce noise
            print(f"  [EEG {clip_label}] sample {count:4d} | value = {alpha_val:.4f} | elapsed = {elapsed:.1f}s")

    return alpha_sum, count


def eeg_thread_main():
    """Background thread: collects alpha for clip 1 and clip 2, then sets the decision."""
    try:
        state["eeg_status"] = "collecting"
        print("\n  [EEG] Thread started — opening UDP socket on port", UDP_PORT)
        print(f"  [EEG] Using payload index: {state['eeg_index']}")

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", UDP_PORT))
        sock.settimeout(1.0)

        # ── Clip 1: collect alpha for its full duration ──────────────
        clip1 = state["clips"][1]
        already_elapsed_1 = time.time() - clip1["start_time"]
        collect_time_1 = max(clip1["duration"] - already_elapsed_1, 0)
        print(f"  [EEG] Clip 1: duration={clip1['duration']:.1f}s, already_elapsed={already_elapsed_1:.2f}s, collecting for {collect_time_1:.1f}s")

        sum1, n1 = collect_alpha_for_duration(sock, collect_time_1, "Clip 1")
        mean1 = sum1 / n1 if n1 > 0 else float("nan")
        print(f"\n  [EEG] *** Clip 1 done — mean alpha: {mean1:.4f}  ({n1} samples) ***")
        if n1 == 0:
            print("  [EEG] WARNING: No UDP samples received for Clip 1!")

        # ── Wait for Clip 2 to start ────────────────────────────────
        print("  [EEG] Waiting for clip 2 to start...")
        while not state["clips"][2]["started"]:
            time.sleep(0.1)

        clip2 = state["clips"][2]
        already_elapsed_2 = time.time() - clip2["start_time"]
        collect_time_2 = max(clip2["duration"] - already_elapsed_2 - DECISION_LEAD_TIME, 0)
        print(f"  [EEG] Clip 2: duration={clip2['duration']:.1f}s, already_elapsed={already_elapsed_2:.2f}s, collecting for {collect_time_2:.1f}s")

        sum2, n2 = collect_alpha_for_duration(sock, collect_time_2, "Clip 2")
        mean2 = sum2 / n2 if n2 > 0 else float("nan")
        print(f"\n  [EEG] *** Clip 2 done — mean alpha: {mean2:.4f}  ({n2} samples) ***")
        if n2 == 0:
            print("  [EEG] WARNING: No UDP samples received for Clip 2!")

        sock.close()

        # ── Decide ──────────────────────────────────────────────────
        print(f"\n  [EEG] ── Results ──────────────────────────────────")
        print(f"  [EEG] Clip 1 (calm)     mean alpha: {mean1:.4f}  (sum={sum1:.4f}, n={n1})")
        print(f"  [EEG] Clip 2 (excited)  mean alpha: {mean2:.4f}  (sum={sum2:.4f}, n={n2})")

        if math.isnan(mean1) and math.isnan(mean2):
            choice = "calm"
            print("  [EEG] Both clips had NO samples (nan) — defaulting to calm")
        elif math.isnan(mean1):
            choice = "excited"
            print("  [EEG] Clip 1 had no data — picking excited")
        elif math.isnan(mean2):
            choice = "calm"
            print("  [EEG] Clip 2 had no data — picking calm")
        elif mean1 <= mean2:
            choice = "calm"
            print("  [EEG] Clip 1 (calm) had LOWER alpha → more engagement")
        else:
            choice = "excited"
            print("  [EEG] Clip 2 (excited) had LOWER alpha → more engagement")

        # Set decision directly in state (no HTTP needed, same process!)
        state["decision"] = choice
        state["timestamp"] = time.time()
        state["eeg_status"] = "done"
        print(f"\n  [EEG] >>> DECISION SET: {choice.upper()} <<<\n")

    except Exception as e:
        state["eeg_status"] = "error"
        print(f"\n  [EEG] ERROR in thread: {e}")
        import traceback
        traceback.print_exc()


# ---------- PAGES ----------
@app.route("/")
def index():
    return send_file("index.html")


@app.route("/NS_isolated_white.png")
def serve_logo():
    return send_file("NS_isolated_white.png")


# ---------- API: EEG Config (from frontend dropdowns) ----------
@app.route("/api/eeg-config", methods=["POST"])
def eeg_config():
    """Frontend sends the selected brainwave band and channel."""
    data = request.json
    band = data.get("band")        # 0-6 (delta..gamma)
    channel = data.get("channel")  # "1"-"8" or "avg"

    if band not in range(7):
        return jsonify({"error": "band must be 0-6"}), 400

    if channel == "avg":
        eeg_index = BAND_AVG_INDICES[band]
        label = f"{BAND_NAMES[band]} (all-channels avg)"
    else:
        ch = int(channel)
        if ch < 1 or ch > 8:
            return jsonify({"error": "channel must be 1-8 or avg"}), 400
        eeg_index = BAND_BASES[band] + (ch - 1)
        label = f"{BAND_NAMES[band]} ch{ch}"

    state["eeg_index"] = eeg_index
    print(f"  [CONFIG] Band={BAND_NAMES[band]}, Channel={channel} → payload index {eeg_index} ({label})")
    return jsonify({"status": "ok", "index": eeg_index, "label": label})


# ---------- VIDEO SERVING ----------
@app.route("/videos/<path:filename>")
def serve_video(filename):
    video_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "videos")
    return send_from_directory(video_dir, filename)


# ---------- API: EEG Script → Server ----------
@app.route("/api/decide", methods=["POST"])
def decide():
    """EEG script calls this with {"choice": "calm"} or {"choice": "excited"}"""
    data = request.json
    print(f"  [DEBUG] /api/decide received: {data}")
    choice = data.get("choice", "").lower()
    if choice not in ("calm", "excited"):
        return jsonify({"error": "choice must be 'calm' or 'excited'"}), 400

    state["decision"] = choice
    state["timestamp"] = time.time()
    print(f"\n>>> DECISION RECEIVED: {choice.upper()} <<<\n")
    return jsonify({"status": "ok", "choice": choice})


@app.route("/api/eeg", methods=["POST"])
def eeg_data():
    """Optional: EEG script sends live data for visualization"""
    data = request.json
    state["eeg_live"] = data
    return jsonify({"status": "ok"})


# ---------- API: Frontend → Server (clip start/duration) ----------
@app.route("/api/clip-started", methods=["POST"])
def clip_started():
    """Frontend reports when a clip starts playing and its duration.
    When clip 1 starts, automatically launches the EEG collection thread."""
    data = request.json
    clip_num = data.get("clip")       # 1 or 2
    duration = data.get("duration")   # seconds (float)
    if clip_num not in (1, 2):
        return jsonify({"error": "clip must be 1 or 2"}), 400
    state["clips"][clip_num] = {
        "started": True,
        "start_time": time.time(),
        "duration": duration,
    }
    print(f"  [CLIP {clip_num}] started — duration {duration:.1f}s")

    # Auto-launch EEG thread when clip 1 starts
    if clip_num == 1 and (state["eeg_thread"] is None or not state["eeg_thread"].is_alive()):
        t = threading.Thread(target=eeg_thread_main, daemon=True)
        state["eeg_thread"] = t
        t.start()
        print("  [EEG] Background thread launched!")

    return jsonify({"status": "ok"})


@app.route("/api/clip-info")
def clip_info():
    """EEG script polls this to get clip durations and start times"""
    return jsonify({
        "clip1": state["clips"][1],
        "clip2": state["clips"][2],
    })


# ---------- API: HTML Page → Server (polling) ----------
@app.route("/api/decision")
def get_decision():
    """HTML page polls this to check if a decision has been made"""
    print(f"  [DEBUG] /api/decision polled — current decision: {state['decision']}")
    return jsonify({
        "decision": state["decision"],
        "timestamp": state["timestamp"],
    })


@app.route("/api/eeg-live")
def get_eeg_live():
    """HTML page polls this for live EEG visualization data"""
    return jsonify(state["eeg_live"])


@app.route("/api/reset", methods=["POST"])
def reset():
    """Reset for a new session"""
    state["decision"] = None
    state["timestamp"] = None
    state["eeg_live"] = {}
    state["clips"] = {
        1: {"started": False, "start_time": None, "duration": None},
        2: {"started": False, "start_time": None, "duration": None},
    }
    state["eeg_thread"] = None
    state["eeg_status"] = "idle"
    state["eeg_index"] = 20
    print("\n>>> SESSION RESET <<<\n")
    return jsonify({"status": "ok"})


# ---------- CHECK VIDEOS ----------
@app.route("/api/check-videos")
def check_videos():
    """Check which video files are available"""
    video_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "videos")
    expected = ["calm_clip.mp4", "excited_clip.mp4", "calm_ending.mp4", "excited_ending.mp4"]
    found = {}
    for f in expected:
        found[f] = os.path.exists(os.path.join(video_dir, f))
    return jsonify(found)


# ---------- RUN ----------
if __name__ == "__main__":
    video_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "videos")
    os.makedirs(video_dir, exist_ok=True)

    print("=" * 60)
    print("  [BRAIN] NEUROSNATCH SERVER")
    print("=" * 60)
    print(f"  Open: http://localhost:5000")
    print(f"  Videos folder: {video_dir}")
    print()

    # Check for videos
    expected = ["calm_clip.mp4", "excited_clip.mp4", "calm_ending.mp4", "excited_ending.mp4"]
    for f in expected:
        path = os.path.join(video_dir, f)
        status = "[OK]" if os.path.exists(path) else "[MISSING]"
        print(f"  {status}  {f}")

    print()
    print("  To send a decision from your EEG script:")
    print('    requests.post("http://localhost:5000/api/decide", json={"choice": "calm"})')
    print("=" * 60)
    print()

    app.run(host="0.0.0.0", port=5000, debug=True)
