import json
import os
import runpy
import tkinter
import warnings
from threading import Thread
from tkinter import Button, Canvas, Frame, OptionMenu, N, Toplevel

import numpy as np
import pandas as pd
import tensorflow as tf
import wget
from PIL import Image, ImageTk
from webcolors import hex_to_rgb

from models import Team, TeamStats, FieldPlayer, SubstitutePlayer, UITeam
from utils import get_dictionary_item_by_property

warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=DeprecationWarning)
tf.compat.v1.enable_eager_execution()
np.set_printoptions(formatter={'float': lambda x: "{0:0.3f}".format(x)})

base_folder = os.path.dirname(__file__)


class EventArgs:
    def __init__(self, ui_team: UITeam, index: int):
        self.ui_team = ui_team
        self.index = index


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


def show_predicted_results(win_percent, draw_percent, loss_percent, home_name, home_color, away_name, away_color):
    msg_results = Toplevel()
    msg_results.grab_set()
    msg_results.wm_title('Prediction results')

    canvas_bars = Canvas(msg_results, width=300, height=200)

    bar_height_factor = 2
    bottom_line = 160

    canvas_bars.create_line(20, bottom_line, 280, bottom_line)

    canvas_bars.create_rectangle(20, bottom_line, 80, bottom_line - win_percent * bar_height_factor, fill=home_color)
    canvas_bars.create_text(50, bottom_line - win_percent * bar_height_factor - 10, font='Times 10 bold', text='%.2f%%' % win_percent)
    canvas_bars.create_text(50, bottom_line + 10, font='Times 10 bold', text=home_name)

    canvas_bars.create_rectangle(120, bottom_line, 180, bottom_line - draw_percent * bar_height_factor, fill='#dedede')
    canvas_bars.create_text(150, bottom_line - draw_percent * bar_height_factor - 10, font='Times 10 bold', text='%.2f%%' % draw_percent)
    canvas_bars.create_text(150, bottom_line + 10, font='Times 10 bold', text='Draw')

    canvas_bars.create_rectangle(220, bottom_line, 280, bottom_line - loss_percent * bar_height_factor, fill=away_color)
    canvas_bars.create_text(250, bottom_line - loss_percent * bar_height_factor - 10, font='Times 10 bold', text='%.2f%%' % loss_percent)
    canvas_bars.create_text(250, bottom_line + 10, font='Times 10 bold', text=away_name)

    canvas_bars.pack()


