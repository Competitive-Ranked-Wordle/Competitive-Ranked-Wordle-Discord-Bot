"""
Competitive Ranked Wordle Daily Calculations Script

Copyright (C) 2025  Jivan RamjiSingh

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import requests
import random
import json
from datetime import date, timedelta
from wordle_api_handler import WordleAPI

class WordleCalculations:
    def __init__(self, config: dict, wordle: WordleAPI, round_digits: int = 3):
        self.lb = config['discord']['leaderboard_webhook']
        self.general = config['discord']['general_webhook']
        self.report = config['discord']['report_webhook']
        self.dev = config['discord']['dev_webhook']
        self.lb_message = config['discord']['leaderboard_message']

        self.today = date.today()
        self.yesterday = self.today - timedelta(days=1)

        self.wordle = wordle

        self.round_digits = round_digits

    def format_value(self, value: float):
        if value == None:
            return 0
        else:
            return round(value, self.round_digits)

    def calculate_daily(self):
        res = self.wordle.calculate_daily(self.yesterday)
    
    def daily_ranks(self):
        res = self.wordle.daily_ranks(self.today)
        if res.get('status', 200) == 404:
            return False
        
        webhook = {
            "content": f"**{self.today}: Wordle Rankings**",
            "embeds": [],
            "attachments": []
        }
        for player in res['raw_data']:
            lb_entry = {
                "title": f"{player['rank']}. {player['player_name']}",
                "description": f"Hard Mode: {player['hard_mode']}",
                "color": random.randint(0, 16777215),
            }
            webhook['embeds'].append(lb_entry)
        
        res = requests.post(self.general, data=json.dumps(webhook), headers={'Content-Type': 'application/json'})

    
    def daily_summary(self):
        res = self.wordle.daily_summary(self.today)
        if res.get('status', 200) == 404:
            return False
        webhook = {
            "content": f"**{self.today}: Wordle Rankings**",
            "embeds": [],
            "attachments": []
        }

        i = 0
        n = 0
        last_ord = False
        for player, stats in res['sorted_player_stats'].items():
            if stats['end_ord'] == last_ord:
                n += 1
            else:
                last_ord = stats['end_ord']
                i += 1 + n
                n = 0
            lb_entry = {
                "title": f"{i}. {player}",
                "color": random.randint(0, 16777215),
                "fields": [
                    {
                        "name": f"Ordinal: {self.format_value(stats['end_ord'])}",
                        "value": f"Δ {self.format_value(stats['ord_change'])}",
                        "inline": True
                    },
                    {
                        "name": f"ELO: {self.format_value(stats['end_elo'])}",
                        "value": f"Δ {self.format_value(stats['elo_change'])}",
                        "inline": True
                    }
                ]
            }
            webhook['embeds'].append(lb_entry)
        res = requests.post(self.report, data=json.dumps(webhook), headers={'Content-Type': 'application/json'})


    def weekly_summary(self):
        res = self.wordle.weekly_summary(self.today)
        if res.get('status', 200) == 404:
            return False
        webhook = {
            "content": f"**{self.today}: Weekly Wordle Rankings**",
            "embeds": [],
            "attachments": []
        }
        i = 0
        n = 0
        last_ord = False
        for player, stats in res['sorted_player_stats'].items():
            if stats['end_ord'] == last_ord:
                n += 1
            else:
                last_ord = stats['end_ord']
                i += 1 + n
                n = 0
            lb_entry = {
                "title": f"{i}. {player}",
                "color": random.randint(0, 16777215),
                "fields": [
                    {
                        "name": f"Ordinal: {self.format_value(stats['start_ord'])} -> {self.format_value(stats['end_ord'])}",
                        "value": f"Δ {self.format_value(stats['ord_change'])}",
                        "inline": True
                    },
                    {
                        "name": f"ELO: {self.format_value(stats['start_elo'])} -> {self.format_value(stats['end_elo'])}",
                        "value": f"Δ {self.format_value(stats['elo_change'])}",
                        "inline": True
                    },
                    {
                        "name": f"Average Score: {stats['average_score']}",
                        "value": f"",
                        "inline": True
                    },
                ]
            }
            webhook['embeds'].append(lb_entry)
        res = requests.post(self.report, data=json.dumps(webhook), headers={'Content-Type': 'application/json'})

    def leaderboard(self):
        data = self.wordle.leaderboard()
        webhook = {
            "content": f"Wordle Leaderboard ({self.today})",
            "embeds": [],
            "attachments": []
        }

        i = 0
        n = 0
        last_ord = False
        for player in data:
            if player['player_ord'] == last_ord:
                n += 1
            else:
                i += 1 + n
                n = 0
                last_ord = player['player_ord']
            lb_entry = {
                "title": f"{i}. {player['player_name']}",
                "color": random.randint(0, 16777215),
                "fields": [
                    {
                        "name": f"Ordinal: {self.format_value(player['player_ord'])}",
                        "value": f"Δ {self.format_value(player['ord_delta'])}",
                        "inline": True
                    },
                    {
                        "name": f"ELO: {self.format_value(player['player_elo'])}",
                        "value": f"Δ {self.format_value(player['elo_delta'])}",
                        "inline": True
                    },
                    {
                        "name": f"Mu: {self.format_value(player['player_mu'])}",
                        "value": f"Δ {self.format_value(player['mu_delta'])}",
                        "inline": True
                    },
                    {
                        "name": f"Sigma: {self.format_value(player['player_sigma'])}",
                        "value": f"Δ {self.format_value(player['sigma_delta'])}",
                        "inline": True
                    }
                ]
            }
            webhook['embeds'].append(lb_entry)
        
        if self.lb_message:
            res = requests.patch(f"{self.lb}/messages/{self.lb_message}", data=json.dumps(webhook), headers={'Content-Type': 'application/json'})
        else:
            res = requests.post(self.lb, data=json.dumps(webhook), headers={'Content-Type': 'application/json'})

if __name__ == '__main__':
    import yaml
    import argparse
    import os

    parser = argparse.ArgumentParser(description='Competitive Ranked Wordle Backend Calculations Script')
    parser.add_argument('mode', choices=['calculate_daily', 'daily_ranks', 'daily_summary', 'weekly_summary', 'leaderboard'])
    parser.add_argument('--config', default='config.yml')

    args = parser.parse_args()

    config_file = os.getenv('CONFIG_FILE', args.config)
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    wordle = WordleAPI(config)
    calculations = WordleCalculations(config, wordle)

    match args.mode:
        case 'calculate_daily':
            calculations.calculate_daily()
        case 'daily_ranks':
            calculations.daily_ranks()
        case 'daily_summary':
            calculations.daily_summary()
        case 'weekly_summary':
            calculations.weekly_summary()
        case 'leaderboard':
            calculations.leaderboard()