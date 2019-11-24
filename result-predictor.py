import json
import os
import runpy
import tkinter
import warnings
from threading import Thread
from tkinter import Button, Canvas, Frame, OptionMenu, N, Toplevel, Label

import numpy as np
import pandas as pd
import tensorflow as tf
import wget
from PIL import Image, ImageTk
from webcolors import hex_to_rgb

from models import Team, TeamStats
from utils import get_dictionary_item_by_property

warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=DeprecationWarning)
tf.compat.v1.enable_eager_execution()
np.set_printoptions(formatter={'float': lambda x: "{0:0.3f}".format(x)})

base_folder = os.path.dirname(__file__)


def get_team_by_name(team_name) -> Team:
    return get_dictionary_item_by_property(teams, 'name', team_name)


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
    msg_results.grab_set()
    msg_results.wm_title('Prediction results')

    result = 'win: %d%%\ndraw: %d%%\nloss: %d%%' % (win_percent, draw_percent, loss_percent)
    lbl_results = Label(msg_results, text=result)
    lbl_results.grid(row=0, column=0)

    b = Button(msg_results, text="Okay", command=msg_results.destroy)
    b.grid(row=1, column=0)


def predict_result():

    def convert_stats_to_summary(team_data: TeamStats, side):
        return {
            'ball_possession_%s' % side: team_data.ball_possession,
            'own_half_ball_losses_%s' % side: team_data.own_half_ball_losses,
            'opponent_half_ball_recoveries_%s' % side: team_data.opponent_half_ball_recoveries,
            'own_half_ball_recoveries_%s' % side: team_data.own_half_ball_recoveries,
            'successful_tackles_%s' % side: team_data.successful_tackles,
            'fouls_%s' % side: team_data.fouls,
            'yellow_cards_%s' % side: team_data.yellow_cards,
            'red_cards_%s' % side: team_data.red_cards,
            'penalty_kick_goals_%s' % side: team_data.penalty_kick_goals,
            'shots_on_goal_%s' % side: team_data.shots_on_goal,
            'shots_inside_the_area_%s' % side: team_data.shots_inside_the_area,
            'shots_outside_the_area_%s' % side: team_data.shots_outside_the_area,
            'shots_on_target_%s' % side: team_data.shots_on_target,
            'shots_off_target_%s' % side: team_data.shots_off_target,
            'shots_after_right_side_attacks_%s' % side: team_data.shots_after_right_side_attacks,
            'shots_after_center_attacks_%s' % side: team_data.shots_after_center_attacks,
            'shots_after_left_side_attacks_%s' % side: team_data.shots_after_left_side_attacks,
            'direct_crosses_into_the_area_%s' % side: team_data.direct_crosses_into_the_area,
            'attacking_passes_%s' % side: team_data.attacking_passes,
            'key_passes_%s' % side: team_data.key_passes,
            'air_challenges_won_%s' % side: team_data.air_challenges_won,
            'ground_challenges_won_%s' % side: team_data.ground_challenges_won,
            'dribbles_won_%s' % side: team_data.dribbles_won,
        }

    left_team_data = TeamStats()
    left_team = get_team_by_name(team_left.get())
    for left_field_player in left_field_players:
        player = left_team.get_player_by_id(left_field_player['player_id'])
        left_team_data.add_player_stats(player)
    left_team_data.ball_possession = left_team.possession
    left_players_stats_summary = convert_stats_to_summary(left_team_data, '0')

    right_team_data = TeamStats()
    right_team = get_team_by_name(team_right.get())
    for right_field_player in right_field_players:
        player = right_team.get_player_by_id(right_field_player['player_id'])
        right_team_data.add_player_stats(player)
    right_team_data.ball_possession = right_team.possession
    right_players_stats_summary = convert_stats_to_summary(right_team_data, '1')

    stats_summary = {**left_players_stats_summary, **right_players_stats_summary}
    input_data_frame = pd.DataFrame(stats_summary, index=[0])
    input_data = np.array(input_data_frame)
    results = prediction_model.predict(input_data)
    show_predicted_results(results[0][0] * 100, results[0][1] * 100, results[0][2] * 100)


