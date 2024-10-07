import numpy as np
import tensorflow as tf
from phase import Phase
from action import Action
import action_choices
import os


from .agent_q_reward_shaping_with_replay_frame import AgentDQNReplayFrame

"""
This agent use DQN to perform the best action.
0517_r0_d0_p9_T300_replay_frame_lr0.0001_delta0.9.keras
"""
np.random.seed(15)

current_path = os.path.dirname(os.path.realpath(__file__))
read_dqn_path = current_path + "/agent_dqn/0517_r0_d0_p9_T300_replay_frame_lr0.0001_delta0.9.keras"
DQN = AgentDQNReplayFrame()
DQN.initialize(learning=False, read_dqn_path=read_dqn_path)

EPSILON = 0


def make_decision(current_gameboard, player_name):
    observation, info = get_observation_info(current_gameboard, player_name)
    print(info)
    action_mask = info["action_masks"]
    action_mask_bool = info["action_masks"].astype(bool)
    all_action_list = np.array(list(range(6)))
    allowable_actions = all_action_list[action_mask_bool]

    user_action = DQN.action(observation, 0, False, False, info)
    return user_action


def make_pre_flop_moves(player, current_gameboard, allowable_actions):
    """Strategies for agent in pre-flop round
    Args:
        player
        current_gameboard
        allowable_actions

    Returns:
        function
    """
    return make_decision(current_gameboard, player.player_name)


def make_flop_moves(player, current_gameboard, allowable_actions):
    """Strategies for agent in flop round

    Args:
        player
        current_gameboard
        allowable_actions

    Returns:
        function
    """
    # parameters the agent need to take actions with
    return make_decision(current_gameboard, player.player_name)

def make_turn_moves(player, current_gameboard, allowable_actions):
    """Strategies for agent in flop round
    Args:
        player
        current_gameboard
        allowable_actions

    Returns:
        function
    """

    # parameters the agent need to take actions with
    return make_decision(current_gameboard, player.player_name)


def make_river_moves(player, current_gameboard, allowable_actions):
    """Strategies of agent in river round

    Args:
        player
        current_gameboard
        allowable_actions

    Returns:
        function
    """
    return make_decision(current_gameboard, player.player_name)


def _build_decision_agent_methods_dict():
    """
    This function builds the decision agent methods dictionary.
    :return: The decision agent dict. Keys should be exactly as stated in this example, but the functions can be anything
    as long as you use/expect the exact function signatures we have indicated in this document.
    """
    ans = dict()
    ans["make_pre_flop_moves"] = make_pre_flop_moves
    ans["make_flop_moves"] = make_flop_moves
    ans["make_turn_moves"] = make_turn_moves
    ans["make_river_moves"] = make_river_moves
    ans["strategy_type"] = "agent_random"

    return ans


decision_agent_methods = _build_decision_agent_methods_dict()


def get_observation_info(current_gameboard, player_name):
    observation = _get_obs(current_gameboard, player_name)
    info = _get_info(current_gameboard, player_name)

    return observation, info



def _get_obs(current_gameboard, player_name, stopped=False):
    player_status, bankroll = _get_status_and_bankroll_info(current_gameboard)
    return {
        "player_status": player_status,
        "bankroll": bankroll,
        "position": _get_position_info(current_gameboard, player_name),
        "hole_cards": _get_hole_cards_info(current_gameboard, player_name, stopped=stopped),
        "community_card": _get_community_card_info(current_gameboard),
        "action": _get_action_info(current_gameboard),
        "pot_amount": _get_pot_amount(current_gameboard),
        "game_idx": _get_game_index(current_gameboard),
    }


def _get_info(current_gameboard, player_name, stopped=False):
    """
    PARAMS:
        stopped(bool): True if terminated or truncated, there is no need to show action_masks
    """
    output_info_dict = dict()

    # player_name_list
    player_name_list = []
    for player in current_gameboard["players"]:
        player_name_list.append(player.player_name)

    if not stopped:
        # action_masks
        player_obj = current_gameboard["players_dict"][player_name]
        if player_obj.status == "lost":
            raise

        if current_gameboard["board"].cur_phase == Phase.PRE_FLOP:
            allowable_actions = player_obj.compute_allowable_pre_flop_actions(current_gameboard)
        elif current_gameboard["board"].cur_phase == Phase.FLOP:
            allowable_actions = player_obj.compute_allowable_flop_actions(current_gameboard)
        elif current_gameboard["board"].cur_phase == Phase.TURN:
            allowable_actions = player_obj.compute_allowable_turn_actions(current_gameboard)
        elif current_gameboard["board"].cur_phase == Phase.RIVER:
            allowable_actions = player_obj.compute_allowable_river_actions(current_gameboard)
        else:
            raise

        allowable_string = [action.name for action in allowable_actions]
        action_masks = []
        for action in ["CALL", "BET", "RAISE_BET", "CHECK", "FOLD", "ALL_IN"]:
            if action in allowable_string:
                action_masks.append(1)
            else:
                action_masks.append(0)

    # showdown
    showdown = []
    if current_gameboard["board"].previous_showdown:
        for hands in current_gameboard["board"].previous_showdown:
            tem_hand = []
            for card in hands:
                if card:
                    tem_hand.append(_card_encoder(card))
                else:
                    tem_hand.append(-1)
            showdown.append(tem_hand)

    # return
    output_info_dict["player_name_list"] = player_name_list
    if not stopped:
        output_info_dict["action_masks"] = np.array(action_masks)
    output_info_dict["previous_showdown"] = showdown

    return output_info_dict



