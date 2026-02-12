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
import os
import json
from datetime import date, time, timedelta
from zoneinfo import ZoneInfo
from discord.ext import commands, tasks
from bin.wordle_api_handler import WordleAPI

# Wordle Schedule
# 12:01AM: Rollover spoiler thread
# 12:30AM: Calculate rankings for the previous day
# 3:00AM: Update the leaderboard
# 9:00AM: Post the daily ratings (Mon - Sat), Weekly rankings (Sun)
# 5:00PM: Post the daily rankings

TZ_EST = ZoneInfo("America/New_York")

time_rollover = time(hour=0, minute=1, second=0, tzinfo=TZ_EST)
time_calculate = time(hour=0, minute=30, second=0, tzinfo=TZ_EST)
time_leaderboard = time(hour=3, minute=0, second=0, tzinfo=TZ_EST)
time_ratings = time(hour=9, minute=0, second=0, tzinfo=TZ_EST)
time_rankings = time(hour=17, minute=0, second=0, tzinfo=TZ_EST)

class WordleBot(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.wordle = WordleAPI(self.config)

        self.round_digits = 3

        self.general = int(config['discord']['general_channel_id'])
        self.lb = int(config['discord']['leaderboard_channel_id'])
        self.report = int(config['discord']['report_channel_id'])
        self.logging =int(config['discord']['logging_channel_id'])

        self.calculate_daily.start()
        self.create_new_thread.start()
        self.daily_ranks.start()
        self.daily_summary.start()
        self.leaderboard.start()

    def get_wordle_puzzle(self, today):
        first_wordle = date(2021, 6, 19)
        delta = today - first_wordle
        return delta.days
    
    def format_value(self, value: float):
        if value == None:
            return 0
        else:
            return round(value, self.round_digits)
    
    def gen_thread_name(self, today):
        puzzle = self.get_wordle_puzzle(today)
        thread_name = f"Wordle {puzzle} Official Spoiler Thread"
        # thread_name = f"Wordle_{puzzle}"
        return thread_name
    
    def gen_submission_response(self, data):
        embed = discord.Embed(
            title = f"{data['player_name']}'s Wordle {data['puzzle']} Score",
            description = f"Score: {data['score']}\nCalculated Score: {data['calculated_score']}\nHard Mode: {'Y' if data['hard_mode'] == 1 else 'N'}"
        )
        return embed
    
    def gen_score_response(self, player, data):
        embed = discord.Embed(
            title = f"{player}'s Wordle {data['puzzle']} Score",
            description = f"{data['raw_score']}\n\nWith a raw score of {data['score']}, their calculated score is: {data['calculated_score']}"
        )
        return embed

    # ---
    # Event Listeners
    # ---
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"WordleBot Loaded")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == bot.user:
            return

        if str(message.channel) == 'general':
            if re.match(r'Wordle ([\d,]+) ([\dX])\/6(\*?)', message.content[0:16]):
                data = self.wordle.add_score(message.content, message.author.name)
                if data.get('status', 500) != 200:
                    response = f"Error {data.get('status', 500)} from server, please contact a Wordle admin."
                    msg = data.get('msg', response)
                    await message.channel.send(msg)
                else:
                    active_threads = await message.guild.active_threads()
                    desired_thread = None

                    for thread in active_threads:
                        if thread.name == self.gen_thread_name(date.today()):
                            desired_thread = thread

                    if desired_thread == None:
                        desired_thread = await self.create_new_thread()

                    await desired_thread.add_user(message.author)
                    # await desired_thread.send(f"{message.author.mention} has been added to the thread.")
                    await desired_thread.send(embed=self.gen_submission_response(data))

    # ---
    # Scheduled Tasks
    # ---
    @tasks.loop(time=time_calculate)
    async def calculate_daily(self):
        today = date.today()
        yesterday = today - timedelta(days=1)
        channel = self.bot.get_channel(self.logging)

        res = self.wordle.calculate_daily(yesterday)

        await channel.send(json.dumps(res, indent=4))

    @tasks.loop(time=time_rollover)
    async def create_new_thread(self):
        channel = self.bot.get_channel(self.general)
        puzzle = self.get_wordle_puzzle(date.today())
        prev_thread = self.gen_thread_name(date.today() - timedelta(days=1))
        active_threads = await channel.guild.active_threads()

        for thread in active_threads:
            if thread.name == prev_thread:
                await thread.edit(locked=True, reason='This Wordle is now over, you are free to talk about spoilers in the general chat.')

        if channel:
            thread = await channel.create_thread(
                name=self.gen_thread_name(date.today()),
                auto_archive_duration=1440,
                type=discord.ChannelType.private_thread,
                invitable=False,
                reason="Starting spoiler thread"
            )
            await thread.send(f"Thread for Wordle {puzzle} created! Please keep all spoilers to this thread.")
        return thread
    
    @tasks.loop(time=time_rankings)
    async def daily_ranks(self):
        today = date.today()
        res = self.wordle.daily_ranks(today)
        channel = self.bot.get_channel(self.general)

        if res.get('status', 200) == 404:
            return False

        embed = discord.Embed(title=f"{today}: Wordle Rankings")

        for player in res['raw_data']:
            embed.add_field(
                name=f"{player['rank']}. {player['player_name']}",
                value=f"Hard Mode: {player['hard_mode']}",
                inline=False
            )

        await channel.send(embed=embed)
    
    @tasks.loop(time=time_ratings)
    async def daily_summary(self):
        today = date.today()
        yesterday = today - timedelta(days=1)
        channel = self.bot.get_channel(self.report)

        if today.weekday() == 6:
            res = self.wordle.weekly_summary(yesterday)
            if res.get('status', 200) == 404:
                return False
            
            embed = discord.Embed(title=f"**{today}: Weekly Wordle Rankings**")

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


                data_points = [
                    f"Ordinal: {self.format_value(stats['start_ord'])} -> {self.format_value(stats['end_ord'])} (Δ {self.format_value(stats['ord_change'])})",
                    f"ELO: {self.format_value(stats['start_elo'])} -> {self.format_value(stats['end_elo'])} (Δ {self.format_value(stats['elo_change'])})",
                    f"Average Score: {stats['average_score']}"
                ]

                embed.add_field(
                    name=f"{i}. {player}",
                    value='\n'.join(data_points),
                    inline=False
                )

            await channel.send(embed=embed)
        else:
            res = self.wordle.daily_summary(today)
            

            if res.get('status', 200) == 404:
                return False
            
            embed = discord.Embed(title=f"**{today}: Wordle Rankings**")

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
                
                data_points = [
                    f"Ordinal: {self.format_value(stats['end_ord'])} (Δ {self.format_value(stats['ord_change'])})",
                    f"ELO: {self.format_value(stats['end_elo'])} (Δ {self.format_value(stats['elo_change'])})",
                ]

                embed.add_field(
                    name=f"{i}. {player}",
                    value='\n'.join(data_points),
                    inline=False
                )

            await channel.send(embed=embed)

    @tasks.loop(time=time_leaderboard)
    async def leaderboard(self):
        today = date.today()
        data = self.wordle.leaderboard()
        channel = self.bot.get_channel(self.lb)

        embed = discord.Embed(title=f"Wordle Leaderboard ({today})")

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
            
            data_points = [
                f"Ordinal: {self.format_value(player['player_ord'])} (Δ {self.format_value(player['ord_delta'])})",
                f"ELO: {self.format_value(player['player_elo'])} (Δ {self.format_value(player['elo_delta'])})",
                f"Mu: {self.format_value(player['player_mu'])} (Δ {self.format_value(player['mu_delta'])})",
                f"Sigma: {self.format_value(player['player_sigma'])} (Δ {self.format_value(player['sigma_delta'])})",
            ]

            embed.add_field(
                name=f"{i}. {player['player_name']}",
                value='\n'.join(data_points),
                inline=True
            )

        await channel.send(embed=embed)

    # ---
    # Commands
    # ---

    @commands.command()
    async def score(self, ctx, puzzle: int, player: str = False):
        if player == False:
            player = ctx.message.author.name
        data = self.wordle.check_score(player, puzzle)
        if data.get('status', 200) == 404:
            msg = f"{player} did not play Wordle #{puzzle}"
            await ctx.send(msg)
        else:
            await ctx.send(embed=self.gen_score_response(player, data))
        
    
    @commands.command()
    async def blame(self, ctx, puzzle: int, player: str = False):
        if player == False:
            player = ctx.message.author.name
        data = self.wordle.blame(player, puzzle)
        embed = discord.Embed(
            description = data.get('msg', f"Error while processing blame data for {player} in Wordle {puzzle}")
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def register(self, ctx, name: str = False):
        if name == False:
            name = ctx.message.author.name
        data = self.wordle.register(name, 'discord', ctx.message.author.name)
        if data.get('status', 200) == 409:
            await ctx.send(f"@{ctx.message.author.name} is already registered to play Wordle!")
        else:
            await ctx.send(f"Successfully registered @{data['player_uuid']} as {data['player_name']}")

    @commands.command()
    async def update(self, ctx, name: str = False):
        if name == False:
            await ctx.send("Please include a name to update the registration to, ex: `!update WordleBot`")
            return False
        data = self.wordle.update_registration(name, 'discord', ctx.message.author.name)
        await ctx.send(f"Successfully updated @{data['player_uuid']} to {data['player_name']}")
    
    @commands.command()
    async def diagnose(self, ctx):
        await ctx.send(f"Checking in, it is currently {date.today()}")

# ---
# Get this show on the road
# ---
config_file = os.getenv('CONFIG_FILE', 'config.yml')
with open(config_file, 'r') as f:
    config = yaml.safe_load(f)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    if "WordleBot" in bot.cogs:
        print("WordleBot cog already loading, skipping...")
    else:
        await bot.add_cog(WordleBot(bot, config))

bot.run(config['discord']['token'])