def process_players():
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
                        team_id = int(team['id'])
                        teams_dic[team_id] = Team(team_id, team)
                    current_team = teams_dic[team['id']]
                    current_team.add_player(int(player_id), data_store['data'][player_id])
    teams_json_path = os.path.join(base_folder, 'resources', 'teams.json')
    with open(teams_json_path, 'r', encoding='utf8') as f:
        data_store = json.load(f)
        team_ids = data_store['data'].keys()
        for team_id in team_ids:
            if int(team_id) in teams_dic:
                season = data_store['data'][team_id]['stats']['902']['19/20']
                teams_dic[int(team_id)].set_possession(season)
    lst_to_delete = list(map(str, list(teams_dic.keys())) - data_store['data'].keys())
    for to_del in lst_to_delete:
        del teams_dic[int(to_del)]
    process_latest_lineups(teams_dic)
    return teams_dic


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
                    if teams_dic[home_team['id']].latest_lineup is None:
                        teams_dic[home_team['id']].set_latest_lineup(curr_game['lineups']['first_team'][0]['lineup'][0]['main'][0])
                        num_of_lineups_found += 1
                    if teams_dic[away_team['id']].latest_lineup is None:
                        teams_dic[away_team['id']].set_latest_lineup(curr_game['lineups']['second_team'][0]['lineup'][0]['main'][0])
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
    opt_field_team = OptionMenu(frm_field_menu, team_var, teams_names)
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

    team = get_team_by_name(team_var.get())
    player_color = team.player_uniform_color
    goalie_color = team.goalie_uniform_color
    col = 0
    row = 0
    i = 0
    global left_players
    players_arr = left_players if side == 'left' else right_players
    for player in players_arr:
        player['canvas'].grid_forget()
    players_arr.clear()
    for player_id, player in team.players.items():
        shirt_number = player.shirt_number
        position = player.position
        last_name = player.last_name
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


def draw_formation(canvas_field, formation, team_name, side):
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
    team = get_team_by_name(team_name)
    player_color = team.player_uniform_color
    goalie_color = team.goalie_uniform_color
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
    draw_formation(canvas_field_left, formation_left, team_left.get(), 'left')
    draw_formation(canvas_field_right, formation_right, team_right.get(), 'right')


def on_team_changed(side):
    team = team_left if side == 'left' else team_right
    formation = formation_left if side == 'left' else formation_right
    lst_players = lst_players_left if side == 'left' else lst_players_right
    init_all_players(None, team, -1, side, lst_players)

    latest_lineup_formation = get_team_by_name(team.get()).latest_lineup.formation
    formation.set(latest_lineup_formation)

    field_players = left_field_players if side == 'left' else right_field_players
    init_latest_players(field_players, team.get(), formation.get())


def on_formation_changed(side):
    canvas_field = canvas_field_left if side == 'left' else canvas_field_right
    formation = formation_left if side == 'left' else formation_right
    team = team_left.get() if side == 'left' else team_right.get()
    draw_formation(canvas_field, formation, team, side)


def init_latest_players(field_players, team_name, formation):
    player_positions = resources['formations'][formation]['positions']
    latest_lineup = get_team_by_name(team_name).latest_lineup.players
    for player in latest_lineup:
        player_index = player_positions[player.position]
        field_players[player_index]['player_id'] = player.id
        field_players[player_index]['shirt_number'] = player.shirt_number
        field_players[player_index]['name'] = player.name
        field_canvas = field_players[player_index]['canvas']
        txt_shirt_number = field_players[player_index]['txt_shirt_number']
        txt_name = field_players[player_index]['txt_name']
        field_canvas.itemconfig(txt_shirt_number, text=player.shirt_number)
        field_canvas.itemconfig(txt_name, text=player.name)


teams = process_players()
teams_names = list(map(lambda team: team.name, teams.values()))

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
team_left.set(teams_names[0])
team_left.trace('w', lambda context, index, mode, side='left': on_team_changed(side))
formation_left = tkinter.StringVar(window)
latest_formation_left = get_team_by_name(team_left.get()).latest_lineup.formation
formation_left.set(latest_formation_left)
formation_left.trace('w', lambda context, index, mode, side='left': on_formation_changed(side))

canvas_field_right = None
lst_players_right = None
right_players = []
right_field_players = []
right_selected_player = -1
right_selected_field_player = -1
team_right = tkinter.StringVar(window)
team_right.set(teams_names[1])
team_right.trace('w', lambda context, index, mode, side='right': on_team_changed(side))
formation_right = tkinter.StringVar(window)
latest_formation_right = get_team_by_name(team_right.get()).latest_lineup.formation
formation_right.set(latest_formation_right)
formation_right.trace('w', lambda context, index, mode, side='right': on_formation_changed(side))

init_top_menu()
init_vars()

init_latest_players(left_field_players, team_left.get(), formation_left.get())
init_latest_players(right_field_players, team_right.get(), formation_right.get())
window.mainloop()
