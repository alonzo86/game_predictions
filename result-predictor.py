import json
import os
import re
import runpy
import statistics
import tkinter
import warnings
import numpy as np
import pandas as pd
import tensorflow as tf
from threading import Thread
from tkinter import Button, Canvas, Frame, OptionMenu, N, Toplevel, Label

import wget
from PIL import Image, ImageTk
from webcolors import hex_to_rgb

warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=DeprecationWarning)
tf.compat.v1.enable_eager_execution()
np.set_printoptions(formatter={'float': lambda x: "{0:0.3f}".format(x)})

base_folder = os.path.dirname(__file__)


def safe_div(x, y):
    return 0 if y == 0 else x / y


def is_polygon_dark(hex_color):
    rgb = hex_to_rgb(hex_color)
    return (rgb[0] * 0.299 + rgb[1] * 0.587 + rgb[2] * 0.114) <= 186


def train_model():

    def start_training():
        train_games = os.path.join(base_folder, 'train-games.py')
        runpy.run_path(path_name=train_games)

    process = Thread(target=start_training)
    process.start()


def download_data():

    def download():
        players_url = 'https://cdnapi.bamboo-video.com/api/football/player?format=json&iid=573881b7181f46ae4c8b4567&returnZeros=false'
        players_json_path = os.path.join(base_folder, 'resources', 'players.json')
        teams_url = 'https://cdnapi.bamboo-video.com/api/football/team?format=json&iid=573881b7181f46ae4c8b4567&filter={}&returnZeros=false&expand=[%22stats%22]'
        teams_json_path = os.path.join(base_folder, 'resources', 'teams.json')
        rounds_url = 'https://cdnapi.bamboo-video.com/api/football/round?format=json&iid=573881b7181f46ae4c8b4567'
        rounds_json_path = os.path.join(base_folder, 'resources', 'rounds.json')
        os.remove(players_json_path)
        wget.download(players_url, players_json_path)
        os.remove(teams_json_path)
        wget.download(teams_url, teams_json_path)
        os.remove(rounds_json_path)
        wget.download(rounds_url, rounds_json_path)
        parse_games_by_teams = os.path.join(base_folder, 'parse-games-by-teams.py')
        runpy.run_path(path_name=parse_games_by_teams)

    process = Thread(target=download)
    process.start()


def show_predicted_results(loss_percent, draw_percent, win_percent):
    msg_results = Toplevel()
    msg_results.wm_title('Prediction results')

    result = 'win: %d%%\ndraw: %d%%\nloss: %d%%' % (win_percent, draw_percent, loss_percent)
    lbl_results = Label(msg_results, text=result)
    lbl_results.grid(row=0, column=0)

    b = Button(msg_results, text="Okay", command=msg_results.destroy)
    b.grid(row=1, column=0)


