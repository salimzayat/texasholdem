from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

from texasholdem.game.hand_phase import HandPhase

if TYPE_CHECKING:
    from texasholdem.game.game import TexasHoldEm


class PlayerPosition(Enum):
    """Positional classification of a player in the current betting circle."""

    EARLY = auto()
    MID = auto()
    LATE = auto()


def get_player_position(game: TexasHoldEm, player_id: int) -> PlayerPosition:
    """Return the positional classification of player_id in the current hand.

    The betting circle starts from bb_loc+1 during PREFLOP and from btn_loc+1
    in all other phases. Players are divided into thirds: the first third is
    EARLY, the middle third is MID, and the final third is LATE.

    Arguments:
        game (TexasHoldEm): The running game.
        player_id (int): The player to classify.
    Returns:
        PlayerPosition: EARLY, MID, or LATE.
    Raises:
        ValueError: If player_id is not an active (in-pot) player.
    """
    start = game.bb_loc + 1 if game.hand_phase == HandPhase.PREFLOP else game.btn_loc + 1
    ordered = list(game.in_pot_iter(loc=start))

    if player_id not in ordered:
        raise ValueError(f"Player {player_id} is not an active player in the current hand.")

    index = ordered.index(player_id)
    n = len(ordered)

    if index < n // 3:
        return PlayerPosition.EARLY
    if index < (2 * n) // 3:
        return PlayerPosition.MID
    return PlayerPosition.LATE
