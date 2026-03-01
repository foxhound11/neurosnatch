``` markdown
# Neurosnatch: Adaptive AI-Powered Storytelling Engine

## Overview

Neurosnatch is an adaptive, AI-powered storytelling engine designed to revolutionize media consumption. It moves beyond traditional interactive films, which are hindered by high production costs and illusion-breaking user input, by allowing the story to shift based on the viewer's unconscious neuro-engagement data.

The project is positioned to own a new form of media consumption that will emerge as the internet becomes flooded with high-quality AI-generated video content.

## Technology & Mechanism

The core mechanism of Neurosnatch involves using electroencephalography (EEG) to track a viewer's brain activity and determine their level of engagement with the presented video content.

### Components

*   **EEG Device:** A g.tec Unicorn Hybrid Black EEG headset (used in the initial demo).
*   **Target Signal:** The model tracks the intensity of **alpha brain waves** in the **parietal region** of the brain.
*   **Engagement Metric:** A **lower average alpha wave amplitude** in the parietal region is assumed to correspond to **higher engagement** (alpha wave "desynchronisation" correlates with increased attention and interest).
*   **Story Adaptation:** The video player selects the next scene by recognizing the extract with the lowest alpha wave power as more interesting for the viewer.

### Demo Implementation

The current demo presents the viewer with a movie consisting of two contrasting scenes (e.g., one joyful and one darker). The algorithm:
1.  Measures the viewer's parietal alpha wave intensity for each scene.
2.  Identifies the scene that elicited the lowest alpha wave power.
3.  Automatically selects one of two possible third videos to continue the narrative, adapting the story in real-time based on the viewer's subconscious preference.

## Current Technical Limitations & Future Improvements

The current demo and prototype have several technical limitations that outline a clear roadmap for future development:

| Limitation | Description | Future Improvement Goal |
| :--- | :--- | :--- |
| **No Prefrontal EEG (No Alpha Asymmetry)** | The 8-channel EEG used lacked channels F3 & F4 (prefrontal cortex). This prevents the measurement of **alpha asymmetry**, which is used to determine positive/negative emotional feedback (approach vs. avoid signals). | Utilize higher-channel EEG or specific electrode placements to incorporate prefrontal alpha asymmetry for a more nuanced emotional response measurement. |
| **Not Multimodal** | Only EEG data is currently measured. This makes it difficult to cleanly separate EEG changes that may be due to attention, eye state, movement, or general arousal. | Add **eye tracking** to know what the viewer is looking at, and incorporate **heart rate** and **skin conductance** to provide a direct body arousal signal. |
| **No ERPs (No Event Markers)** | The video events were not time-locked with the EEG recording. This prevents the ability to measure **Event-Related Potentials (ERPs)**, which are fast brain responses to specific moments (like a cut, reveal, or jump scare). | Implement exact timestamps for video events to measure P300-style effects and other fast brain responses. |
| **Bandpower Only** | The model uses only bandpower features (energy in alpha, beta, gamma bands), discarding complex interactions. | Utilize raw EEG data to compute **cross-coupling**, where one frequency band’s rhythm modulates another band’s strength (e.g., theta phase controlling gamma amplitude). |

## Scalability and Business Model

The project has a phased approach for market entry and scaling:

1.  **Short Term (Data Collection & Validation):** Sell the experience to **exhibitions, experience parks, and immersive venues**. This generates early revenue and, crucially, feeds proprietary neuro-engagement data back into the model for fine-tuning.
2.  **Medium Term (Integration):** Partner with consumer EEG device providers (e.g., **Muse** and others) to integrate the video player functionality directly into existing EEG apps. This leverages the growing at-home adoption of EEG devices.
3.  **Long Term (Widespread Adoption):** As consumer EEG technology becomes democratized (e.g., via EEG earbuds like NextSense or potential AirPod patents), sell the core algorithm and technology to major **streaming platforms** (like Netflix or Amazon Prime Video) and virtual reality experience providers to reach a wider consumer base.

```