def predict_result():

    def convert_stats_to_summary(team_data: TeamStats, team_index):
        return {
            'ball_possession_%s' % team_index: team_data.ball_possession,
            'own_half_ball_losses_%s' % team_index: team_data.own_half_ball_losses,
            'opponent_half_ball_recoveries_%s' % team_index: team_data.opponent_half_ball_recoveries,
            'own_half_ball_recoveries_%s' % team_index: team_data.own_half_ball_recoveries,
            'successful_tackles_%s' % team_index: team_data.successful_tackles,
            'fouls_%s' % team_index: team_data.fouls,
            'yellow_cards_%s' % team_index: team_data.yellow_cards,
            'red_cards_%s' % team_index: team_data.red_cards,
            'penalty_kick_goals_%s' % team_index: team_data.penalty_kick_goals,
            'shots_on_goal_%s' % team_index: team_data.shots_on_goal,
            'shots_inside_the_area_%s' % team_index: team_data.shots_inside_the_area,
            'shots_outside_the_area_%s' % team_index: team_data.shots_outside_the_area,
            'shots_on_target_%s' % team_index: team_data.shots_on_target,
            'shots_off_target_%s' % team_index: team_data.shots_off_target,
            'shots_after_right_side_attacks_%s' % team_index: team_data.shots_after_right_side_attacks,
            'shots_after_center_attacks_%s' % team_index: team_data.shots_after_center_attacks,
            'shots_after_left_side_attacks_%s' % team_index: team_data.shots_after_left_side_attacks,
            'direct_crosses_into_the_area_%s' % team_index: team_data.direct_crosses_into_the_area,
            'attacking_passes_%s' % team_index: team_data.attacking_passes,
            'key_passes_%s' % team_index: team_data.key_passes,
            'air_challenges_won_%s' % team_index: team_data.air_challenges_won,
            'ground_challenges_won_%s' % team_index: team_data.ground_challenges_won,
            'dribbles_won_%s' % team_index: team_data.dribbles_won,
        }

    left_team_data = TeamStats()
    left_team = get_team_by_name(home_team.name.get())
    for left_field_player in home_team.field_players:
        player = left_team.get_player_by_id(left_field_player.player_id)
        left_team_data.add_player_stats(player)
    left_team_data.ball_possession = left_team.possession
    left_players_stats_summary = convert_stats_to_summary(left_team_data, '0')

    right_team_data = TeamStats()
    right_team = get_team_by_name(away_team.name.get())
    for right_field_player in away_team.field_players:
        player = right_team.get_player_by_id(right_field_player.player_id)
        right_team_data.add_player_stats(player)
    right_team_data.ball_possession = right_team.possession
    right_players_stats_summary = convert_stats_to_summary(right_team_data, '1')

    stats_summary = {**left_players_stats_summary, **right_players_stats_summary}
    input_data_frame = pd.DataFrame(stats_summary, index=[0])
    input_data = np.array(input_data_frame)
    results = prediction_model.predict(input_data)
    show_predicted_results(results[0][0] * 100, results[0][1] * 100, results[0][2] * 100, left_team.name, left_team.player_uniform_color, right_team.name, right_team.player_uniform_color)


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
                    home_team_id = curr_game['homeTeamId']['id']
                    away_team_id = curr_game['awayTeamId']['id']
                    if teams_dic[home_team_id].latest_lineup is None:
                        teams_dic[home_team_id].set_latest_lineup(curr_game['lineups']['first_team'][0]['lineup'][0]['main'][0])
                        num_of_lineups_found += 1
                    if teams_dic[away_team_id].latest_lineup is None:
                        teams_dic[away_team_id].set_latest_lineup(curr_game['lineups']['second_team'][0]['lineup'][0]['main'][0])
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
    frm_fields = Frame(window)
    frm_fields.grid(column=0, row=1)
    left_canvas = init_field(frm_fields, home_team, 0)
    init_substitute_players(frm_fields, 0, home_team)
    right_canvas = init_field(frm_fields, away_team, 2)
    init_substitute_players(frm_fields, 2, away_team)
    return left_canvas, right_canvas


def init_field(parent, ui_team: UITeam, column):
    frm_field_menu = Frame(parent)
    frm_field_menu.grid(column=column, row=0, sticky=tkinter.NW)
    opt_field_team = OptionMenu(frm_field_menu, ui_team.name, teams_names)
    opt_field_team.grid(column=0, row=0, sticky=tkinter.NW)
    opt_field_formation = OptionMenu(frm_field_menu, ui_team.formation, *resources['formations'].keys())
    opt_field_formation.grid(column=1, row=0, sticky=tkinter.NW)

    frm_field = Frame(parent)
    frm_field.grid(column=column, row=1, sticky=tkinter.N)

    photo_image = ImageTk.PhotoImage(resources['field'])
    canvas_field = Canvas(frm_field, width=564, height=900)
    canvas_field.image = photo_image
    canvas_field.create_image(0, 0, anchor=tkinter.NW, image=photo_image)
    canvas_field.pack()
    return canvas_field


def init_substitute_players(parent, column, ui_team: UITeam):
    if ui_team.players is None:
        ui_team.players = Frame(parent)
        ui_team.players.grid(column=column + 1, row=1, sticky=N)

    team = get_team_by_name(ui_team.name.get())
    player_color = team.player_uniform_color
    goalie_color = team.goalie_uniform_color
    col = 0
    row = 0
    index = 0
    for player in ui_team.substitute_players:
        player.canvas.grid_forget()
    ui_team.substitute_players.clear()
    for player_id, player in team.players.items():
        shirt_number = player.shirt_number
        position = player.position
        last_name = player.last_name
        canvas_player = Canvas(ui_team.players, width=80, height=90)
        polygon_color = goalie_color if position == 'goalie' else player_color
        font_color = '#fff' if is_polygon_dark(polygon_color) else '#000'
        player_canvas_id = canvas_player.create_polygon(resources['shirt_path'], outline='#000', fill=polygon_color)
        canvas_player.create_text(35, 30, fill=font_color, font='Times 20 bold', text=shirt_number)
        canvas_player.create_text(35, 50, fill=font_color, font='Times 8', text=last_name)
        canvas_player.create_text(35, 70, fill='#000', font='Times 8', text=position)
        canvas_player.bind('<Button-1>', lambda event, arg=index: ui_team.select_player(False, arg))
        canvas_player.grid(column=col, row=row)
        ui_team.substitute_players.append(SubstitutePlayer(canvas_player, player_canvas_id, player_id, shirt_number, last_name))
        row += 1
        index += 1
        if row > 8:
            row = 0
            col += 1