def _get_status_and_bankroll_info(current_gameboard):
    player_status_list = []
    bankroll_list = []
    for player in current_gameboard["players"]:
        if player.status == "lost":
            player_status_list.append(0)
            bankroll_list.append(-1)
        else:
            player_status_list.append(1)
            bankroll_list.append(player.current_cash)
    return (np.array(player_status_list, dtype=np.int64), np.array(bankroll_list, dtype=np.int64))


def _get_position_info(current_gameboard, player_name):
    # [dealer position, player_position]
    player_position_idx = -1
    for idx, player in enumerate(current_gameboard["players"]):
        if player.player_name == player_name:
            player_position_idx = idx
            break
    if player_position_idx == -1:
        raise ("player_position_idx should not be -1, please check _get_position_info")

    return np.array([current_gameboard["board"].dealer_position, player_position_idx], dtype=np.int64)


def _get_hole_cards_info(current_gameboard, player_name, stopped=False):
    # [card1, card2]
    hole_cards = []
    for idx, player in enumerate(current_gameboard["players"]):
        if player.player_name == player_name:
            hole_cards = player.hole_cards
            break
    if not stopped and not hole_cards:
        raise ("player's hole_cards should not be empty, please check _get_hole_cards_info")

    card_list = []
    for card in hole_cards:
        card_list.append(_card_encoder(card))
    return np.array(card_list, dtype=np.int64)


def _get_community_card_info(current_gameboard):
    # [flop1. flop2, flop3, turn, river]
    current_community_card = []
    for card in current_gameboard["board"].community_cards:
        current_community_card.append(_card_encoder(card))

    return np.array(current_community_card + [-1] * (5 - len(current_community_card)), dtype=np.int64)


def _get_action_info(current_gameboard):
    players_last_move_list_encode = []
    for move in current_gameboard["board"].players_last_move_list_hist:
        if move in [Action.SMALL_BLIND, Action.BIG_BLIND, Action.NONE]:
            # which mean they didn't move
            players_last_move_list_encode.append(-1)
        else:
            players_last_move_list_encode.append(_action_encoder(move))

    return np.array(players_last_move_list_encode, dtype=np.int64)


def _get_pot_amount(current_gameboard):
    # get the amount (included main pot and side pot)

    total_amount = 0

    # amount in previous round
    total_amount += sum(current_gameboard["board"].pots_amount_list)

    # amount in current round

    for player_name in current_gameboard["board"].player_pot:
        total_amount += current_gameboard["board"].player_pot[player_name]

    return np.array([total_amount])


def _get_game_index(current_gameboard):
    return np.array([current_gameboard["board"].game_idx])


def _card_encoder(card):
    """decode Card object into int
    Args:
        card: Card object

    Returns:
        card_code:int (1~52)

    Raises:


    """
    # assert isinstance(card, Card)
    if card.suit == "spade":
        suit_idx = 0
    elif card.suit == "heart":
        suit_idx = 1
    elif card.suit == "diamond":
        suit_idx = 2
    elif card.suit == "club":
        suit_idx = 3
    else:
        raise ("please check card.suit, current value = " + card.suit)

    return int(suit_idx * 13 + card.number)


def _action_encoder(move):
    action_map = {
        Action.LOST: -1,
        Action.NONE: -1,
        Action.CALL: 0,
        Action.BET: 1,
        Action.RAISE_BET: 2,
        Action.CHECK: 3,
        Action.FOLD: 4,
        Action.ALL_IN: 5,
        Action.ALL_IN_ALREADY: 5,
    }
    return action_map[move]


def _action_decoder(action):
    """
    Decode integer action into function and the correspongind parameters
    Args:
        player(Player): the Player object representing gym user
        action(int): the action got from gym user
    Returns:
        action_function
        parameters
    """
    if action == 0:
        action_function = action_choices.call
    elif action == 1:
        action_function = action_choices.bet
    elif action == 2:
        action_function = action_choices.raise_bet
    elif action == 3:
        action_function = action_choices.check
    elif action == 4:
        action_function = action_choices.fold
    elif action == 5:
        action_function = action_choices.all_in
    else:
        raise
    return action_function