def predict_result():
    def init_team_data():
        return {
            'lost_ball': 0, 'own_half_lost_ball': 0, 'ball_recovery': 0, 'ball_recovery_in_opp_half': 0,
            'ball_recovery_in_own_half': 0, 'tackles': 0, 'tackles_success': 0, 'foul': 0, 'yellow_card': 0,
            'red_card': 0, 'penalty_kick': 0, 'penalty_shot_goal': 0, 'regular_goals': 0, 'attempts_on_goal': 0,
            'shots_inside_the_area': 0, 'shots_outside_the_area': 0, 'shots_on_target': 0, 'shots_off_target': 0,
            'left_side_attacks': 0, 'left_side_attacks_with_shot': 0, 'center_attacks': 0, 'center_attacks_with_shot': 0,
            'right_side_attacks': 0, 'right_side_attacks_with_shot': 0, 'crosses': 0, 'direct_crosses_into_the_area': 0,
            'passes': 0, 'attacking_passes': 0, 'key_passes': 0, 'air_challenge': 0, 'air_challenge_won': 0,
            'ground_challenge': 0, 'ground_challenge_won': 0, 'dribbles': 0, 'won_dribbles': 0
        }

    def summarize_team_data(total_team_data, field_player):
        return {
            'lost_ball': total_team_data['lost_ball'] + field_player.get('lostBall', 0),
            'own_half_lost_ball': total_team_data['own_half_lost_ball'] + field_player.get('ownHalfLostBall', 0),
            'ball_recovery': total_team_data['ball_recovery'] + field_player.get('ballRecovery', 0),
            'ball_recovery_in_opp_half': total_team_data['ball_recovery_in_opp_half'] + field_player.get('ballRecoveryInOppHalf', 0),
            'ball_recovery_in_own_half': total_team_data['ball_recovery_in_own_half'] + field_player.get('ballRecoveryInOwnHalf', 0),
            'tackles': total_team_data['tackles'] + field_player.get('tackles', 0),
            'tackles_success': total_team_data['tackles_success'] + field_player.get('tacklesSuccess', 0),
            'foul': total_team_data['foul'] + field_player.get('foul', 0),
            'yellow_card': total_team_data['yellow_card'] + field_player.get('YellowCard', 0),
            'red_card': total_team_data['red_card'] + field_player.get('RedCard', 0),
            'penalty_kick': total_team_data['penalty_kick'] + field_player.get('PenaltyKick', 0),
            'penalty_shot_goal': total_team_data['penalty_shot_goal'] + field_player.get('PenaltyShot_Goal', 0),
            'regular_goals': total_team_data['regular_goals'] + field_player.get('GoalRegular', 0),
            'attempts_on_goal': total_team_data['attempts_on_goal'] + field_player.get('AttemptonGoal', 0),
            'shots_inside_the_area': total_team_data['shots_inside_the_area'] + field_player.get('ShotInsidetheArea', 0),
            'shots_outside_the_area': total_team_data['shots_outside_the_area'] + field_player.get('ShotOutsidetheArea', 0),
            'shots_on_target': total_team_data['shots_on_target'] + field_player.get('OnTarget', 0),
            'shots_off_target': total_team_data['shots_off_target'] + field_player.get('OffTarget', 0),
            'left_side_attacks': total_team_data['left_side_attacks'] + field_player.get('leftSideAttack', 0),
            'left_side_attacks_with_shot': total_team_data['left_side_attacks_with_shot'] + field_player.get('leftSideAttackWithShot', 0),
            'center_attacks': total_team_data['center_attacks'] + field_player.get('centerAttack', 0),
            'center_attacks_with_shot': total_team_data['center_attacks_with_shot'] + field_player.get('centerAttackWithShot', 0),
            'right_side_attacks': total_team_data['right_side_attacks'] + field_player.get('rightSideAttack', 0),
            'right_side_attacks_with_shot': total_team_data['right_side_attacks_with_shot'] + field_player.get('rightSideAttackWithShot', 0),
            'crosses': total_team_data['crosses'] + field_player.get('Cross', 0),
            'direct_crosses_into_the_area': total_team_data['direct_crosses_into_the_area'] + field_player.get('DirectCrossintotheArea', 0),
            'passes': total_team_data['passes'] + field_player.get('passes', 0),
            'attacking_passes': total_team_data['attacking_passes'] + field_player.get('attackingPasses', 0),
            'key_passes': total_team_data['key_passes'] + field_player.get('keyPasses', 0),
            'air_challenge': total_team_data['air_challenge'] + field_player.get('airChallenge', 0),
            'air_challenge_won': total_team_data['air_challenge_won'] + field_player.get('wonAirChallenge', 0),
            'ground_challenge': total_team_data['ground_challenge'] + field_player.get('groundChallenge', 0),
            'ground_challenge_won': total_team_data['ground_challenge_won'] + field_player.get('wonGroundChallenge', 0),
            'dribbles': total_team_data['dribbles'] + field_player.get('dribble', 0),
            'won_dribbles': total_team_data['won_dribbles'] + field_player.get('wonDribble', 0)
        }

    def calc_stats(players_data, ball_possession, side):
        return {
            'ball_possession_%s' % side: ball_possession,
            'own_half_ball_losses_%s' % side: safe_div(players_data['own_half_lost_ball'], players_data['lost_ball']),
            'opponent_half_ball_recoveries_%s' % side: safe_div(players_data['ball_recovery_in_opp_half'], players_data['ball_recovery']),
            'own_half_ball_recoveries_%s' % side: safe_div(players_data['ball_recovery_in_own_half'], players_data['ball_recovery']),
            'successful_tackles_%s' % side: safe_div(players_data['tackles_success'], players_data['tackles']),
            'fouls_%s' % side: safe_div(players_data['foul'], players_data['tackles']),
            'yellow_cards_%s' % side: safe_div(players_data['yellow_card'], players_data['foul']),
            'red_cards_%s' % side: safe_div(players_data['red_card'], players_data['foul']),
            'penalty_kick_goals_%s' % side: safe_div(players_data['penalty_shot_goal'], players_data['penalty_kick']),
            'shots_on_goal_%s' % side: safe_div(players_data['regular_goals'], players_data['attempts_on_goal']),
            'shots_inside_the_area_%s' % side: safe_div(players_data['shots_inside_the_area'], players_data['attempts_on_goal']),
            'shots_outside_the_area_%s' % side: safe_div(players_data['shots_outside_the_area'], players_data['attempts_on_goal']),
            'shots_on_target_%s' % side: safe_div(players_data['shots_on_target'], players_data['attempts_on_goal']),
            'shots_off_target_%s' % side: safe_div(players_data['shots_off_target'], players_data['attempts_on_goal']),
            'shots_after_right_side_attacks_%s' % side: safe_div(players_data['right_side_attacks_with_shot'], players_data['right_side_attacks']),
            'shots_after_center_attacks_%s' % side: safe_div(players_data['center_attacks_with_shot'], players_data['center_attacks']),
            'shots_after_left_side_attacks_%s' % side: safe_div(players_data['left_side_attacks_with_shot'], players_data['left_side_attacks']),
            'direct_crosses_into_the_area_%s' % side: safe_div(players_data['direct_crosses_into_the_area'], players_data['crosses']),
            'attacking_passes_%s' % side: safe_div(players_data['attacking_passes'], players_data['passes']),
            'key_passes_%s' % side: safe_div(players_data['key_passes'], players_data['attacking_passes']),
            'air_challenges_won_%s' % side: safe_div(players_data['air_challenge_won'], players_data['air_challenge']),
            'ground_challenges_won_%s' % side: safe_div(players_data['ground_challenge_won'], players_data['ground_challenge']),
            'dribbles_won_%s' % side: safe_div(players_data['won_dribbles'], players_data['dribbles']),
        }

    left_team_data = init_team_data()
    for left_field_player in left_field_players:
        player = teams[teams_map[team_left.get()]]['players'][left_field_player['player_id']]['stats']
        left_team_data = summarize_team_data(left_team_data, player)
    left_players_stats_summary = calc_stats(left_team_data, teams[teams_map[team_left.get()]]['possession'], '0')

    right_team_data = init_team_data()
    for right_field_player in right_field_players:
        player = teams[teams_map[team_right.get()]]['players'][right_field_player['player_id']]['stats']
        right_team_data = summarize_team_data(right_team_data, player)
    right_players_stats_summary = calc_stats(right_team_data, teams[teams_map[team_right.get()]]['possession'], '1')

    stats_summary = {**left_players_stats_summary, **right_players_stats_summary}
    input_data_frame = pd.DataFrame(stats_summary, index=[0])
    input_data = np.array(input_data_frame)
    results = prediction_model.predict(input_data)
    show_predicted_results(results[0][0] * 100, results[0][1] * 100, results[0][2] * 100)


