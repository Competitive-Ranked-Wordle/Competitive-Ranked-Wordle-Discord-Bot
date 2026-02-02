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
from datetime import date, time, timedelta
from zoneinfo import ZoneInfo
from discord.ext import commands, tasks
from bin.wordle_api_handler import WordleAPI

tz_eastern = ZoneInfo('America/New_York')
wordle_rollover = time(hour=0, minute=1, second=0, tzinfo=tz_eastern)

class WordleBot(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.wordle = WordleAPI(self.config)

        self.general = int(config['discord']['general_channel_id'])

        self.create_new_thread.start()

    def get_wordle_puzzle(self, today):
        first_wordle = date(2021, 6, 19)
        delta = today - first_wordle
        return delta.days
    
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

    # @bot.event
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
    @tasks.loop(time=wordle_rollover)
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

    # ---
    # Commands
    # ---

    # @bot.command()
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
        
    
    # @bot.command()
    @commands.command()
    async def blame(self, ctx, puzzle: int, player: str = False):
        if player == False:
            player = ctx.message.author.name
        data = self.wordle.blame(player, puzzle)
        embed = discord.Embed(
            description = data.get('msg', f"Error while processing blame data for {player} in Wordle {puzzle}")
        )
        await ctx.send(embed=embed)

    # @bot.command()
    @commands.command()
    async def register(self, ctx, name: str = False):
        if name == False:
            name = ctx.message.author.name
        data = self.wordle.register(name, 'discord', ctx.message.author.name)
        if data.get('status', 200) == 409:
            await ctx.send(f"@{ctx.message.author.name} is already registered to play Wordle!")
        else:
            await ctx.send(f"Successfully registered @{data['player_uuid']} as {data['player_name']}")

    # @bot.command()
    @commands.command()
    async def update(self, ctx, name: str = False):
        if name == False:
            await ctx.send("Please include a name to update the registration to, ex: `!update WordleBot`")
            return False
        data = self.wordle.update_registration(name, 'discord', ctx.message.author.name)
        await ctx.send(f"Successfully updated @{data['player_uuid']} to {data['player_name']}")

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
    await bot.add_cog(WordleBot(bot, config))

bot.run(config['discord']['token'])