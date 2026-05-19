"""
Basic agents are included in this module:
    - :func:`call_agent`
    - :func:`random_agent`
    - :func:`ai_agent`

"""

from typing import Tuple, Optional

from texasholdem.game.game import TexasHoldEm
from texasholdem.game.action_type import ActionType
from texasholdem.game.player_state import PlayerState
from texasholdem.agents.ai_clients import get_ai_client
from texasholdem.evaluator.evaluator import evaluate, get_rank_class, chen_formula
from texasholdem.util.log import logger

_client = None
_model = None


def _ensure_client():
    global _client, _model
    if _client is None:
        _client, _model = get_ai_client()
    return _client, _model


def _call_llm(client, model: str, prompt: str) -> str:
    """Dispatch to the appropriate LLM backend and return raw response text."""
    try:
        import anthropic
        if isinstance(client, anthropic.Anthropic):
            response = client.messages.create(
                model=model,
                max_tokens=50,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
    except ImportError:
        pass

    # Ollama — handle both object-style (>=0.4) and dict-style (<0.4) responses
    response = client.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    if hasattr(response, "message"):
        return response.message.content.strip()
    return response["message"]["content"].strip()


def _parse_response(text: str, game: TexasHoldEm) -> Tuple[ActionType, Optional[int]]:
    """Parse 'ACTION' or 'ACTION, amount' from the LLM response.

    Falls back to call_agent if the response can't be parsed.
    """
    try:
        parts = [p.strip() for p in text.split(",", 1)]
        action = ActionType[parts[0].upper()]
        total = None
        if len(parts) > 1 and parts[1]:
            digits = "".join(c for c in parts[1] if c.isdigit())
            total = int(digits) if digits else None
        return action, total
    except (KeyError, ValueError):
        return call_agent(game)


def call_agent(game: TexasHoldEm) -> Tuple[ActionType, None]:
    """
    A player that calls if another player raised or checks.

    Arguments:
        game (TexasHoldEm): The TexasHoldEm game
    Returns:
        Tuple[ActionType, None]: CALL if someone raised, else CHECK

    """
    player = game.players[game.current_player]
    if player.state == PlayerState.TO_CALL:
        return ActionType.CALL, None
    return ActionType.CHECK, None


def random_agent(game: TexasHoldEm, no_fold: bool = False) -> Tuple[ActionType, int]:
    """
    A uniformly random player

        - If someone raised, CALL, FOLD, or RAISE with uniform probability
        - Else, CHECK, (FOLD if no_fold=False), RAISE with uniform probability
        - If RAISE, the value will be uniformly random in [min_raise, # of chips]

    Arguments:
        game (TexasHoldEm): The TexasHoldEm game
        no_fold (bool): Removes the possibility of folding if no one raised, default False.
    Returns:
        Tuple[ActionType, int]: Returns a uniformly random action from the
            available moves.

    """
    moves = game.get_available_moves()
    if no_fold:
        del moves[ActionType.FOLD]

    return moves.sample()


def logical_agent(game: TexasHoldEm) -> Tuple[ActionType, Optional[int]]:
    """
    A simple rule-based agent that considers hand strength and position.
    """
    if len(game.board) < 3:
        # Pre-flop: play only strong hands (top 20% by rank)
        chen = chen_formula(game.get_hand(game.current_player))
        if chen >= 7:  # Chen formula score of 7 or higher is roughly top 20%
            return ActionType.CALL, None
        else:
            return ActionType.FOLD, None        

    rank = evaluate(game.get_hand(game.current_player), game.board)
    rank_class = get_rank_class(rank)
    if rank_class == 1:
        return ActionType.ALL_IN, None
    elif rank_class <= 2:
        return ActionType.RAISE, game.minimum_raise
    elif rank_class <= 4:
        return ActionType.CALL, None
    else:
        return ActionType.FOLD, None


def ai_agent(game: TexasHoldEm, risk_tolerance: int = 5) -> Tuple[ActionType, Optional[int]]:
    """
    An AI-powered poker agent backed by a local Ollama model or Anthropic Claude.

    The client is initialised lazily on the first call and reused for all
    subsequent calls (one shared client across all AI players).

    Arguments:
        game (TexasHoldEm): The TexasHoldEm game
        risk_tolerance (int): 0 = extremely conservative, 10 = extremely aggressive.
            Default 5.
    Returns:
        Tuple[ActionType, Optional[int]]: The chosen action and, for RAISE, the
            total amount to raise to.

    """
    assert 0 <= risk_tolerance <= 10

    client, model = _ensure_client()

    prompt = (
        f"You are playing Texas Hold'em poker. "
        f"Your risk tolerance is {risk_tolerance} out of 10 "
        f"(0 = extremely conservative, 10 = extremely aggressive).\n\n"
        f"{game.get_game_state()}\n\n"
        f"Respond with ONLY a single line in this exact format:\n"
        f"  ACTION, amount\n"
        f"Rules:\n"
        f"- ACTION must be one of: FOLD, CHECK, CALL, RAISE, ALL_IN\n"
        f"- Include amount only for RAISE (the total chips to raise to); omit it otherwise\n"
        f"- Do not include any explanation, just the action line\n"
        f"Examples: CALL    |    FOLD    |    RAISE, 150    |    ALL_IN"
    )
    logger.info(f"AI Agent Prompt:\n{prompt}")

    try:
        text = _call_llm(client, model, prompt)
        return _parse_response(text, game)
    except Exception:
        return call_agent(game)