def process_players():
    players_stat_id_map = {}
    teams_map_dic = {}
    teams_dic = {}
    players_json_path = os.path.join(base_folder, 'resources', 'players.json')
    with open(players_json_path, 'r', encoding='utf8') as f:
        data_store = json.load(f)
        player_ids = data_store['data'].keys()
        for player_id in player_ids:
            if 'stats' in data_store['data'][player_id] and 'shirtNumber' in \
                    data_store['data'][player_id] \
                    and '902' in data_store['data'][player_id]['stats'] and '19/20' in \
                    data_store['data'][player_id]['stats']['902']:
                team = data_store['data'][player_id]['teamId']
                if team:
                    if team['id'] not in teams_dic:
                        teams_map_dic[team['hebrewName']] = team['id']
                        teams_dic[team['id']] = {}
                        teams_dic[team['id']]['name'] = team['hebrewName']
                        teams_dic[team['id']]['color'] = team['color'] if 'color' in team else '#fff'
                        teams_dic[team['id']]['goalie_color'] = team['goalieColor'] if 'goalieColor' in team else '#fff'
                        teams_dic[team['id']]['players'] = {}
                    players = teams_dic[team['id']]['players']
                    if player_id not in players:
                        players[player_id] = {}
                        players[player_id]['shirt_number'] = data_store['data'][player_id]['shirtNumber']
                        players[player_id]['position'] = data_store['data'][player_id]['position']
                        players[player_id]['first_name'] = data_store['data'][player_id]['firstName']
                        players[player_id]['last_name'] = data_store['data'][player_id]['lastName']
                        stats = data_store['data'][player_id]['stats']['902']['19/20'][0]
                        players[player_id]['stats'] = stats
                        players_stat_id_map[stats['playerInstatId']] = player_id
        for team_id in teams_dic:
            if len(teams_dic[team_id]['players'].keys()) < 11 and teams_dic[team_id]['name'] in teams_map_dic:
                del teams_map_dic[teams_dic[team_id]['name']]
    teams_json_path = os.path.join(base_folder, 'resources', 'teams.json')
    with open(teams_json_path, 'r', encoding='utf8') as f:
        data_store = json.load(f)
        team_ids = data_store['data'].keys()
        for team_id in team_ids:
            if int(team_id) in teams_dic:
                possession = []
                season = data_store['data'][team_id]['stats']['902']['19/20']
                for game_index in season.keys():
                    if season[game_index]['stage'] == 'RegularSeason':
                        possession.append(season[game_index]['ballPossession'])
                teams_dic[int(team_id)]['possession'] = statistics.mean(possession) / 100
    lst_to_delete = list(map(str, list(teams_dic.keys())) - data_store['data'].keys())
    for to_del in lst_to_delete:
        del teams_dic[int(to_del)]
    process_latest_lineups(teams_dic)
    return teams_dic, teams_map_dic, players_stat_id_map


