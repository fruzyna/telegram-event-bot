from bot import EventBot

from urllib.request import urlopen
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from threading import Thread
from time import sleep

# implementation of EventBot to track "stick and ball" sports schedules from ESPN

# define channels and bot token
CUBS_CHANNEL = -0
MUBB_CHANNEL = -0
BLKH_CHANNEL = -0
TOKEN = ""

# processes schedules from ESPN.com
def process_espn(url, label):
    games = []

    # get rows of table
    page = urlopen(url)
    html = page.read().decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")
    table = soup.table
    if table:
        rows = table.find_all("tr")
        rows.pop(0)

        for row in rows:
            cells = row.find_all("td")
            if cells and len(cells) >= 4:
                # combine date and time, then interpret
                date = cells[0].string
                for i, s in enumerate(cells[2].strings):
                    if i == 0:
                        date += ' {}'.format(s)
                if ':' in date:
                    dt = datetime.strptime(date, '%a, %b %d %I:%M %p')
                    # add the current year and remove an hour for central time
                    dt = dt.replace(year=datetime.now().year)
                    dt = dt - timedelta(hours=1)

                    # interpret opponent as game
                    game = ''
                    for i, s in enumerate(cells[1].strings):
                        if i == 0:
                            game = s
                        elif i == 2:
                            game += " {}".format(s)

                    # combine into EventBot compatible dictionary
                    games.append({
                        'group': label,
                        'event': game,
                        'datetime': dt,
                        'channel': '',
                    })

    return games

# create bot
bot = EventBot(TOKEN, "Stick and Ball Bot", "It sources Cubs, Blackhawks, and Marquette schedules from ESPN.com", "team", "game")

# handle /next
@bot.tb.message_handler(commands=['next'])
def read_msg(msg):
    bot.next_msg(msg)

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

# handle all other messages
@bot.tb.message_handler(func=lambda _: True)
def read_msg(msg):
    bot.default_msg(msg)

# thread to update list of games every day
def add_games(bot):
    while True:
        games = process_espn("https://www.espn.com/mlb/team/schedule/_/name/chc", "CUBS")
        games += process_espn("https://www.espn.com/nhl/team/schedule/_/name/chi", "BLKH")
        games += process_espn("https://www.espn.com/mens-college-basketball/team/schedule/_/id/269", "MUBB")
        games.sort(key=lambda r: r['datetime'])
        bot.update_events(games)

        sleep(60 * 60 * 24)

# start all threads, give add_games a chance before other threads start
Thread(target=add_games, args=(bot,)).start()
sleep(10)
Thread(target=bot.update_thread, args=(CUBS_CHANNEL, "CUBS")).start()
Thread(target=bot.update_thread, args=(MUBB_CHANNEL, "MUBB")).start()
Thread(target=bot.update_thread, args=(BLKH_CHANNEL, "BLKH")).start()

bot.listen()
