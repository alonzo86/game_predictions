import re
import statistics
from tkinter import Canvas, StringVar
from typing import Optional

from utils import safe_div, get_dictionary_item_by_property


class Player:
    def __init__(self, player_id: int, player_data):
        self.id = player_id
        self.shirt_number = player_data['shirtNumber']
        self.position = player_data['position']
        self.first_name = player_data['firstName']
        self.last_name = player_data['lastName']
        stats = player_data['stats']['902']['19/20'][0]
        self.id_in_stats = stats['playerInstatId']
        self.lost_ball = stats.get('lostBall', 0)
        self.own_half_lost_ball = stats.get('ownHalfLostBall', 0)
        self.ball_recovery = stats.get('ballRecovery', 0)
        self.ball_recovery_in_opp_half = stats.get('ballRecoveryInOppHalf', 0)
        self.ball_recovery_in_own_half = stats.get('ballRecoveryInOwnHalf', 0)
        self.tackles = stats.get('tackles', 0)
        self.tackles_success = stats.get('tacklesSuccess', 0)
        self.foul = stats.get('foul', 0)
        self.yellow_card = stats.get('YellowCard', 0)
        self.red_card = stats.get('RedCard', 0)
        self.penalty_kick = stats.get('PenaltyKick', 0)
        self.penalty_shot_goal = stats.get('PenaltyShot_Goal', 0)
        self.regular_goals = stats.get('GoalRegular', 0)
        self.attempts_on_goal = stats.get('AttemptonGoal', 0)
        self.shots_inside_the_area = stats.get('ShotInsidetheArea', 0)
        self.shots_outside_the_area = stats.get('ShotOutsidetheArea', 0)
        self.shots_on_target = stats.get('OnTarget', 0)
        self.shots_off_target = stats.get('OffTarget', 0)
        self.left_side_attacks = stats.get('leftSideAttack', 0)
        self.left_side_attacks_with_shot = stats.get('leftSideAttackWithShot', 0)
        self.center_attacks = stats.get('centerAttack', 0)
        self.center_attacks_with_shot = stats.get('centerAttackWithShot', 0)
        self.right_side_attacks = stats.get('rightSideAttack', 0)
        self.right_side_attacks_with_shot = stats.get('rightSideAttackWithShot', 0)
        self.crosses = stats.get('Cross', 0)
        self.direct_crosses_into_the_area = stats.get('DirectCrossintotheArea', 0)
        self.passes = stats.get('passes', 0)
        self.attacking_passes = stats.get('attackingPasses', 0)
        self.key_passes = stats.get('keyPasses', 0)
        self.air_challenge = stats.get('airChallenge', 0)
        self.air_challenge_won = stats.get('wonAirChallenge', 0)
        self.ground_challenge = stats.get('groundChallenge', 0)
        self.ground_challenge_won = stats.get('wonGroundChallenge', 0)
        self.dribbles = stats.get('dribble', 0)
        self.won_dribbles = stats.get('wonDribble', 0)


