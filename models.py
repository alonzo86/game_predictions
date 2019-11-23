from utils import safe_div


class TeamStats:
    def __init__(self, team_stats):
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
        tmp_missed_penalty = team_stats.get('MissedPenalty', 0)

        penalty_kick_goals = safe_div(tmp_penalty_kick_goals, tmp_penalty_kicks)

        # Goals
        tmp_regular_goals = team_stats.get('GoalRegular', 0)
        tmp_attempts_on_goal = team_stats.get('AttemptonGoal', 0)
        tmp_shots_inside_the_area = team_stats.get('ShotInsidetheArea', 0)
        tmp_shots_outside_the_area = team_stats.get('ShotOutsidetheArea', 0)
        tmp_shots_on_target = team_stats.get('OnTarget', 0)
        tmp_shots_off_target = team_stats.get('missedShot', 0)
        tmp_blocked_shots = team_stats.get('blockedShot', 0)
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
        tmp_headers = team_stats.get('Header', 0)

        direct_crosses_into_the_area = safe_div(tmp_direct_crosses_into_the_area, tmp_crosses)

        # Passing
        tmp_passes = team_stats.get('passes', 0)
        tmp_non_attacking_passes = team_stats.get('nonAttackingPasses', 0)
        tmp_attacking_passes = team_stats.get('attackingPasses', 0)
        tmp_accurate_passes = team_stats.get('accuratePasses', 0)
        tmp_key_passes = team_stats.get('keyPasses', 0)
        tmp_long_balls = team_stats.get('longBall', 0)
        tmp_accurate_long_balls = team_stats.get('accurateLongBall', 0)

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
