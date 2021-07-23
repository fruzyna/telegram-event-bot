import telebot
from datetime import datetime, timedelta
from time import sleep

# generic event bot, used for notifying of upcoming events within 30 minutes before
class EventBot:

    # create the bot, requires a Telegram bot token and some descriptive information
    def __init__(self, token, name, description, groupType, eventType):
        self.tb = telebot.TeleBot(token)
        self.name = name
        self.description = description
        self.groupType = groupType
        self.eventType = eventType
        self.events = []

    # update the list of available events
    def update_events(self, events):
        self.events = events

    # build a message
    def build_msg(self, event):
        return "[{}] {} @ {} on {}".format(event['group'], event['event'], str(event['datetime']), event['channel'])

    # thread to check for upcoming events 10-15 minutes before hand
    # then posts to the passed in channel
    # can be filtered by event group so that individual channels can be created for each group 
    def update_thread(self, channel, group=''):
        while True:
            now = datetime.now()
            
            for event in self.events:
                if event['datetime'] > now + timedelta(minutes=10) and event['datetime'] < now + timedelta(minutes=15) \
                    and (not group or event['group'].upper() == group.upper()):
                    self.tb.send_message(channel, self.build_msg(event))

            # run every 5 minutes
            sleep(60 * 5)

    # poll so that incoming direct messages can be received
    def listen(self):
        self.tb.polling()

    # responds to next event messages
    # messages can have a group and number of events to list
    def next_msg(self, msg):
        # process arguments
        text = msg.text.strip()
        group = ''
        count = 1
        words = text.split(' ')
        if len(words) == 3:
            group = words[1].upper()
            if words[2].isnumeric():
                count = int(words[2])
        elif len(words) == 2:
            if words[1].isnumeric():
                count = int(words[1])
            else:
                group = words[1].upper()

        # filter events
        selected = filter(lambda event: event['datetime'] > datetime.now() and (not group or event['group'] == group), self.events)
        selected = list(selected)[:count]

        # build and send message
        toSend = ''
        for i, game in enumerate(selected):
            if i > 0:
                toSend += '\n'
            toSend += self.build_msg(game)
        if len(selected) == 0:
            toSend = "No {} {}s found".format(group, self.eventType)

        self.tb.reply_to(msg, toSend)

    # responds to server time message with current time
    def time_msg(self, msg):
            self.tb.reply_to(msg, "Bot time: {}".format(str(datetime.now())))

    # respond to about message with bot description
    def about_msg(self, msg):
            self.tb.reply_to(msg, "{} is a Telegram bot by Liam Fruzyna. {}. Type /help for commands.".format(self.name, self.description))

    # respond to help message with help text
    def help_msg(self, msg):
            self.tb.reply_to(msg, "/next [{}] [count] - next {}\n/time - bot's time\n/about - info about bot\n/help - this help text".format(self.groupType, self.eventType))

    # respond to any other messages with an error message
    def default_msg(self, msg):
        self.tb.reply_to(msg, "Sorry, I don't understand \"{}\"".format(msg.text))