def process_latest_lineups(teams_dic):
    num_of_lineups_found = 0
    players_json_path = os.path.join(base_folder, 'resources', 'rounds.json')
    with open(players_json_path, 'r', encoding='utf8') as f:
        data_store = json.load(f)
        for i in range(len(data_store['data']) - 1, 0, -1):
            curr_round = data_store['data'][i]
            if len(curr_round['standings']) == 0:
                continue
            for game_id in curr_round['games']['objects'].keys():
                if curr_round['games']['objects'][game_id]['status'] == 3:
                    curr_game = curr_round['games']['objects'][game_id]
                    home_team = curr_game['homeTeamId']
                    away_team = curr_game['awayTeamId']
                    if 'latest_lineup' not in teams_dic[home_team['id']]:
                        teams_dic[home_team['id']]['latest_lineup'] = curr_game['lineups']['first_team'][0]['lineup'][0]['main'][0]
                        num_of_lineups_found += 1
                    if 'latest_lineup' not in teams_dic[away_team['id']]:
                        teams_dic[away_team['id']]['latest_lineup'] = curr_game['lineups']['second_team'][0]['lineup'][0]['main'][0]
                        num_of_lineups_found += 1
                if len(teams_dic.keys()) == num_of_lineups_found:
                    return


def get_resource_path(resource_name):
    image_path = os.path.join(base_folder, 'resources', resource_name)
    return image_path


def init_top_menu():
    global txt_btn_update_data
    frm_menu = Frame(window, height=40)
    frm_menu.grid(column=0, row=0, sticky=tkinter.W)
    btn_train_model = Button(frm_menu, text='Train Model', command=train_model)
    btn_train_model.grid(column=0, row=0)
    btn_update_data = Button(frm_menu, textvariable=txt_btn_update_data, command=download_data)
    txt_btn_update_data.set('Update Data')
    btn_update_data.grid(column=1, row=0)
    btn_predict = Button(frm_menu, text='Predict', command=predict_result)
    btn_predict.grid(column=2, row=0)


def init_fields():
    global lst_players_left, lst_players_right
    frm_fields = Frame(window)
    frm_fields.grid(column=0, row=1)
    left_canvas = init_field(frm_fields, team_left, formation_left, 0, 'left')
    lst_players_left = init_all_players(frm_fields, team_left, 0, 'left', None)
    right_canvas = init_field(frm_fields, team_right, formation_right, 2, 'right')
    lst_players_right = init_all_players(frm_fields, team_right, 2, 'right', None)
    return left_canvas, right_canvas