def draw_formation(ui_team: UITeam):
    index = 0
    for field_player in ui_team.field_players:
        tag = 'polygon_%s' % index
        ui_team.canvas.tag_unbind(tag, '<Button-1>')
        ui_team.canvas.delete(field_player.player_canvas_id)
        ui_team.canvas.delete(field_player.shirt_number_canvas_id)
        ui_team.canvas.delete(field_player.name_canvas_id)
        index += 1
    ui_team.field_players.clear()
    team = get_team_by_name(ui_team.name.get())
    player_color = team.player_uniform_color
    goalie_color = team.goalie_uniform_color
    formation_map = resources['formations'][ui_team.formation.get()]['points']
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
        player_canvas_id = ui_team.canvas.create_polygon(points, outline='#000', fill=polygon_color, tag=tag)
        shirt_number_canvas_id = ui_team.canvas.create_text(points[0] + 35, points[1] + 10, fill=font_color, font='Times 20 bold', text='')
        name_canvas_id = ui_team.canvas.create_text(points[0] + 35, points[1] + 30, fill=font_color, font='Times 8', text='')
        ui_team.field_players.append(FieldPlayer(ui_team.canvas, player_canvas_id, shirt_number_canvas_id, name_canvas_id))
        ui_team.canvas.tag_bind(tag, '<Button-1>', lambda event, arg=index: ui_team.select_player(True, arg))
        index += 1


def on_player_selected(event_args: EventArgs):
    event_args.ui_team.select_player(True, event_args.index)


def init_vars():
    home_team.canvas, away_team.canvas = init_fields()
    draw_formation(home_team)
    draw_formation(away_team)


def on_team_changed(ui_team: UITeam):
    init_substitute_players(None, -1, ui_team)

    latest_lineup_formation = get_team_by_name(ui_team.name.get()).latest_lineup.formation
    ui_team.formation.set(latest_lineup_formation)

    init_latest_players(ui_team)


def on_formation_changed(ui_team):
    draw_formation(ui_team)


def init_latest_players(ui_team):
    player_positions = resources['formations'][ui_team.formation.get()]['positions']
    latest_lineup = get_team_by_name(ui_team.name.get()).latest_lineup.players
    for player in latest_lineup:
        player_index = player_positions[player.position]
        ui_team.field_players[player_index].player_id = player.id
        ui_team.field_players[player_index].shirt_number = player.shirt_number
        ui_team.field_players[player_index].name = player.name
        field_canvas = ui_team.field_players[player_index].canvas
        txt_shirt_number = ui_team.field_players[player_index].shirt_number_canvas_id
        txt_name = ui_team.field_players[player_index].name_canvas_id
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

home_default_name = teams_names[0]
home_latest_formation = get_team_by_name(home_default_name).latest_lineup.formation
home_team = UITeam(window, home_default_name, home_latest_formation)
home_team.name.trace('w', lambda context, index, mode, ui_team=home_team: on_team_changed(ui_team))
home_team.formation.trace('w', lambda context, index, mode, ui_team=home_team: on_formation_changed(ui_team))

away_default_name = teams_names[1]
away_latest_formation = get_team_by_name(away_default_name).latest_lineup.formation
away_team = UITeam(window, away_default_name, away_latest_formation)
away_team.name.trace('w', lambda context, index, mode, ui_team=away_team: on_team_changed(ui_team))
away_team.formation.trace('w', lambda context, index, mode, ui_team=away_team: on_formation_changed(ui_team))

init_top_menu()
init_vars()

init_latest_players(home_team)
init_latest_players(away_team)
window.mainloop()
