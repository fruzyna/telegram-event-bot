import telebot, logging
from datetime import datetime, timedelta, date, time as dtime
from time import sleep, time
from sched import scheduler

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
        logging.info('Updating events')
        self.events = events

    # build a message
    def build_msg(self, event):
        return "[{}] {} @ {} on {}".format(event['group'], event['event'], str(event['datetime']), event['channel'])

    # schedules alerts for upcoming events 10 minutes before hand
    # then posts to the passed in channel
    # can be filtered by event group so that individual channels can be created for each group 
    def schedule_alerts(self, channel, group=''):
        logging.info('Scheduling alerts')
        now = datetime.now()
        

        
        s = scheduler(time, sleep)
        for event in self.events:
            dt = event['datetime']
            if dt > now and dt < now + timedelta(hours=24) \
                and (not group or event['group'].upper() == group.upper()):
                msg = self.build_msg(event)
                in_secs = (dt - timedelta(minutes=10) - now).total_seconds()
                logging.info(f"Scheduling '{msg}' for {in_secs} secs from now")
                s.enter(in_secs, 1, self.tb.send_message, (channel, msg))

        # on Friday schedule weekend update at noon
        if now.weekday() == 4:
            in_secs = (datetime.combine(date.today(), dtime(hour=10, minute=59)) - now).total_seconds()
            logging.info(f"Scheduling weekend update for {in_secs} secs from now")
            s.enter(in_secs, 1, self.weekend_update, [channel])

        s.run()

    # poll so that incoming direct messages can be received
    def listen(self):
        try:
            logging.info('Polling')
            self.tb.polling()
        except KeyboardInterrupt:
            logging.info('Keyboard interrupt')
            return
        except Exception as e:
            logging.info('Exception, restarting', e)
            self.listen()

    # process arguments for next and last commands
    def process_args(self, msg):
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
        return group, count

    # builds and send weekend update message
    def weekend_update(self, channel):
        # filter events
        today = date.today()
        monday = datetime.combine(today + timedelta((7 - today.weekday()) % 7), datetime.min.time())
        selected = filter(lambda event: event['datetime'] > datetime.now() and event['datetime'] < monday, self.events)

        msgs = ['Weekend Update:']
        for event in selected:
            msgs.append(self.build_msg(event))

        # build and send message
        try:
            self.tb.send_message(channel, '\n'.join(msgs))
        except:
            pass

    # responds to next event messages
    # messages can have a group and number of events to list
    def next_msg(self, msg):
        group, count = self.process_args(msg)

        # filter events
        selected = filter(lambda event: event['datetime'] > datetime.now() and (not group or event['group'] == group), self.events)
        selected = list(selected)[:count]

        # build and send message
        self.send_message(selected, group, msg)

    # responds to last event messages
    # messages can have a group and number of events to list
    def last_msg(self, msg):
        group, count = self.process_args(msg)

        # filter events
        selected = filter(lambda event: event['datetime'] < datetime.now() and (not group or event['group'] == group), self.events)
        selected = list(selected)[-count:]

        # build and send message
        self.send_message(selected, group, msg)


    # send a message containing several events
    def send_message(self, selected, group, msg):
        toSend = ''
        for i, game in enumerate(selected):
            if i > 0:
                toSend += '\n'
            toSend += self.build_msg(game)
        if len(selected) == 0:
            toSend = "No {} {}s found".format(group, self.eventType)

        try:
            self.tb.reply_to(msg, toSend)
        except Exception as e:
            if len(toSend) > 4096:
                self.tb.reply_to(msg, 'Response too long, try fewer events')
            else:
                self.tb.reply_to(msg, f'Unknown error sending message\n{e}')

    # responds to server time message with current time
    def time_msg(self, msg):
            self.tb.reply_to(msg, 'Bot time: {}'.format(str(datetime.now())))

    # respond to about message with bot description
    def about_msg(self, msg):
            self.tb.reply_to(msg, "{} is a Telegram bot by Liam Fruzyna. {}. Type /help for commands.".format(self.name, self.description))

    # respond to help message with help text
    def help_msg(self, msg):
            self.tb.reply_to(msg, "/next [{}] [count] - next {}\n/time - bot's time\n/about - info about bot\n/help - this help text\n/groups - list teams/sports available".format(self.groupType, self.eventType))

    # respond to groups message with list of groups
    def groups_msg(self, msg):
            print([event['group'] for event in self.events])
            self.tb.reply_to(msg, "Groups:\n{}".format('\n'.join(list(set([event['group'] for event in self.events])))))

    # respond to any other messages with an error message
    def default_msg(self, msg):
        self.tb.reply_to(msg, "Sorry, I don't understand \"{}\"".format(msg.text))