def init_field(parent, team_var, formation_var, column, side):
    frm_field_menu = Frame(parent)
    frm_field_menu.grid(column=column, row=0, sticky=tkinter.NW)
    opt_field_team = OptionMenu(frm_field_menu, team_var, *teams_map.keys())
    opt_field_team.grid(column=0, row=0, sticky=tkinter.NW)
    opt_field_formation = OptionMenu(frm_field_menu, formation_var, *resources['formations'].keys())
    opt_field_formation.grid(column=1, row=0, sticky=tkinter.NW)
    btn_set_player = Button(frm_field_menu, text='Set Player', command=lambda: set_player(side))
    btn_set_player.grid(column=2, row=0)

    frm_field = Frame(parent)
    frm_field.grid(column=column, row=1, sticky=tkinter.N)

    photo_image = ImageTk.PhotoImage(resources['field'])
    canvas_field = Canvas(frm_field, width=564, height=900)
    canvas_field.image = photo_image
    canvas_field.create_image(0, 0, anchor=tkinter.NW, image=photo_image)
    canvas_field.pack()
    return canvas_field


def init_all_players(parent, team_var, column, side, lst_players):
    if lst_players is None:
        lst_players = Frame(parent)
        lst_players.grid(column=column + 1, row=1, sticky=N)

    player_color = teams[teams_map[team_var.get()]]['color']
    goalie_color = teams[teams_map[team_var.get()]]['goalie_color']
    player_ids = teams[teams_map[team_var.get()]]['players']
    col = 0
    row = 0
    i = 0
    global left_players
    players_arr = left_players if side == 'left' else right_players
    for player in players_arr:
        player['canvas'].grid_forget();
    players_arr.clear()
    for player_id in player_ids:
        shirt_number = teams[teams_map[team_var.get()]]['players'][player_id]['shirt_number']
        position = teams[teams_map[team_var.get()]]['players'][player_id]['position']
        last_name = teams[teams_map[team_var.get()]]['players'][player_id]['last_name']
        canvas_player = Canvas(lst_players, width=80, height=90)
        polygon_color = goalie_color if position == 'goalie' else player_color
        font_color = '#fff' if is_polygon_dark(polygon_color) else '#000'
        player_poly = canvas_player.create_polygon(resources['shirt_path'], outline='#000', fill=polygon_color)
        canvas_player.create_text(35, 30, fill=font_color, font='Times 20 bold', text=shirt_number)
        canvas_player.create_text(35, 50, fill=font_color, font='Times 8', text=last_name)
        canvas_player.create_text(35, 70, fill='#000', font='Times 8', text=position)
        data = {'side': side, 'index': i}
        canvas_player.bind('<Button-1>', lambda event, arg=data: replacement_player_click(arg))
        canvas_player.grid(column=col, row=row)
        players_arr.append(
            {'canvas': canvas_player, 'player': player_poly, 'player_id': player_id, 'shirt_number': shirt_number,
             'name': last_name})
        row += 1
        i += 1
        if row > 8:
            row = 0
            col += 1
    return lst_players


def replacement_player_click(data):
    if data['side'] == 'left':
        global left_selected_player
        if left_selected_player > -1:
            canvas = left_players[left_selected_player]['canvas']
            player = left_players[left_selected_player]['player']
            canvas.itemconfig(player, outline='#000', width=1)
            if left_selected_player == data['index']:
                left_selected_player = -1
                return
        left_selected_player = data['index']
        canvas = left_players[left_selected_player]['canvas']
        player = left_players[left_selected_player]['player']
        canvas.itemconfig(player, outline='#ff0', width=3)
    else:
        global right_selected_player
        if right_selected_player > -1:
            canvas = right_players[right_selected_player]['canvas']
            player = right_players[right_selected_player]['player']
            canvas.itemconfig(player, outline='#000', width=1)
            if right_selected_player == data['index']:
                right_selected_player = -1
                return
        right_selected_player = data['index']
        canvas = right_players[right_selected_player]['canvas']
        player = right_players[right_selected_player]['player']
        canvas.itemconfig(player, outline='#ff0', width=3)


