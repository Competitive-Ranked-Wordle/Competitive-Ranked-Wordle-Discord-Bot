# Discord Wordle Bot

A simple Discord bot that facilitates gameplay of [Competitive Ranked Wordle](https://github.com/jivandabeast/Competitive-Ranked-Wordle/tree/master)

## Commands and Features

1. Automatically parse Wordle submissions in the #general channel

2. `!register [Display Name]`: Registers a user to be included in the game, this is a **required** step in order to play Competitive Ranked Wordle.

3. `!update [Display Name]`: Updates a user's display name, in the event that they want to change it

4. `!score [Puzzle] [Player Username?]`: Displays a user's Wordle submission for a given day, if a user is not specified it will display the score of the requestor

5. `!blame [Puzzle] [Player Username?]`: Displays a user's ELO gain/loss for a given Puzzle, this can be done even before the calculations are run for a given day (to provide an estimate of how their ELO will change). If a user is not specified, it will output for the requestor.

## Setup

### Prerequisites

- Discord Bot Account/Token

  I will not go into detail on how to get one of these, but you can do it through the [Discord Developer Portal](https://discord.com/developers/applications)

- An instance of the CRW backend server (and an account to match)

  More information on running one of these available [here](https://github.com/Competitive-Ranked-Wordle/Competitive-Ranked-Wordle)

### Docker

1. Create a folder for the resources & create required files

```
$ mkdir /docker/crw-discord-bot
$ wget https://raw.githubusercontent.com/jivandabeast/Competitive-Ranked-Wordle-Discord-Bot/refs/heads/master/config.yml.sample
$ mv config.yml.sample config.yml
```

2. Edit `config.yml` with all the required data

3. Execute the docker image

`docker run -d --name crw-discord-bot -v /docker/crw-discord-bot:/data -e CONFIG_FILE=/data/config.yml jivandabeast/competitive-ranked-wordle-discord-bot:latest`

4. Log in to your Discord server, and register with `!register` to ensure that the bot has connected and is operational

## Wordle Schedule (Eastern)

- 12:01AM: Lock old spoiler thread and create a new one
- 12:30AM: Calculate rankings for the previous day
- 3:00AM: Update the leaderboard
- 9:00AM: Post the daily ratings (Mon - Sat), Weekly ratings (Sun)
- 5:00PM: Post the daily rankings

## Gameplay Rules

1. All games must be played in Hard Mode

   In order to be ranked you must be playing the game with "Hard Mode" enabled in your Wordle settings. If you make a submission without this enabled, you will be included in the daily ranking, however you will not have your ELO or OpenSkill rating updated.

2. Submit before 12:00AM Eastern to be ranked.

   In order to be included in the ranks for the day, you must submit your score before 11:00PM Eastern time to have your ELO and OpenSkill rating re-calculated. In order to be included in the daily ranking (non-competitive), you must submit before 5:00PM Eastern time.

3. Submit your score, and only your score

   In order to submit your score, simply paste what is copied to your clipboard when you click "Share" in the Wordle results page and send it in the #general channel. DO NOT ADD ANYTHING ELSE TO THIS MESSAGE
