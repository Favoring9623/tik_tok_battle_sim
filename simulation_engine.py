import time
import random

class TikTokBattle:
    def __init__(self):
        self.time = 0
        self.creator_score = 0
        self.opponent_score = 0
        self.agents = []

    def add_agent(self, agent):
        self.agents.append(agent)

    def simulate(self):
        print("🎬 Starting TikTok Live Battle Simulation...\n")
        for t in range(60):
            self.time = t
            self._simulate_opponent_behavior()
            for agent in self.agents:
                agent.act(self)
            self._display_scores()
            time.sleep(0.25)  # Adjust to speed up or slow down sim

        print("\n🏁 Battle Over!")
        if self.creator_score > self.opponent_score:
            print("✅ Creator Wins!")
        else:
            print("❌ Opponent Wins!")

    def _simulate_opponent_behavior(self):
        # Random spike from opponent around 15s or 45s
        if self.time in [15, 45] and random.random() > 0.5:
            spike = random.randint(500, 1500)
            print(f"[OPPONENT SPIKE] Opponent gains {spike} points ⚡")
            self.opponent_score += spike

    def _display_scores(self):
        print(f"[{self.time:02d}s] Creator: {self.creator_score} | Opponent: {self.opponent_score}")


class AIBaseAgent:
    def __init__(self, name, creator_id="creator"):
        self.name = name
        self.creator_id = creator_id

    def act(self, battle: TikTokBattle):
        raise NotImplementedError()


class NovaWhale(AIBaseAgent):
    def __init__(self):
        super().__init__("NovaWhale")
        self.has_acted = False

    def act(self, battle):
        if battle.time >= 45 and not self.has_acted:
            if battle.creator_score < battle.opponent_score:
                print(f"{self.name} 🐋: Drops LION & UNIVERSE 🌌 at {battle.time}s")
                battle.creator_score += 1800
                self.has_acted = True
                if random.random() > 0.7:
                    print(f"{self.name}: 'The tide has turned.'")


class PixelPixie(AIBaseAgent):
    def __init__(self):
        super().__init__("PixelPixie")
        self.budget = 1000
        self.rose_value = 10

    def act(self, battle):
        if battle.time < 45 and self.budget >= self.rose_value:
            print(f"{self.name} 🧚‍♀️: Sends a ROSE 🌹 at {battle.time}s")
            battle.creator_score += self.rose_value
            self.budget -= self.rose_value
            if random.random() > 0.5:
                msg = random.choice([
                    "Let’s goooo! 🌟",
                    "You got this 💪✨",
                    "Battle mode ON! 🧚‍♀️",
                ])
                print(f"{self.name}: '{msg}'")


class GlitchMancer(AIBaseAgent):
    def __init__(self):
        super().__init__("GlitchMancer")
        self.cooldown = False

    def act(self, battle):
        trigger = (random.random() < 0.1) or (battle.time in [22, 38])
        if not self.cooldown and trigger:
            print(f"{self.name} 🌀: BURST mode activated!")
            for _ in range(random.randint(3, 6)):
                print(f"{self.name}: Sends TikTok gift 🎁")
                battle.creator_score += 60
            print(f"{self.name}: '{random.choice(['lol.wut.exe', 'gl!+cH @ct!vaT3d', '0000X⚡flash'])}'")
            self.cooldown = True

# Run the simulation
if __name__ == "__main__":
    battle = TikTokBattle()
    battle.add_agent(NovaWhale())
    battle.add_agent(PixelPixie())
    battle.add_agent(GlitchMancer())
    battle.simulate()