def field_player_click(data):
    if data['side'] == 'left':
        global left_selected_field_player
        if left_selected_field_player > -1:
            canvas = left_field_players[left_selected_field_player]['canvas']
            player = left_field_players[left_selected_field_player]['player']
            canvas.itemconfig(player, outline='#000', width=1)
            if left_selected_field_player == data['index']:
                left_selected_field_player = -1
                return
        left_selected_field_player = data['index']
        canvas = left_field_players[left_selected_field_player]['canvas']
        player = left_field_players[left_selected_field_player]['player']
        canvas.itemconfig(player, outline='#ff0', width=3)
    else:
        global right_selected_field_player
        if right_selected_field_player > -1:
            canvas = right_field_players[right_selected_field_player]['canvas']
            player = right_field_players[right_selected_field_player]['player']
            canvas.itemconfig(player, outline='#000', width=1)
            if right_selected_field_player == data['index']:
                right_selected_field_player = -1
                return
        right_selected_field_player = data['index']
        canvas = right_field_players[right_selected_field_player]['canvas']
        player = right_field_players[right_selected_field_player]['player']
        canvas.itemconfig(player, outline='#ff0', width=3)


def set_player(side):
    global right_selected_player, right_selected_field_player, left_selected_player, left_selected_field_player
    players = right_players
    selected_player = right_selected_player
    field_players = right_field_players
    selected_field_player = right_selected_field_player
    if side == 'left':
        players = left_players
        selected_player = left_selected_player
        field_players = left_field_players
        selected_field_player = left_selected_field_player

    right_selected_player = -1
    right_selected_field_player = -1
    left_selected_player = -1
    left_selected_field_player = -1

    player_id = players[selected_player]['player_id']
    shirt_number = players[selected_player]['shirt_number']
    name = players[selected_player]['name']
    field_players[selected_field_player]['player_id'] = player_id
    field_players[selected_field_player]['shirt_number'] = shirt_number
    field_players[selected_field_player]['name'] = name

    replacement_canvas = players[selected_player]['canvas']
    field_canvas = field_players[selected_field_player]['canvas']

    txt_shirt_number = field_players[selected_field_player]['txt_shirt_number']
    txt_name = field_players[selected_field_player]['txt_name']
    field_canvas.itemconfig(txt_shirt_number, text=shirt_number)
    field_canvas.itemconfig(txt_name, text=name)

    player = players[selected_player]['player']
    field_player = field_players[selected_field_player]['player']
    replacement_canvas.itemconfig(player, outline='#000', width=1)
    field_canvas.itemconfig(field_player, outline='#000', width=1)


def draw_formation(canvas_field, formation, team_id, side):
    global left_field_players
    global right_field_players
    field_players = left_field_players if side == 'left' else right_field_players
    index = 0
    for field_player in field_players:
        tag = 'polygon_%s' % index
        canvas_field.tag_unbind(tag, '<Button-1>')
        canvas_field.delete(field_player['player'])
        canvas_field.delete(field_player['txt_shirt_number'])
        canvas_field.delete(field_player['txt_name'])
        index += 1
    field_players.clear()
    player_color = teams[team_id]['color']
    goalie_color = teams[team_id]['goalie_color']
    formation_map = resources['formations'][formation.get()]['points']
    num_of_points = len(resources['shirt_path'])
    index = 0
    for position in formation_map:
        points = []
        for i in range(0, num_of_points, 2):
            points.append(resources['shirt_path'][i] + position[0])
            points.append(resources['shirt_path'][i + 1] + position[1])
        tag = 'polygon_%s' % index
        polygon_color = goalie_color if index == 0 else player_color
        font_color = '#fff' if is_polygon_dark(polygon_color) else '#000'
        player = canvas_field.create_polygon(points, outline='#000', fill=polygon_color, tag=tag)
        shirt_number = canvas_field.create_text(points[0] + 35, points[1] + 10, fill=font_color, font='Times 20 bold',
                                                text='')
        name = canvas_field.create_text(points[0] + 35, points[1] + 30, fill=font_color, font='Times 8', text='')
        field_players.append(
            {'canvas': canvas_field, 'player': player, 'txt_shirt_number': shirt_number, 'txt_name': name})
        data = {'side': side, 'index': index}
        canvas_field.tag_bind(tag, '<Button-1>', lambda event, arg=data: field_player_click(arg))
        index += 1


