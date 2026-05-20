"""Unit tests for get_player_position / PlayerPosition."""
import pytest

from texasholdem.game.game import TexasHoldEm
from texasholdem.game.player_position import PlayerPosition, get_player_position
from texasholdem.game.hand_phase import HandPhase
from texasholdem.game.action_type import ActionType


def _make_game(max_players: int = 9) -> TexasHoldEm:
    """Return a game in PREFLOP with all players active."""
    game = TexasHoldEm(buyin=500, big_blind=10, small_blind=5, max_players=max_players)
    game.start_hand()
    return game


# ---------------------------------------------------------------------------
# PREFLOP: circle starts at bb_loc + 1
# ---------------------------------------------------------------------------

def test_preflop_9_players_early():
    game = _make_game(9)
    assert game.hand_phase == HandPhase.PREFLOP
    ordered = list(game.in_pot_iter(loc=game.bb_loc + 1))
    # first third (indices 0, 1, 2) → EARLY
    for pid in ordered[:3]:
        assert get_player_position(game, pid) == PlayerPosition.EARLY


def test_preflop_9_players_mid():
    game = _make_game(9)
    ordered = list(game.in_pot_iter(loc=game.bb_loc + 1))
    # middle third (indices 3, 4, 5) → MID
    for pid in ordered[3:6]:
        assert get_player_position(game, pid) == PlayerPosition.MID


def test_preflop_9_players_late():
    game = _make_game(9)
    ordered = list(game.in_pot_iter(loc=game.bb_loc + 1))
    # last third (indices 6, 7, 8) → LATE
    for pid in ordered[6:]:
        assert get_player_position(game, pid) == PlayerPosition.LATE


# ---------------------------------------------------------------------------
# Post-flop: circle starts at btn_loc + 1
# ---------------------------------------------------------------------------

def _advance_to_flop(game: TexasHoldEm) -> TexasHoldEm:
    """Take CHECK/CALL actions until we reach the FLOP."""
    while game.hand_phase == HandPhase.PREFLOP:
        moves = game.get_available_moves()
        if ActionType.CHECK in moves.action_types:
            game.take_action(ActionType.CHECK)
        else:
            game.take_action(ActionType.CALL)
    return game


def test_flop_9_players_positions():
    game = _make_game(9)
    _advance_to_flop(game)
    assert game.hand_phase == HandPhase.FLOP

    ordered = list(game.in_pot_iter(loc=game.btn_loc + 1))
    n = len(ordered)

    for i, pid in enumerate(ordered):
        pos = get_player_position(game, pid)
        if i < n // 3:
            assert pos == PlayerPosition.EARLY
        elif i < (2 * n) // 3:
            assert pos == PlayerPosition.MID
        else:
            assert pos == PlayerPosition.LATE


# ---------------------------------------------------------------------------
# Edge cases: small player counts
# ---------------------------------------------------------------------------

def test_3_players_one_per_tier():
    game = _make_game(3)
    assert game.hand_phase == HandPhase.PREFLOP
    ordered = list(game.in_pot_iter(loc=game.bb_loc + 1))
    assert len(ordered) == 3
    assert get_player_position(game, ordered[0]) == PlayerPosition.EARLY
    assert get_player_position(game, ordered[1]) == PlayerPosition.MID
    assert get_player_position(game, ordered[2]) == PlayerPosition.LATE


def test_2_players_positions():
    game = _make_game(2)
    assert game.hand_phase == HandPhase.PREFLOP
    ordered = list(game.in_pot_iter(loc=game.bb_loc + 1))
    assert len(ordered) == 2
    # n=2: n//3=0, 2n//3=1 → index 0 → MID, index 1 → LATE
    assert get_player_position(game, ordered[0]) == PlayerPosition.MID
    assert get_player_position(game, ordered[1]) == PlayerPosition.LATE


# ---------------------------------------------------------------------------
# Error case
# ---------------------------------------------------------------------------

def test_player_not_in_pot_raises():
    game = _make_game(9)
    # Fold one player so they leave the pot
    while game.hand_phase == HandPhase.PREFLOP:
        folded_player = game.current_player
        game.take_action(ActionType.FOLD)
        break

    with pytest.raises(ValueError):
        get_player_position(game, folded_player)