class TeamStats:
    def __init__(self, team_stats=None):
        self.goals = 0
        self.ball_possession = 0
        self.own_half_ball_losses = 0
        self.opponent_half_ball_recoveries = 0
        self.own_half_ball_recoveries = 0
        self.successful_tackles = 0
        self.fouls = 0
        self.yellow_cards = 0
        self.red_cards = 0
        self.penalty_kick_goals = 0
        self.shots_on_goal = 0
        self.shots_inside_the_area = 0
        self.shots_outside_the_area = 0
        self.shots_on_target = 0
        self.shots_off_target = 0
        self.shots_after_left_side_attacks = 0
        self.shots_after_center_attacks = 0
        self.shots_after_right_side_attacks = 0
        self.direct_crosses_into_the_area = 0
        self.attacking_passes = 0
        self.key_passes = 0
        self.air_challenges_won = 0
        self.ground_challenges_won = 0
        self.dribbles_won = 0

        if team_stats is None:
            return

        # Ball Possession
        tmp_lost_balls = team_stats.get('lostBall', 0)
        tmp_own_half_lost_ball = team_stats.get('ownHalfLostBall', 0)
        tmp_ball_possession = team_stats.get('ballPossession', 0)
        tmp_ball_recovery = team_stats.get('ballRecovery', 0)
        tmp_ball_recovery_in_opponent_half = team_stats.get('ballRecoveryInOppHalf', 0)
        tmp_ball_recovery_in_own_half = team_stats.get('ballRecoveryInOwnHalf', 0)

        ball_possession = tmp_ball_possession / 100
        own_half_ball_losses = safe_div(tmp_own_half_lost_ball, tmp_lost_balls)
        opponent_half_ball_recoveries = safe_div(tmp_ball_recovery_in_opponent_half, tmp_ball_recovery)
        own_half_ball_recoveries = safe_div(tmp_ball_recovery_in_own_half, tmp_ball_recovery)

        # Cards
        tmp_tackles = team_stats.get('tackles', 0)
        tmp_successful_tackles = team_stats.get('tacklesSuccess', 0)
        tmp_fouls = team_stats.get('foul', 0)
        tmp_yellow_cards = team_stats.get('YellowCard', 0)
        tmp_red_cards = team_stats.get('RedCard', 0)

        successful_tackles = safe_div(tmp_successful_tackles, tmp_tackles)
        fouls = safe_div(tmp_fouls, tmp_tackles)
        yellow_cards = safe_div(tmp_yellow_cards, tmp_fouls)
        red_cards = safe_div(tmp_red_cards, tmp_fouls)

        # Penalties
        tmp_penalty_kicks = team_stats.get('PenaltyKick', 0)
        tmp_penalty_kick_goals = team_stats.get('PenaltyShot_Goal', 0)
        # tmp_missed_penalty = team_stats.get('MissedPenalty', 0)

        penalty_kick_goals = safe_div(tmp_penalty_kick_goals, tmp_penalty_kicks)

        # Goals
        tmp_regular_goals = team_stats.get('GoalRegular', 0)
        tmp_attempts_on_goal = team_stats.get('AttemptonGoal', 0)
        tmp_shots_inside_the_area = team_stats.get('ShotInsidetheArea', 0)
        tmp_shots_outside_the_area = team_stats.get('ShotOutsidetheArea', 0)
        tmp_shots_on_target = team_stats.get('OnTarget', 0)
        tmp_shots_off_target = team_stats.get('missedShot', 0)
        # tmp_blocked_shots = team_stats.get('blockedShot', 0)
        tmp_left_side_attacks = team_stats.get('leftSideAttack', 0)
        tmp_left_side_attacks_with_shot = team_stats.get('leftSideAttackWithShot', 0)
        tmp_center_attacks = team_stats.get('centerAttack', 0)
        tmp_center_attacks_with_shot = team_stats.get('centerAttackWithShot', 0)
        tmp_right_side_attacks = team_stats.get('rightSideAttack', 0)
        tmp_right_side_attacks_with_shot = team_stats.get('rightSideAttackWithShot', 0)

        shots_on_goal = safe_div(tmp_regular_goals, tmp_attempts_on_goal)
        shots_inside_the_area = safe_div(tmp_shots_inside_the_area, tmp_attempts_on_goal)
        shots_outside_the_area = safe_div(tmp_shots_outside_the_area, tmp_attempts_on_goal)
        shots_on_target = safe_div(tmp_shots_on_target, tmp_attempts_on_goal)
        shots_off_target = safe_div(tmp_shots_off_target, tmp_attempts_on_goal)
        shots_after_left_side_attacks = safe_div(tmp_left_side_attacks_with_shot, tmp_left_side_attacks)
        shots_after_center_attacks = safe_div(tmp_center_attacks_with_shot, tmp_center_attacks)
        shots_after_right_side_attacks = safe_div(tmp_right_side_attacks_with_shot, tmp_right_side_attacks)

        # Crossing
        tmp_crosses = team_stats.get('Cross', 0)
        tmp_direct_crosses_into_the_area = team_stats.get('DirectCrossintotheArea', 0)
        # tmp_headers = team_stats.get('Header', 0)

        direct_crosses_into_the_area = safe_div(tmp_direct_crosses_into_the_area, tmp_crosses)

        # Passing
        tmp_passes = team_stats.get('passes', 0)
        # tmp_non_attacking_passes = team_stats.get('nonAttackingPasses', 0)
        tmp_attacking_passes = team_stats.get('attackingPasses', 0)
        # tmp_accurate_passes = team_stats.get('accuratePasses', 0)
        tmp_key_passes = team_stats.get('keyPasses', 0)
        # tmp_long_balls = team_stats.get('longBall', 0)
        # tmp_accurate_long_balls = team_stats.get('accurateLongBall', 0)

        attacking_passes = safe_div(tmp_attacking_passes, tmp_passes)
        key_passes = safe_div(tmp_key_passes, tmp_attacking_passes)

        # Challenges
        tmp_air_challenges = team_stats.get('airChallenge', 0)
        tmp_air_challenges_won = team_stats.get('wonAirChallenge', 0)
        tmp_ground_challenges = team_stats.get('groundChallenge', 0)
        tmp_ground_challenges_won = team_stats.get('wonGroundChallenge', 0)
        tmp_dribbles = team_stats.get('dribble', 0)
        tmp_dribbles_won = team_stats.get('wonDribble', 0)

        air_challenges_won = safe_div(tmp_air_challenges_won, tmp_air_challenges)
        ground_challenges_won = safe_div(tmp_ground_challenges_won, tmp_ground_challenges)
        dribbles_won = safe_div(tmp_dribbles_won, tmp_dribbles)

        self.goals = tmp_regular_goals
        self.ball_possession = ball_possession
        self.own_half_ball_losses = own_half_ball_losses
        self.opponent_half_ball_recoveries = opponent_half_ball_recoveries
        self.own_half_ball_recoveries = own_half_ball_recoveries
        self.successful_tackles = successful_tackles
        self.fouls = fouls
        self.yellow_cards = yellow_cards
        self.red_cards = red_cards
        self.penalty_kick_goals = penalty_kick_goals
        self.shots_on_goal = shots_on_goal
        self.shots_inside_the_area = shots_inside_the_area
        self.shots_outside_the_area = shots_outside_the_area
        self.shots_on_target = shots_on_target
        self.shots_off_target = shots_off_target
        self.shots_after_left_side_attacks = shots_after_left_side_attacks
        self.shots_after_center_attacks = shots_after_center_attacks
        self.shots_after_right_side_attacks = shots_after_right_side_attacks
        self.direct_crosses_into_the_area = direct_crosses_into_the_area
        self.attacking_passes = attacking_passes
        self.key_passes = key_passes
        self.air_challenges_won = air_challenges_won
        self.ground_challenges_won = ground_challenges_won
        self.dribbles_won = dribbles_won

    def add_player_stats(self, player_stats: Player):
        self.own_half_ball_losses += safe_div(player_stats.own_half_lost_ball, player_stats.lost_ball) / 11
        self.opponent_half_ball_recoveries += safe_div(player_stats.ball_recovery_in_opp_half, player_stats.ball_recovery) / 11
        self.own_half_ball_recoveries += safe_div(player_stats.ball_recovery_in_own_half, player_stats.ball_recovery) / 11
        self.successful_tackles += safe_div(player_stats.tackles_success, player_stats.tackles) / 11
        self.fouls += safe_div(player_stats.foul, player_stats.tackles) / 11
        self.yellow_cards += safe_div(player_stats.yellow_card, player_stats.foul) / 11
        self.red_cards += safe_div(player_stats.red_card, player_stats.foul) / 11
        self.penalty_kick_goals += safe_div(player_stats.penalty_shot_goal, player_stats.penalty_kick) / 11
        self.shots_on_goal += safe_div(player_stats.regular_goals, player_stats.attempts_on_goal) / 11
        self.shots_inside_the_area += safe_div(player_stats.shots_inside_the_area, player_stats.attempts_on_goal) / 11
        self.shots_outside_the_area += safe_div(player_stats.shots_outside_the_area, player_stats.attempts_on_goal) / 11
        self.shots_on_target += safe_div(player_stats.shots_on_target, player_stats.attempts_on_goal) / 11
        self.shots_off_target += safe_div(player_stats.shots_off_target, player_stats.attempts_on_goal) / 11
        self.shots_after_right_side_attacks += safe_div(player_stats.right_side_attacks_with_shot, player_stats.right_side_attacks) / 11
        self.shots_after_center_attacks += safe_div(player_stats.center_attacks_with_shot, player_stats.center_attacks) / 11
        self.shots_after_left_side_attacks += safe_div(player_stats.left_side_attacks_with_shot, player_stats.left_side_attacks) / 11
        self.direct_crosses_into_the_area += safe_div(player_stats.direct_crosses_into_the_area, player_stats.crosses) / 11
        self.attacking_passes += safe_div(player_stats.attacking_passes, player_stats.passes) / 11
        self.key_passes += safe_div(player_stats.key_passes, player_stats.attacking_passes) / 11
        self.air_challenges_won += safe_div(player_stats.air_challenge_won, player_stats.air_challenge) / 11
        self.ground_challenges_won += safe_div(player_stats.ground_challenge_won, player_stats.ground_challenge) / 11
        self.dribbles_won += safe_div(player_stats.won_dribbles, player_stats.dribbles) / 11