def init_vars():
    global canvas_field_left, canvas_field_right, left_selected_player, left_selected_field_player, right_selected_player, right_selected_field_player
    left_selected_player = -1
    left_selected_field_player = -1
    right_selected_player = -1
    right_selected_field_player = -1
    canvas_field_left, canvas_field_right = init_fields()
    draw_formation(canvas_field_left, formation_left, teams_map[team_left.get()], 'left')
    draw_formation(canvas_field_right, formation_right, teams_map[team_right.get()], 'right')


def on_team_changed(side):
    team = team_left if side == 'left' else team_right
    formation = formation_left if side == 'left' else formation_right
    lst_players = lst_players_left if side == 'left' else lst_players_right
    init_all_players(None, team, -1, side, lst_players)

    formation.set(get_team_formation(team.get()))

    field_players = left_field_players if side == 'left' else right_field_players
    init_latest_players(field_players, team.get(), formation.get())


def on_formation_changed(side):
    canvas_field = canvas_field_left if side == 'left' else canvas_field_right
    formation = formation_left if side == 'left' else formation_right
    team = team_left.get() if side == 'left' else team_right.get()
    draw_formation(canvas_field, formation, teams_map[team], side)


def get_team_formation(team_id):
    delimiter = '-'
    formation_parts = re.findall(r'\d+', teams[teams_map[team_id]]['latest_lineup']['starting_tactic'])
    return delimiter.join(list(map(str, formation_parts)))


def init_latest_players(field_players, team_id, formation):
    player_positions = resources['formations'][formation]['positions']
    players = teams[teams_map[team_id]]['latest_lineup']['player']
    for player in players:
        if player['starting_position_name'] == 'Substitute player':
            continue
        player_in_stat_id = player['id']
        player_id = players_id_stat_id_dic[int(player_in_stat_id)]
        shirt_number = player['num']
        name = teams[teams_map[team_id]]['players'][player_id]['first_name']
        starting_position_name = player['starting_position_name']
        player_index = player_positions[starting_position_name]
        field_players[player_index]['player_id'] = player_id
        field_players[player_index]['shirt_number'] = shirt_number
        field_players[player_index]['name'] = name
        field_canvas = field_players[player_index]['canvas']
        txt_shirt_number = field_players[player_index]['txt_shirt_number']
        txt_name = field_players[player_index]['txt_name']
        field_canvas.itemconfig(txt_shirt_number, text=shirt_number)
        field_canvas.itemconfig(txt_name, text=name)


