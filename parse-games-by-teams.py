import json
import csv
import os
import sys

from models import TeamStats

base_folder = os.path.dirname(__file__)


def append_team_stats_to_array(arr, team_stats: TeamStats):
    arr.append(team_stats.ball_possession)
    arr.append(team_stats.own_half_ball_losses)
    arr.append(team_stats.opponent_half_ball_recoveries)
    arr.append(team_stats.own_half_ball_recoveries)
    arr.append(team_stats.successful_tackles)
    arr.append(team_stats.fouls)
    arr.append(team_stats.yellow_cards)
    arr.append(team_stats.red_cards)
    arr.append(team_stats.penalty_kick_goals)
    arr.append(team_stats.shots_on_goal)
    arr.append(team_stats.shots_inside_the_area)
    arr.append(team_stats.shots_outside_the_area)
    arr.append(team_stats.shots_on_target)
    arr.append(team_stats.shots_off_target)
    arr.append(team_stats.shots_after_left_side_attacks)
    arr.append(team_stats.shots_after_center_attacks)
    arr.append(team_stats.shots_after_right_side_attacks)
    arr.append(team_stats.direct_crosses_into_the_area)
    arr.append(team_stats.attacking_passes)
    arr.append(team_stats.key_passes)
    arr.append(team_stats.air_challenges_won)
    arr.append(team_stats.ground_challenges_won)
    arr.append(team_stats.dribbles_won)


filename = os.path.join(base_folder, 'resources', 'teams.json')
with open(filename, 'r', encoding="utf8") as f:
    data_store = json.load(f)

games = 0
summary = {}
team_ids = data_store['data'].keys()
for team_id in team_ids:
    team_game_seasons = data_store['data'][team_id]['stats']['902']
    seasons = team_game_seasons.keys()
    for season in seasons:
        game_indexes = team_game_seasons[season].keys()
        for game_index in game_indexes:
            game_stats = team_game_seasons[season][game_index]
            game_id = game_stats['gameId']
            game_stage = game_stats['stage']
            if game_id != 0 and game_stage == 'RegularSeason':
                if game_id not in summary:
                    summary[game_id] = []
                summary[game_id].append(TeamStats(game_stats))

csv_headers = ['result',
               'ball_possession_0', 'own_half_ball_losses_0', 'opponent_half_ball_recoveries_0',
               'own_half_ball_recoveries_0', 'successful_tackles_0', 'fouls_0', 'yellow_cards_0', 'red_cards_0',
               'penalty_kick_goals_0', 'shots_on_goal_0', 'shots_inside_the_area_0', 'shots_outside_the_area_0',
               'shots_on_target_0', 'shots_off_target_0', 'shots_after_left_side_attacks_0', 'shots_after_center_attacks_0',
               'shots_after_right_side_attacks_0', 'direct_crosses_into_the_area_0', 'attacking_passes_0',
               'key_passes_0', 'air_challenges_won_0', 'ground_challenges_won_0', 'dribbles_won_0',
               'ball_possession_1', 'own_half_ball_losses_1', 'opponent_half_ball_recoveries_1',
               'own_half_ball_recoveries_1', 'successful_tackles_1', 'fouls_1', 'yellow_cards_1', 'red_cards_1',
               'penalty_kick_goals_1', 'shots_on_goal_1', 'shots_inside_the_area_1', 'shots_outside_the_area_1',
               'shots_on_target_1', 'shots_off_target_1', 'shots_after_left_side_attacks_1', 'shots_after_center_attacks_1',
               'shots_after_right_side_attacks_1', 'direct_crosses_into_the_area_1', 'attacking_passes_1',
               'key_passes_1', 'air_challenges_won_1', 'ground_challenges_won_1', 'dribbles_won_1']
game_stats_filename = os.path.join(base_folder, 'resources', 'game_stats.csv')
with open(game_stats_filename, 'w', newline='') as csvFile:
    writer = csv.writer(csvFile)
    writer.writerow(csv_headers)
    for game_id in summary.keys():
        if len(summary[game_id]) == 2:
            try:
                team_stats_0 = summary[game_id][0]
                team_stats_1 = summary[game_id][1]
                result = 'draw' if team_stats_0.goals == team_stats_1.goals else 'win' if team_stats_0.goals > team_stats_1.goals else 'lose'
                row = [result]
                append_team_stats_to_array(row, team_stats_0)
                append_team_stats_to_array(row, team_stats_1)
                writer.writerow(row)
                games += 1
            except:
                print('Exception in game', sys.exc_info(), game_id)

print('Regular season games found:', games)

csvFile.close()