class Lineup:
    def __init__(self, formation):
        self.formation = formation
        self.players = []


class LineupPlayer:
    def __init__(self, player: Player, shirt_number, position):
        self.id = player.id
        self.name = player.last_name
        self.shirt_number = shirt_number
        self.position = position


class Team:
    def __init__(self, team_id, team_info):
        self.id = team_id
        self.possession = None
        self.name = team_info['hebrewName']
        self.player_uniform_color = team_info['color'] if 'color' in team_info else '#fff'
        self.goalie_uniform_color = team_info['goalieColor'] if 'goalieColor' in team_info else '#fff'
        self.players = {}
        self.latest_lineup = None

    def get_player_by_id(self, player_id: int):
        return self.players.get(player_id, None)

    def get_player_by_stat_id(self, player_id_in_stats: int) -> Optional[Player]:
        return get_dictionary_item_by_property(self.players, 'id_in_stats', player_id_in_stats)

    def add_player(self, player_id: int, player_data):
        existing_player = self.get_player_by_id(player_id)
        if existing_player is not None:
            return
        player = Player(player_id, player_data)
        self.players[player_id] = player

    def set_possession(self, season_possession):
        possession = []
        for game_index in season_possession.keys():
            if season_possession[game_index]['stage'] == 'RegularSeason':
                possession.append(season_possession[game_index]['ballPossession'])
        self.possession = statistics.mean(possession) / 100

    def set_latest_lineup(self, latest_lineup):
        self.latest_lineup = Lineup(self.parse_team_formation(latest_lineup['starting_tactic']))
        players = latest_lineup['player']
        for lineup_player in players:
            if lineup_player['starting_position_name'] == 'Substitute player':
                continue
            player_id_in_stat = int(lineup_player['id'])
            shirt_number = lineup_player['num']
            starting_position_name = lineup_player['starting_position_name']
            player = self.get_player_by_stat_id(player_id_in_stat)
            if player is not None:
                self.latest_lineup.players.append(LineupPlayer(player, shirt_number, starting_position_name))

    @staticmethod
    def parse_team_formation(formation: str):
        delimiter = '-'
        formation_parts = re.findall(r'\d+', formation)
        return delimiter.join(list(map(str, formation_parts)))