teams, teams_map, players_id_stat_id_dic = process_players()
window = tkinter.Tk()
window.geometry('1700x1000')
resources = {
    'field': Image.open(get_resource_path('field.jpg')),
    'shirt_path': [0.0, 15.0, 15.0, 3.0, 30.0, 0.0, 37.5, 0.0, 52.5, 3.0, 67.5, 15.0, 60.0, 30.0, 52.5, 22.5, 52.5, 60.0, 30.0, 60.0, 15.0, 60.0, 15.0, 22.5, 7.5, 30.0],
    'formations': {
        '4-4-2': {
            'points': [[250, 760], [57, 600], [184, 600], [311, 600], [438, 600], [57, 400], [184, 400], [311, 400], [438, 400], [184, 200], [311, 200]],
            'positions': {
                'Goalkeeper': 0,
                'Defender - Left': 1,
                'Defender - Left central': 2,
                'Defender - Right central': 3,
                'Defender - Right': 4,
                'Midfielder - Left': 5,
                'Defensive midfielder - Left central': 6,
                'Defensive midfielder - Right central': 7,
                'Midfielder - Right': 8,
                'Forward - Left central': 9,
                'Forward - Right central': 10
            }
        },
        '4-3-3': {
            'points': [[250, 760], [57, 600], [184, 600], [311, 600], [438, 600], [150, 400], [250, 400], [350, 400], [150, 200], [250, 200], [350, 200]],
            'positions': {
                'Goalkeeper': 0,
                'Defender - Left': 1,
                'Defender - Left central': 2,
                'Defender - Right central': 3,
                'Defender - Right': 4,
                'Midfielder - Left central': 5,
                'Defensive midfielder - Central': 6,
                'Midfielder - Right central': 7,
                'Attacking midfielder - Left': 8,
                'Forward - Central': 9,
                'Attacking midfielder - Right': 10
            }
        },
        '5-3-2': {
            'points': [[250, 760], [57, 550], [150, 640], [250, 650], [350, 640], [438, 550], [150, 400], [250, 400], [350, 400], [184, 200], [311, 200]],
            'positions': {}
        },
        '3-5-2': {
            'points': [[250, 760], [150, 640], [250, 650], [350, 640], [57, 400], [150, 400], [250, 400], [350, 400], [438, 400], [184, 200], [311, 200]],
            'positions': {
                'Goalkeeper': 0,
                'Defender - Left central': 1,
                'Defender - Central': 2,
                'Defender - Right central': 3,
                'Midfielder - Left': 4,
                'Defensive midfielder - Left central': 5,
                'Midfielder - Left central': 5,
                'Attacking midfielder - Central': 6,
                'Defensive midfielder - Central': 6,
                'Defensive midfielder - Right central': 7,
                'Midfielder - Right central': 7,
                'Midfielder - Right': 8,
                'Forward - Left central': 9,
                'Forward - Right central': 10
            }
        },
        '4-2-3-1': {
            'points': [[250, 760], [57, 600], [184, 600], [311, 600], [438, 600], [184, 470], [311, 470], [57, 320], [250, 320], [438, 320], [250, 200]],
            'positions': {
                'Goalkeeper': 0,
                'Defender - Left': 1,
                'Defender - Left central': 2,
                'Defender - Right central': 3,
                'Defender - Right': 4,
                'Defensive midfielder - Left central': 5,
                'Defensive midfielder - Right central': 6,
                'Attacking midfielder - Left': 7,
                'Attacking midfielder - Central': 8,
                'Attacking midfielder - Right': 9,
                'Forward - Central': 10
            }
        },
        '3-4-3': {
            'points': [[250, 760], [150, 600], [250, 600], [350, 600], [57, 400], [184, 400], [311, 400], [438, 400], [150, 200], [250, 200], [350, 200]],
            'positions': {
                'Goalkeeper': 0,
                'Defender - Left central': 1,
                'Defender - Central': 2,
                'Defender - Right central': 3,
                'Midfielder - Left': 4,
                'Defensive midfielder - Left central': 5,
                'Attacking midfielder - Left central': 5,
                'Defensive midfielder - Right central': 6,
                'Attacking midfielder - Right central': 6,
                'Midfielder - Right': 7,
                'Attacking midfielder - Left': 8,
                'Forward - Central': 9,
                'Attacking midfielder - Right': 10
            }
        }
    }
}

keras_file = os.path.join(base_folder, 'resources', 'game_prediction_model.h5')
prediction_model = tf.keras.models.load_model(keras_file)

txt_btn_update_data = tkinter.StringVar()

canvas_field_left = None
lst_players_left = None
left_players = []
left_field_players = []
left_selected_player = -1
left_selected_field_player = -1
team_left = tkinter.StringVar(window)
team_left.set(list(teams_map.keys())[0])
team_left.trace('w', lambda context, index, mode, side='left': on_team_changed(side))
formation_left = tkinter.StringVar(window)
latest_formation_left = get_team_formation(team_left.get())
formation_left.set(latest_formation_left)
formation_left.trace('w', lambda context, index, mode, side='left': on_formation_changed(side))

canvas_field_right = None
lst_players_right = None
right_players = []
right_field_players = []
right_selected_player = -1
right_selected_field_player = -1
team_right = tkinter.StringVar(window)
team_right.set(list(teams_map.keys())[1])
team_right.trace('w', lambda context, index, mode, side='right': on_team_changed(side))
formation_right = tkinter.StringVar(window)
latest_formation_right = get_team_formation(team_right.get())
formation_right.set(latest_formation_right)
formation_right.trace('w', lambda context, index, mode, side='right': on_formation_changed(side))

init_top_menu()
init_vars()

init_latest_players(left_field_players, team_left.get(), formation_left.get())
init_latest_players(right_field_players, team_right.get(), formation_right.get())
window.mainloop()
