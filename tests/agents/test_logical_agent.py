"""Unit tests for logical_agent pre-flop position-based thresholds."""
from unittest.mock import patch

import pytest

from texasholdem.game.game import TexasHoldEm
from texasholdem.game.action_type import ActionType
from texasholdem.game.hand_phase import HandPhase
from texasholdem.game.player_position import PlayerPosition
from texasholdem.agents.basic import logical_agent


@pytest.fixture()
def preflop_game() -> TexasHoldEm:
    """Return a 9-player game stopped at PREFLOP."""
    game = TexasHoldEm(buyin=500, big_blind=10, small_blind=5, max_players=9)
    game.start_hand()
    assert game.hand_phase == HandPhase.PREFLOP
    return game


def _run_preflop(game: TexasHoldEm, position: PlayerPosition, chen: float):
    """Call logical_agent with mocked position and chen score."""
    with (
        patch(
            "texasholdem.agents.basic.get_player_position",
            return_value=position,
        ),
        patch(
            "texasholdem.agents.basic.chen_formula",
            return_value=chen,
        ),
    ):
        return logical_agent(game)


# ---------------------------------------------------------------------------
# EARLY position
# ---------------------------------------------------------------------------

class TestEarlyPosition:
    def test_raise_at_threshold(self, preflop_game):
        action, _ = _run_preflop(preflop_game, PlayerPosition.EARLY, chen=9)
        assert action == ActionType.RAISE

    def test_raise_above_threshold(self, preflop_game):
        action, _ = _run_preflop(preflop_game, PlayerPosition.EARLY, chen=12)
        assert action == ActionType.RAISE

    def test_call_at_threshold(self, preflop_game):
        action, _ = _run_preflop(preflop_game, PlayerPosition.EARLY, chen=8)
        assert action == ActionType.CALL

    def test_fold_below_call_threshold(self, preflop_game):
        action, _ = _run_preflop(preflop_game, PlayerPosition.EARLY, chen=7)
        assert action == ActionType.FOLD

    def test_fold_well_below_threshold(self, preflop_game):
        action, _ = _run_preflop(preflop_game, PlayerPosition.EARLY, chen=0)
        assert action == ActionType.FOLD


# ---------------------------------------------------------------------------
# MID position
# ---------------------------------------------------------------------------

class TestMidPosition:
    def test_raise_at_threshold(self, preflop_game):
        action, _ = _run_preflop(preflop_game, PlayerPosition.MID, chen=9)
        assert action == ActionType.RAISE

    def test_raise_above_threshold(self, preflop_game):
        action, _ = _run_preflop(preflop_game, PlayerPosition.MID, chen=11)
        assert action == ActionType.RAISE

    def test_call_at_threshold(self, preflop_game):
        action, _ = _run_preflop(preflop_game, PlayerPosition.MID, chen=7)
        assert action == ActionType.CALL

    def test_call_between_thresholds(self, preflop_game):
        action, _ = _run_preflop(preflop_game, PlayerPosition.MID, chen=8)
        assert action == ActionType.CALL

    def test_fold_below_call_threshold(self, preflop_game):
        action, _ = _run_preflop(preflop_game, PlayerPosition.MID, chen=6)
        assert action == ActionType.FOLD

    def test_fold_well_below_threshold(self, preflop_game):
        action, _ = _run_preflop(preflop_game, PlayerPosition.MID, chen=0)
        assert action == ActionType.FOLD


# ---------------------------------------------------------------------------
# LATE position
# ---------------------------------------------------------------------------

class TestLatePosition:
    def test_raise_at_threshold(self, preflop_game):
        action, _ = _run_preflop(preflop_game, PlayerPosition.LATE, chen=9)
        assert action == ActionType.RAISE

    def test_raise_above_threshold(self, preflop_game):
        action, _ = _run_preflop(preflop_game, PlayerPosition.LATE, chen=10)
        assert action == ActionType.RAISE

    def test_call_at_threshold(self, preflop_game):
        action, _ = _run_preflop(preflop_game, PlayerPosition.LATE, chen=6)
        assert action == ActionType.CALL

    def test_call_between_thresholds(self, preflop_game):
        action, _ = _run_preflop(preflop_game, PlayerPosition.LATE, chen=8)
        assert action == ActionType.CALL

    def test_fold_below_call_threshold(self, preflop_game):
        action, _ = _run_preflop(preflop_game, PlayerPosition.LATE, chen=5)
        assert action == ActionType.FOLD

    def test_fold_well_below_threshold(self, preflop_game):
        action, _ = _run_preflop(preflop_game, PlayerPosition.LATE, chen=0)
        assert action == ActionType.FOLD


# ---------------------------------------------------------------------------
# Post-flop: position logic is not applied; rank-class logic takes over
# ---------------------------------------------------------------------------

class TestPostFlopUnchanged:
    """Ensure post-flop behaviour is unaffected by position changes."""

    def _advance_to_flop(self, game: TexasHoldEm) -> TexasHoldEm:
        while game.hand_phase == HandPhase.PREFLOP:
            if ActionType.CHECK in game.get_available_moves().action_types:
                game.take_action(ActionType.CHECK)
            else:
                game.take_action(ActionType.CALL)
        return game

    def test_postflop_rank_class_1_all_in(self, preflop_game):
        self._advance_to_flop(preflop_game)
        with (
            patch("texasholdem.agents.basic.evaluate", return_value=1),
            patch("texasholdem.agents.basic.get_rank_class", return_value=1),
        ):
            action, _ = logical_agent(preflop_game)
        assert action == ActionType.ALL_IN

    def test_postflop_rank_class_2_raise(self, preflop_game):
        self._advance_to_flop(preflop_game)
        with (
            patch("texasholdem.agents.basic.evaluate", return_value=100),
            patch("texasholdem.agents.basic.get_rank_class", return_value=2),
        ):
            action, _ = logical_agent(preflop_game)
        assert action == ActionType.RAISE

    def test_postflop_rank_class_4_call(self, preflop_game):
        self._advance_to_flop(preflop_game)
        with (
            patch("texasholdem.agents.basic.evaluate", return_value=500),
            patch("texasholdem.agents.basic.get_rank_class", return_value=4),
        ):
            action, _ = logical_agent(preflop_game)
        assert action == ActionType.CALL

    def test_postflop_rank_class_5_fold(self, preflop_game):
        self._advance_to_flop(preflop_game)
        with (
            patch("texasholdem.agents.basic.evaluate", return_value=1000),
            patch("texasholdem.agents.basic.get_rank_class", return_value=5),
        ):
            action, _ = logical_agent(preflop_game)
        assert action == ActionType.FOLD
