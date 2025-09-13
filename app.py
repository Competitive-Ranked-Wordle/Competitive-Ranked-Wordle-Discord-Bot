"""
Competitive Ranked Wordle Discord Bot
    A Discord bot application to handle user submissions and reporting

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

# ---
# Imports
# ---
import discord
import yaml
import re
import random
import requests
import json
from datetime import date
from discord.ext import commands
from bin.wordle_api_handler import WordleAPI

# ---
# Data Definition & Library Configuration
# ---
with open('config.yml', 'r') as f:
    config = yaml.safe_load(f)

description = "A Discord Bot to handle Competitive Ranked Wordle play :)"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
# client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix="!", description=description, intents=intents)

wordle = WordleAPI(config)

# ---
# Discord Bot Events
# ---
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if str(message.channel) == 'wordle-dev':
        if re.match(r'Wordle ([\d,]+) ([\dX])\/6(\*?)', message.content[0:16]):
            data = wordle.add_score(message.content, message.author.name)
            if data.get('status', 200) == 409:
                msg = f"You have already submitted your Wordle score today. In the future, you can reference your score by typing `!score` with the puzzle number, ex. `!score 1546`"
            else:
                msg = f"""Wordle Score for {data['player_name']}
Puzzle: {data['puzzle']}
Score: {data['score']}
Calculated Score: {data['calculated_score']}
Hard Mode: {'Y' if data['hard_mode'] == 1 else 'N'}
"""
            await message.channel.send(msg)
    
    await bot.process_commands(message)
        

# ---
# Bot Commands
# ---
@bot.command()
async def score(ctx, puzzle: int, player: str = False):
    if player == False:
        player = ctx.message.author.name
    data = wordle.check_score(player, puzzle)
    if data.get('status', 200) == 404:
        msg = f"{player} did not play Wordle #{puzzle}"
    else:
        msg = f"""{data['player_information']['player_name']}'s Performance on Wordle #{puzzle}:
{data['raw_score']}

With a raw score of {data['score']}, that brings their calculated score to: {data['calculated_score']}
"""
    await ctx.send(msg)

@bot.command()
async def blame(ctx, puzzle: int, player: str = False):
    if player == False:
        player = ctx.message.author.name
    data = wordle.blame(player, puzzle)
    await ctx.send(data['msg'])

@bot.command()
async def register(ctx, name: str = False):
    if name == False:
        name = ctx.message.author.name
    data = wordle.register(name, 'discord', ctx.message.author.name)
    if data.get('status', 200) == 409:
        await ctx.send(f"@{ctx.message.author.name} is already registered to play Wordle!")
    else:
        await ctx.send(f"Successfully registered @{data['player_uuid']} as {data['player_name']}")

@bot.command()
async def update(ctx, name: str = False):
    if name == False:
        await ctx.send("Please include a name to update the registration to, ex: `!update WordleBot`")
        return False
    data = wordle.update_registration(name, 'discord', ctx.message.author.name)
    await ctx.send(f"Successfully updated @{data['player_uuid']} to {data['player_name']}")

@bot.command()
async def leaderboard(ctx):
    data = wordle.leaderboard()
    webhook = {
        "content": f"Current Wordle Leaderboard ({date.today()})",
        "embeds": [],
        "attachments": []
    }

    i = 0
    n = 0
    last_ord = False
    round_digits = 3
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
                    "name": f"Ordinal: {round(player['player_ord'], round_digits)}",
                    "value": f"Δ {round(player['ord_delta'], round_digits)}",
                    "inline": True
                },
                {
                    "name": f"ELO: {round(player['player_elo'], round_digits)}",
                    "value": f"Δ {round(player['elo_delta'], round_digits)}",
                    "inline": True
                },
                {
                    "name": f"Mu: {round(player['player_mu'], round_digits)}",
                    "value": f"Δ {round(player['mu_delta'], round_digits)}",
                    "inline": True
                },
                {
                    "name": f"Sigma: {round(player['player_sigma'], round_digits)}",
                    "value": f"Δ {round(player['sigma_delta'], round_digits)}",
                    "inline": True
                }
            ]
        }
        webhook['embeds'].append(lb_entry)
    
    res = requests.post(config['discord']['webhook'], data=json.dumps(webhook), headers={'Content-Type': 'application/json'})

bot.run(config['discord']['token'])