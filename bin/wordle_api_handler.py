"""
Competitive Ranked Wordle API Handler

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

class WordleAPI:
    def __init__(self, config):
        self.base_url = config['wordle']['base_url']
        self.username = config['wordle']['username']
        self.password = config['wordle']['password']

    def auth(self):
        data = {
            'grant_type': 'password',
            'username': self.username,
            'password': self.password
        }
        req = requests.post(f"{self.base_url}/token", data=data)
        body = req.json()
        return body['access_token']

    def create_headers(self):
        headers = {
            'Authorization': f"Bearer {self.auth()}"
        }
        return headers

    def register(self, player_name: str, player_platform: str, player_uuid: str):
        data = {
            "player_name": player_name,
            "player_platform": player_platform,
            "player_uuid": player_uuid
        }
        req = requests.post(f"{self.base_url}/register", headers=self.create_headers(), json=data)
        return req.json()

    def update_registration(self, player_name: str, player_platform: str, player_uuid: str):
        data = {
            "player_name": player_name,
            "player_platform": player_platform,
            "player_uuid": player_uuid
        }
        req = requests.post(f"{self.base_url}/update-registration", headers=self.create_headers(), json=data)
        return req.json()

    def add_score(self, score: str, uuid: str):
        data = {
            'score': score,
            'uuid': uuid
        }
        req = requests.post(f"{self.base_url}/add-score", headers=self.create_headers(), json=data)
        return req.json()

    def check_score(self, uuid: str, puzzle: int):
        req = requests.get(f"{self.base_url}/score/{uuid}?puzzle={puzzle}", headers=self.create_headers())
        return req.json()

    def blame(self, uuid: str, puzzle: int):
        req = requests.get(f"{self.base_url}/blame/{uuid}?puzzle={puzzle}", headers=self.create_headers())
        return req.json()
    
    def leaderboard(self):
        req = requests.get(f"{self.base_url}/leaderboard", headers=self.create_headers())
        return req.json()