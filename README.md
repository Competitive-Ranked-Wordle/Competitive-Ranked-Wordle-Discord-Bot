# Discord Wordle Bot

A simple Discord bot that facilitates gameplay of [Competitive Ranked Wordle](https://github.com/jivandabeast/Competitive-Ranked-Wordle/tree/master)

## Commands and Features

1. Automatically parse Wordle submissions in the #general channel

2. `!register [Display Name]`: Registers a user to be included in the game, this is a **required** step in order to play Competitive Ranked Wordle.

3. `!update [Display Name]`: Updates a user's display name, in the event that they want to change it

4. `!score [Player Username?]`: Displays a user's Wordle submission for a given day, if a user is not specified it will display the score of the requestor

5. `!blame [Puzzle] [Player Username?]`: Displays a user's ELO gain/loss for a given Puzzle, this can be done even before the calculations are run for a given day (to provide an estimate of how their ELO will change). If a user is not specified, it will output for the requestor.

6. `!leaderboard`: Sends an updated ranking leaderboard (containing all users) to the #leaderboard channel. This command is roadmapped for deletion, in favor of a daily-updated leaderboard.

## Setup

### Docker

1. Pull the git repository

`git clone https://github.com/jivandabeast/Competitive-Ranked-Wordle-Discord-Bot`

2. Build the Docker image

`cd Competitive-Ranked-Wordle-Discord-Bot`

`docker build -t crw-discord-bot .`

3. Create a folder for the resources & create required files

```
$ mkdir /docker/crw-discord-bot
$ wget https://raw.githubusercontent.com/jivandabeast/Competitive-Ranked-Wordle-Discord-Bot/refs/heads/master/config.yml.sample
$ mv config.yml.sample config.yml
```

4. Edit `config.yml` with all the required data

5. Execute the docker image

`docker run -d --name crw-discord-bot -v /docker/crw-discord-bot:/data -e CONFIG_FILE=/data/config.yml crw-discord-bot`

6. Log in to your Discord server, and register with `!register` to ensure that the bot has connected and is operational

7. Edit the server crontab to enable reporting functionality

```crontab
# Sample Wordle Schedule
# 12:30AM: Calculate rankings for the previous day
# 3:00AM: Update the leaderboard
# 9:00AM: Post the daily ratings (Mon - Sat), Weekly rankings (Sun)
# 5:00PM: Post the daily rankings

# Wordle Daily Calculations
30 0 * * * docker exec -it crw-discord-bot python3 /wordlebot/bin/backend_handler.py calculate_daily >/dev/null 2>&1
# Wordle Daily Leaderboard Update
0 3 * * * docker exec -it crw-discord-bot python3 /wordlebot/bin/backend_handler.py leaderboard >/dev/null 2>&1
# Wordle Daily Ranks
0 17 * * * docker exec -it crw-discord-bot python3 /wordlebot/bin/backend_handler.py daily_ranks >/dev/null 2>&1
# Wordle Summary (Mon - Sat)
0 9 * * 1-6 docker exec -it crw-discord-bot python3 /wordlebot/bin/backend_handler.py daily_summary >/dev/null 2>&1
# Wordle Summary (Sun)
0 9 * * 0 docker exec -it crw-discord-bot python3 /wordlebot/bin/backend_handler.py weekly_summary >/dev/null 2>&1
```
