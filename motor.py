from bot import EventBot
from schedule import process_espn_racing, process_espn_f1, process_imsa

from threading import Thread
from time import sleep

import logging

# implementation of EventBot to track motorsport schedules

MOTOR_CHANNEL = -0
TOKEN = ""

# create bot
bot = EventBot(TOKEN, "Motorsport Bot", "It sources NASCAR, IndyCar, and F1 schedules from ESPN.com", "series", "race")

# handle /next
@bot.tb.message_handler(commands=['next'])
def read_msg(msg):
    logging.info('Got next message')
    bot.next_msg(msg)

# handle /last
@bot.tb.message_handler(commands=['last'])
def read_msg(msg):
    logging.info('Got last message')
    bot.last_msg(msg)

# handle /time
@bot.tb.message_handler(commands=['time'])
def read_msg(msg):
    logging.info('Got time message')
    bot.time_msg(msg)

# handle /about
@bot.tb.message_handler(commands=['about'])
def read_msg(msg):
    logging.info('Got about message')
    bot.about_msg(msg)

# handle /help
@bot.tb.message_handler(commands=['help'])
def read_msg(msg):
    logging.info('Got help message')
    bot.help_msg(msg)

# handle /groups
@bot.tb.message_handler(commands=['groups'])
def read_msg(msg):
    logging.info('Got groups message')
    bot.groups_msg(msg)

# handle all other messages
@bot.tb.message_handler(func=lambda _: True)
def read_msg(msg):
    logging.info('Got other message')
    bot.default_msg(msg)

# thread to update list of races every day
def add_races(bot):
    while True:
        try:
            logging.info('Fetching races')
            races = process_espn_racing("https://www.espn.com/racing/schedule", "NCS")
            races += process_espn_racing("https://www.espn.com/racing/schedule/_/series/xfinity", "NXS")
            races += process_espn_racing("https://www.espn.com/racing/schedule/_/series/camping", "NCWTS")
            races += process_espn_racing("https://www.espn.com/racing/schedule/_/series/indycar", "INDY")
            races += process_espn_f1("https://www.espn.com/f1/schedule", "F1")
            races += process_imsa("https://www.imsa.com/weathertech/tv-streaming-schedule/", "IMSA")
            races += process_imsa("https://www.imsa.com/michelinpilotchallenge/tv-streaming-schedule/", "PILOT")
            logging.info(f"Found {len(races)} races")
            races.sort(key=lambda r: r['datetime'])
            logging.info(str(races))
            bot.update_events(races)
            bot.schedule_alerts(MOTOR_CHANNEL)
            bot.schedule_weekend_update(MOTOR_CHANNEL)

            sleep(60 * 60 * 24)
        except Exception as e:
            logging.error('Error updating events')
            logging.error(e)

logging.basicConfig(filename='motorlog.txt',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

# start all threads, give add_races a chance before other threads start
Thread(target=add_races, daemon=True, args=(bot,)).start()
sleep(10)

bot.listen()
logging.info('Escaped listen')
