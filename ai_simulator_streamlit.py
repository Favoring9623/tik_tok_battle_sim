import streamlit as st
import random
import time

# Simulated options for AI to choose from during battle
options = ["Mega Gift", "Protect Creator", "Launch Emote Storm", "Taunt Opponent"]

# --- Aggressive AI Decision Logic ---
def ai_aggressive_decision_making(options):
    if st.session_state.get("ascended_bonus") and options:
        weights = [random.uniform(1.2, 2.0) for _ in options]
        return random.choices(options, weights=weights)[0]
    return random.choice(options) if options else None

# --- Score Boost in Ascended Form ---
def apply_ascended_behavior(base_score):
    if st.session_state.get("ascended_bonus"):
        boosted = int(base_score * 2.0) + 250
        st.toast(f"🔥 Ascended boost applied: {boosted} points!")
        return boosted
    return base_score

# --- Simulate Battle Round ---
def simulate_battle_round(round_number):
    st.subheader(f"🌀 Battle Round {round_number}")
    base_score = random.randint(100, 500)
    ai_action = ai_aggressive_decision_making(options)
    boosted_score = apply_ascended_behavior(base_score)

    st.write(f"**AI Action:** {ai_action}")
    st.write(f"**Base Score:** {base_score}")
    st.write(f"**Final Score:** {boosted_score}")

# --- Setup Session State ---
st.set_page_config(page_title="AI Battle Simulation", layout="centered")
st.title("🎮 Tiktok AI Battle Simulator")
st.session_state.setdefault("ascended_bonus", False)

# --- Activate Ascension (for testing) ---
if st.button("🚀 Activate Ascended Form"):
    st.session_state["ascended_bonus"] = True
    st.success("AI has entered Ascended Form")

# --- Battle Simulation Loop ---
num_rounds = st.slider("Select Number of Rounds:", 1, 10, 3)
if st.button("▶️ Start Battle Simulation"):
    for i in range(1, num_rounds + 1):
        simulate_battle_round(i)
        time.sleep(0.5)
