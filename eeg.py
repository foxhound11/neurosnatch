import socket
import time
import requests
import json

# ── Server URL ─────────────────────────────────────────────────────────────
SERVER_URL = "http://localhost:5000"
# ──────────────────────────────────────────────────────────────────────────

# The Unicorn bandpower UDP payload is 70 comma-separated values.
# Value 21 (1-indexed) = alpha band, channel 1  →  index 20 (0-indexed).
ALPHA_INDEX = 20
UDP_PORT    = 1000   # change to whichever port the Unicorn Suite is sending on

DECISION_LEAD_TIME = 0.5  # send the decision this many seconds before clip 2 ends


def get_clip_info():
    """Poll the server for clip durations reported by the frontend."""
    try:
        r = requests.get(f"{SERVER_URL}/api/clip-info", timeout=2)
        return r.json()
    except Exception:
        return None


def wait_for_clip(clip_num):
    """Block until the frontend reports that a clip has started.
    Returns (duration, server_start_time)."""
    key = f"clip{clip_num}"
    print(f"  Waiting for Clip {clip_num} to start in the browser...")
    while True:
        info = get_clip_info()
        if info and info.get(key) and info[key].get("started"):
            duration = info[key]["duration"]
            start_time = info[key]["start_time"]  # server wall-clock
            print(f"  Clip {clip_num} started — duration {duration:.1f}s")
            return duration, start_time
        time.sleep(0.2)


def send_decision(choice):
    """POST the final decision to the server so the frontend plays the right ending."""
    try:
        r = requests.post(
            f"{SERVER_URL}/api/decide",
            json={"choice": choice},
            timeout=5,
        )
        print(f"  Decision sent to server: {choice} — {r.json()}")
    except Exception as e:
        print(f"  ERROR sending decision: {e}")


def collect_alpha(sock, duration_limit, clip_label):
    """Collect alpha samples from UDP for up to `duration_limit` seconds.
    Returns (alpha_sum, sample_count)."""
    alpha_sum, count = 0.0, 0
    t0 = time.monotonic()

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
        if len(parts) <= ALPHA_INDEX:
            continue
        try:
            alpha_val = float(parts[ALPHA_INDEX].strip())
        except ValueError:
            continue

        alpha_sum += alpha_val
        count += 1
        print(f"  [{clip_label}] sample {count:4d} | alpha = {alpha_val:.4f} | elapsed = {elapsed:.1f}s")

    return alpha_sum, count


if __name__ == "__main__":
    print("=" * 58)
    print("  NEUROSNATCH — EEG Alpha Analyzer")
    print("=" * 58)
    print(f"  UDP port : {UDP_PORT}")
    print(f"  Server   : {SERVER_URL}")
    print()
    print("  Start the session in the browser. This script will")
    print("  auto-detect clip durations and record alpha power.")
    print("  Decision is sent {:.1f}s before Clip 2 ends.".format(DECISION_LEAD_TIME))
    print("=" * 58)
    print()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", UDP_PORT))
    sock.settimeout(1.0)

    # ── Phase 1: wait for Clip 1 to start, then collect alpha ──────────
    video1_length, clip1_start = wait_for_clip(1)

    # Account for any lag between clip start and us noticing
    already_elapsed_1 = time.time() - clip1_start
    collect_time_1 = max(video1_length - already_elapsed_1, 0)
    print(f"  (clip 1 started {already_elapsed_1:.2f}s ago, collecting for {collect_time_1:.1f}s)")

    sum1, n1 = collect_alpha(sock, collect_time_1, "Clip 1")
    mean1 = sum1 / n1 if n1 > 0 else float("nan")
    print(f"\n  *** Clip 1 done — mean alpha: {mean1:.4f}  ({n1} samples) ***")
    if n1 == 0:
        print("  *** WARNING: No UDP samples received for Clip 1! Is the Unicorn sending? ***")
    print()

    # ── Phase 2: wait for Clip 2 to start, collect, decide early ───────
    video2_length, clip2_start = wait_for_clip(2)

    # Account for any lag between clip 2 start and us noticing
    already_elapsed_2 = time.time() - clip2_start
    collect_time_2 = max(video2_length - already_elapsed_2 - DECISION_LEAD_TIME, 0)
    print(f"  (clip 2 started {already_elapsed_2:.2f}s ago, collecting for {collect_time_2:.1f}s)")

    sum2, n2 = collect_alpha(sock, collect_time_2, "Clip 2")
    mean2 = sum2 / n2 if n2 > 0 else float("nan")
    print(f"\n  *** Clip 2 done — mean alpha: {mean2:.4f}  ({n2} samples) ***")
    if n2 == 0:
        print("  *** WARNING: No UDP samples received for Clip 2! Is the Unicorn sending? ***")
    print()

    sock.close()

    # ── Decide ─────────────────────────────────────────────────────────
    #   Lower mean alpha → more engagement / less relaxation.
    #   Clip 1 = calm_clip, Clip 2 = excited_clip.
    #   Pick the clip with lower alpha as the one the brain engaged with more.
    print("── Results ──────────────────────────────────────────")
    print(f"  Clip 1 (calm)     mean alpha: {mean1:.4f}  (sum={sum1:.4f}, n={n1})")
    print(f"  Clip 2 (excited)  mean alpha: {mean2:.4f}  (sum={sum2:.4f}, n={n2})")
    print(f"  nan check: mean1 is nan? {mean1 != mean1}  mean2 is nan? {mean2 != mean2}")

    import math
    if math.isnan(mean1) and math.isnan(mean2):
        choice = "calm"
        print("  → Both clips had NO samples (nan) — defaulting to calm")
    elif math.isnan(mean1):
        choice = "excited"
        print("  → Clip 1 had no data — picking excited")
    elif math.isnan(mean2):
        choice = "calm"
        print("  → Clip 2 had no data — picking calm")
    elif mean1 <= mean2:
        choice = "calm"
        print("  → Clip 1 (calm) had LOWER alpha → more engagement")
    else:
        choice = "excited"
        print("  → Clip 2 (excited) had LOWER alpha → more engagement")

    print(f"\n  >>> DECISION: {choice.upper()} <<<")
    print("─────────────────────────────────────────────────────")

    print(f"\n  Sending decision to {SERVER_URL}/api/decide ...")
    send_decision(choice)
    print("\n  Done. The browser will now play the ending video.")
