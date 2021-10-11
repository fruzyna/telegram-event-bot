from bot import EventBot

from urllib.request import urlopen
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from threading import Thread
from time import sleep

# implementation of EventBot to track motorsport schedules from ESPN

MOTOR_CHANNEL = -0
TOKEN = ""

# processes schedules from ESPN.com
def process_espn(url, label):
    races = []

    # get rows of table
    page = urlopen(url)
    html = page.read().decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.table.find_all("tr")
    rows.pop(0)

    for row in rows:
        cells = row.find_all("td")
        if len(cells) >= 4:
            # combine date and time, then interpret
            date = ''
            for s in cells[0].strings:
                if date:
                    date += ' '
                date += s
            date = date.replace('Noon', '12:00 PM')
            if date != 'DATE':
                dt = datetime.strptime(date, '%a, %b %d %I:%M %p ET')

                # use track as race name
                race = ''
                for s in cells[1].strings:
                    if not race:
                        race = s
                    # interpret postponed dates
                    elif s.startswith("**Race postponed to "):
                        date = s[s.index(' to ')+4:]
                        dt = datetime.strptime(date, '%B %d at %I:%M %p')
                
                # remove annoying extract cup series text
                if race.startswith('NASCAR') and ' at ' in race:
                    start = race.index(' at ') + 4
                    race = race[start:]
                elif race.startswith('NASCAR'):
                    start = race.upper().index('SERIES') + 7
                    race = race[start:]

                # add the current year and remove an hour for central time
                dt = dt.replace(year=datetime.now().year)
                dt = dt - timedelta(hours=1)

                # combine into EventBot compatible dictionary
                races.append({
                    'group': label,
                    'event': race,
                    'datetime': dt,
                    'channel': cells[2].string
                })

    return races

# while ESPN has an F1 schedule like NASCAR and Indy, there is a slightly better version
def process_espn_f1(url, label):
    races = []

    # get rows of table
    page = urlopen(url)
    html = page.read().decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.tbody.find_all("tr")
    rows.pop(0)

    for row in rows:
        cells = row.find_all("td")
        # interpret date time
        date = cells[2].string
        if " - " in date:
            dt = datetime.strptime(date, '%b %d - %I:%M %p')
            dt = dt.replace(year=datetime.now().year)
            dt = dt - timedelta(hours=1)

            # interpret race name
            race = ''
            for s in cells[1].strings:
                if not race:
                    race = s

            # combine into EventBot compatible dictionary
            races.append({
                'group': label,
                'event': race,
                'datetime': dt,
                'channel': cells[3].string
            })

    return races

# processes schedules from IMSA
def process_imsa(url, label):
    races = []

    # get rows of table
    page = urlopen(url)
    html = page.read().decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.find_all("div", class_="rich-text-component-container")
    rows.pop(0)

    for row in rows:
        name = row.find("a", class_="onTv-event-title").string
        date = row.find("span", class_="date-display-single").string.split(' -')[0]
        dt = datetime.strptime(date, '%A, %B %d, %Y – %I:%M %p')
        dt = dt - timedelta(hours=1)

        # determine TV channel by image
        tvimg = row.img['src'].upper()
        tv = 'IMSA TV'
        if 'TRACKPASS' in tvimg:
            tv = 'TrackPass'
        elif 'NBCSN' in tvimg:
            tv = 'NBCSN'
        elif 'NBC' in tvimg:
            tv = 'NBC'

        # combine into EventBot compatible dictionary
        # if not qualifying
        if "QUALIFYING" not in name.upper():
            races.append({
                'group': label,
                'event': name,
                'datetime': dt,
                'channel': tv
            })

    return races

# processes schedules from ENASCAR.com
def process_enascar(url, label):
    races = []

    # get rows of table
    page = urlopen(url)
    html = page.read().decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.find_all("div", class_='tableRowContainer', recursive=True)
    rows.pop(0)

    for row in rows:
        name = row.find('div', class_='trackCell').string
        watch = row.find('div', class_='watchCell').string

        # time only listed for upcoming events
        if 'on' in watch:
            parts = watch.split()
            date = '{0} {1}'.format(row.find('div', class_='dateCell').string, parts[0])
            dt = datetime.strptime(date, '%B %d, %Y %I%p')
            dt = dt - timedelta(hours=1)
            races.append({
                'group': label,
                'event': name,
                'datetime': dt,
                'channel': parts[-1]
            })

    return races

# create bot
bot = EventBot(TOKEN, "Motorsport Bot", "It sources NASCAR, IndyCar, and F1 schedules from ESPN.com", "series", "race")

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

# handle all other messages
@bot.tb.message_handler(func=lambda _: True)
def read_msg(msg):
    bot.default_msg(msg)

# thread to update list of races every day
def add_races(bot):
    while True:
        races = process_espn("https://www.espn.com/racing/schedule", "NCS")
        races += process_espn("https://www.espn.com/racing/schedule/_/series/xfinity", "NXS")
        races += process_espn("https://www.espn.com/racing/schedule/_/series/camping", "NCWTS")
        races += process_espn("https://www.espn.com/racing/schedule/_/series/indycar", "INDY")
        races += process_espn_f1("https://www.espn.com/f1/schedule", "F1")
        races += process_imsa("https://www.imsa.com/weathertech/tv-streaming-schedule/", "IMSA")
        races += process_enascar("https://www.enascar.com/schedule/", "ENAS")
        races.sort(key=lambda r: r['datetime'])
        bot.update_events(races)
        bot.schedule_alerts(MOTOR_CHANNEL)

        sleep(60 * 60 * 24)

# start all threads, give add_races a chance before other threads start
Thread(target=add_races, daemon=True, args=(bot,)).start()
sleep(10)

bot.listen()
