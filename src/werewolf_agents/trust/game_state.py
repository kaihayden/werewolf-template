from enum import Enum

class Role(Enum):
    VILLAGER = "villager"
    DOCTOR = "doctor"
    SEER = "seer"
    WOLF = "wolf"

class GameState():

  def __init__(self, player_list):
    self.player_list = player_list
    self.players_left = len(player_list)
    self.wolves_left = 2
    self.doctor_confirm_dead = False
    self.seer_confirm_dead = False
    self.first_known_wolf = False
    self.player_vote_history = [[] for p in player_list]
    self.player_action_history = [[] for p in player_list]
    self.player_alive_state = [True for p in player_list]


    self.player_role_claims = [None for p in player_list]
    self.player_role_claims_round = [None for p in player_list] # round in which player claimed the role
    self.player_role_confirmed = [False for p in player_list]

    self.player_accusation_history = [[None for p2 in player_list] for p in player_list]

    self.player_left_per_round = [self.player_left] # 0, start of game, 1 is after first kill phase
    self.wolf_kill_history = []
    self.lynch_history = []
    self.index_map = {string: index for index, string in enumerate(player_list)}
    self.current_round = 0

  def player_index(self, player_name):
    return self.index_map[player_name]
  
  def record_night_phase_death(self, player_name):
    self.wolf_kill_history.append(player_name)
    if player_name is not None:
      player_id = self.player_index(player_name)
      self.player_alive_state[player_id] = False
      self.players_left -= 1
      self.player_left_per_round.append(self.players_left)
    self.current_round += 1

  def record_vote(self, from_player_name, voted_player_name):
    player_id = self.player_index(from_player_name)
    self.player_vote_history[player_id].append(voted_player_name)

  def record_lynch(self, player_name, player_role): # roles: "villager", "doctor", "seer", "wolf"
    player_id = self.player_index(player_name)
    self.lynch_history.append(player_name)
    self.player_alive_state[player_id] = False
    self.player_role_confirmed[player_id] = player_role
    self.players_left -= 1
    if player_role == "wolf":
      self.wolves_left -= 1
    elif player_role == "seer":
      self.seer_confirm_dead = True
    elif player_role == "doctor":
      self.doctor_confirm_dead = True

  def claim_seer(self, player_name):
    player_id = self.player_index(player_name)
    self.player_role_claims[player_id] = "seer"
    self.player_role_claims_round = self.current_round

  def claim_doctor(self, player_name):
    player_id = self.player_index(player_name)
    self.player_role_claims[player_id] = "doctor"
    self.player_role_claims_round = self.current_round

  def claim_checked(self, player_name, player_checked_name, player_role, round_checked):
    player_id = self.player_index(player_name)
    to_player_id = self.player_index(player_checked_name)
    self.player_accusation_history[player_id][to_player_id] = {
      "round": round_checked,
      "role": player_role,
      "certainty": "confident"
    }

  def claim_saved(self, player_name, player_saved_name, round_saved):
    player_id = self.player_index(player_name)
    to_player_id = self.player_index(player_saved_name)
    self.player_accusation_history[player_id][to_player_id] = {
      "round": round_saved,
      "role": "good",
      "certainty": "confident"
    }

  def player_suggests(self, player_name, player_suggested_role_name, suggested_role, certainty): 
    """_summary_

    Args:
        player_name (str): 
        player_accused_name (str): 
        suggested_role ("villager", "doctor", "seer", wolf", "good"): _description_
        certainty ("guess" or "confident"):
    """
    player_id = self.player_index(player_name)
    to_player_id = self.player_index(player_suggested_role_name)
    self.player_accusation_history[player_id][to_player_id] = {
      "round": self.current_round,
      "role": suggested_role,
      "certainty": certainty
    }

  