class SubstitutePlayer:
    def __init__(self, canvas: Canvas, player_canvas_id: int, player_id: int, shirt_number: int, name):
        self.canvas = canvas
        self.player_canvas_id = player_canvas_id
        self.shirt_number = shirt_number
        self.player_id = player_id
        self.name = name


class FieldPlayer:
    def __init__(self, canvas, player_canvas_id, shirt_number_canvas_id, name_canvas_id):
        self.canvas = canvas
        self.player_canvas_id = player_canvas_id
        self.shirt_number_canvas_id = shirt_number_canvas_id
        self.name_canvas_id = name_canvas_id
        self.player_id = None
        self.name = None
        self.shirt_number = None


class UITeam:
    class SelectedPlayer:
        def __init__(self, is_field_player: bool, index: int):
            self.is_field_player = is_field_player
            self.index = index

    def __init__(self, window, name, formation):
        self.canvas = None
        self.players = None
        self.substitute_players = []
        self.field_players = []
        self.selected_players = []
        self.name = StringVar(window)
        self.name.set(name)
        self.formation = StringVar(window)
        self.formation.set(formation)

    def select_player(self, is_field_player: bool, index: int):
        players_list = self.field_players if is_field_player else self.substitute_players
        selected_player_index = next((i for i, selected_player in enumerate(self.selected_players) if selected_player.is_field_player == is_field_player and selected_player.index == index), -1)
        if selected_player_index > -1:
            canvas = players_list[index].canvas
            player_canvas_id = players_list[index].player_canvas_id
            canvas.itemconfig(player_canvas_id, outline='#000', width=1)
            self.selected_players.pop(selected_player_index)
            return
        substitute_players = [selected_player for selected_player in self.selected_players if not selected_player.is_field_player]
        if len(substitute_players) == 1 and not is_field_player:
            selected_substitute_player_index = next((i for i, selected_player in enumerate(self.selected_players) if not selected_player.is_field_player), -1)
            self.select_player(False, self.selected_players[selected_substitute_player_index].index)
        self.selected_players.append(UITeam.SelectedPlayer(is_field_player, index))
        canvas = players_list[index].canvas
        player_canvas_id = players_list[index].player_canvas_id
        canvas.itemconfig(player_canvas_id, outline='#ff0', width=3)
        field_players = [selected_player for selected_player in self.selected_players if selected_player.is_field_player]
        substitute_players = [selected_player for selected_player in self.selected_players if not selected_player.is_field_player]
        if len(field_players) == 2:
            self.__replace_players(field_players[0], field_players[1], True)
        elif len(substitute_players) == 1 and len(field_players) == 1:
            self.__replace_players(field_players[0], substitute_players[0])

    def __replace_players(self, selected_player1: SelectedPlayer, selected_player2: SelectedPlayer, swap=False):
        player1 = self.field_players[selected_player1.index]
        player2 = self.field_players[selected_player2.index] if swap else self.substitute_players[selected_player2.index]
        player1_id = player1.player_id
        player1_shirt_number = player1.shirt_number
        player1_name = player1.name
        player1.player_id = player2.player_id
        player1.shirt_number = player2.shirt_number
        player1.name = player2.name

        player1.canvas.itemconfig(player1.shirt_number_canvas_id, text=player1.shirt_number)
        player1.canvas.itemconfig(player1.name_canvas_id, text=player1.name)

        if swap:
            player2.player_id = player1_id
            player2.shirt_number = player1_shirt_number
            player2.name = player1_name
            player2.canvas.itemconfig(player2.shirt_number_canvas_id, text=player2.shirt_number)
            player2.canvas.itemconfig(player2.name_canvas_id, text=player2.name)

        self.__reset_selections()

    def __reset_selections(self):
        for selected_player in self.selected_players:
            player = self.field_players[selected_player.index] if selected_player.is_field_player else self.substitute_players[selected_player.index]
            player.canvas.itemconfig(player.player_canvas_id, outline='#000', width=1)
        self.selected_players.clear()
