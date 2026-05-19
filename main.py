from texasholdem.game.game import TexasHoldEm
from texasholdem.gui.text_gui import TextGUI

from texasholdem.agents.basic import call_agent, random_agent, ai_agent
import random

player_agents = {
    1: call_agent,
    2: random_agent,
    3: (ai_agent, random.randint(1, 10)),
    4: random_agent,
    5: call_agent
    # ... player 0 absent = human
}

game = TexasHoldEm(buyin=500, big_blind=5, small_blind=2, max_players=len(player_agents)+1)
gui = TextGUI(game=game, human_players=[0])


game.start_hand()
while game.is_game_running():
    if not game.is_hand_running():
        game.start_hand()
    lookup = player_agents.get(game.current_player)
    if isinstance(lookup, tuple):
        agent = lookup[0]
        kwargs = {'risk_tolerance': lookup[1]}
    else:
        agent = lookup
        kwargs = {}
    gui.run_step(agent=agent, **kwargs)