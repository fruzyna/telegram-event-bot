from bot import EventBot
from schedule import process_espn

from threading import Thread
from time import sleep

# implementation of EventBot to track "stick and ball" sports schedules from ESPN

# define channels and bot token
CUBS_CHANNEL = -0
RSOX_CHANNEL = -0 
MUBB_CHANNEL = -0
BLKH_CHANNEL = -0
TOKEN = ""

# flatten a list of lists
def flatten(l):
    return [item for sublist in l for item in sublist]

# create bot
bot = EventBot(TOKEN, "Stick and Ball Bot", "It sources Cubs, Red Sox, Blackhawks, and Marquette schedules from ESPN.com", "team", "game")

# handle /next
@bot.tb.message_handler(commands=['next'])
def read_msg(msg):
    bot.next_msg(msg)

# handle /last
@bot.tb.message_handler(commands=['last'])
def read_msg(msg):
    bot.last_msg(msg)

# handle /time
@bot.tb.message_handler(commands=['time'])
def read_msg(msg):
    bot.time_msg(msg)

# handle /about
@bot.tb.message_handler(commands=['about'])
def read_msg(msg):
    bot.about_msg(msg)

# handle /help
@bot.tb.message_handler(commands=['help'])
def read_msg(msg):
    bot.help_msg(msg)

# handle /groups
@bot.tb.message_handler(commands=['groups'])
def read_msg(msg):
    bot.groups_msg(msg)

# handle all other messages
@bot.tb.message_handler(func=lambda _: True)
def read_msg(msg):
    bot.default_msg(msg)

# thread to update list of games every day
def add_games(bot):
    while True:
        try:
            games = process_espn("https://www.espn.com/mlb/team/schedule/_/name/chc", "CUBS")
            games += process_espn("https://www.espn.com/mlb/team/schedule/_/name/bos", "RSOX")
            games += process_espn("https://www.espn.com/nhl/team/schedule/_/name/chi", "BLKH")
            games += process_espn("https://www.espn.com/mens-college-basketball/team/schedule/_/id/269", "MUBB")
            games.sort(key=lambda r: r['datetime'])
            bot.update_events(games)
            bot.schedule_alerts(CUBS_CHANNEL, "CUBS")
            bot.schedule_alerts(RSOX_CHANNEL, "RSOX")
            bot.schedule_alerts(MUBB_CHANNEL, "MUBB")
            bot.schedule_alerts(BLKH_CHANNEL, "BLKH")
            bot.schedule_weekend_update(CUBS_CHANNEL)

            sleep(60 * 60 * 24)
        except e:
            print('Error updating events')
            print(e)

# start all threads, give add_games a chance before other threads start
Thread(target=add_games, daemon=True, args=(bot,)).start()
sleep(10)

bot.listen()
