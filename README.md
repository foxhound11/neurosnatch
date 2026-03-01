# Neurosnatch 🧠🎬
> **You watch, the engine feels, the story shifts.**
<img width="1920" height="1080" alt="vlcsnap-2026-03-01-12h52m43s257" src="https://github.com/user-attachments/assets/9136b044-9e4b-49ab-82bc-8703630fef9e" />

Neurosnatch is an adaptive, AI-powered storytelling engine that dynamically changes the narrative of a film based on the viewer's subconscious brain activity. As we get flooded with AI-generated content, new forms of media consumption will emerge - including personalised, eeg based films. Past attempts at interactive films, such as Netflix’s *Bandersnatch*, have been limited by the cinematic illusion-breaking nature of conscious user input. Neurosnatch solves this by removing the remote control and using raw EEG data to steer the story seamlessly.

Worked on during the Imperial Neurotech Hackathon

## 🗂️ Repository Structure
This repository contains the full prototype for the Neurosnatch engine:

- **`eeg.py`**: The EEG analysis and hardware script. It connects to the headset, processes the brainwaves (tracking alpha wave desynchronization), and sends the user's subconscious decision to the server.
- **`server.py`**: A lightweight Flask server that acts as the bridge between the EEG script and the video player frontend. 
- **`index.html`**: The interactive web frontend. It plays the initial clips, polls the server for the user's brainwave decision, and seamlessly transitions to the chosen ending.
- **Video Assets (`.mp4`)**: The branching video clips (`calm_clip`, `excited_clip`, `calm_ending`, `excited_ending`).

*(Note: Depending on how the developer configured `server.py`, the video files may need to be placed in a `videos/` folder before running).*

## ⚙️ How It Works
Our engine uses a **g.tec Unicorn Hybrid Black EEG** headset to track the parietal alpha wave intensity of the viewer as they watch carefully crafted scenes.

1. **Monitor & Track:** Extract real-time brainwave data from the viewer.
2. **Analyze Engagement:** We calculate the average alpha wave amplitude in the parietal region. Lower alpha wave power ("desynchronization") correlates with higher attention, interest, and engagement.
3. **Adapt the Story:** The algorithm determines which scene the viewer engaged with the most and automatically POSTs the decision to the server. The video player then proceeds with the corresponding branching storyline.

## 🚀 How to Run the Demo

### 1. Install Dependencies
Ensure you have Python installed, then install the required packages:

```bash
pip install flask flask-cors requests
```

*(Note: `eeg.py` requires additional dependencies depending on the EEG hardware SDK used).*

### 2. Start the Server
Run the Flask bridge server:

```bash
python server.py
```

It will start running on `http://localhost:5000`.

### 3. Open the Player
Launch `http://localhost:5000` in Google Chrome and enter full screen. Click "Begin Session" to start the experience.

### 4. Run the EEG Integration
Run `eeg.py` while the headset is connected. It will analyze the user's brainwaves and automatically trigger the branching video at the right moment.

```bash
python eeg.py
```

## 📈 Roadmap & Scalability
- **Phase 1 (Experiential):** Deploy at exhibitions, experience parks, and immersive VR venues. We get paid to build our training set.
- **Phase 2 (Integration):** Partner with consumer EEG apps. Give the 1M+ owners of devices like Muse a new reason to use their headsets by adding neuro-responsive video playback.
- **Phase 3 (Mass Market):** License our algorithm to major streaming platforms and virtual reality providers as at-home biometric wearable adoption grows.

## 🚧 Limitations & Future Work
- **No Prefrontal EEG (Alpha Asymmetry):** Current 8-channel headsets lack F3/F4 channels. We cannot measure approach/avoid emotional signals yet.
- **Not Multimodal:** We currently rely exclusively on EEG. Integrating eye tracking or heart rate would isolate true attention from ocular artifacts or general arousal.
- **No Event-Related Potentials (ERPs):** Data is not yet time-locked to specific timestamped video events (e.g., jump scares), preventing P300-style instant response tracking.
- **Bandpower Only:** The model evaluates generic bandpower features instead of raw cross-frequency coupling (like theta phase modulating gamma amplitude).
