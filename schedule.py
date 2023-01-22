from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re


# flatten a list of lists
def flatten(l):
    return [item for sublist in l for item in sublist]


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
                    game = cells[1].text

                    # determine TV channel if string
                    chans = []
                    if cells[3].string:
                        chans.append(cells[3].string)

                    # determine TV channel from image
                    classes = []
                    classes = flatten([i['class'] for i in cells[3].find_all(['figure', 'img'])])
                    classes = list(filter(lambda c: c.startswith('network-'), classes))

                    if classes:
                        if 'network-abc' in classes:
                            chans.append('ABC')
                        if 'network-espn+' in classes:
                            chans.append('ESPN+')
                        if 'network-espn' in classes:
                            chans.append('ESPN')
                        if 'network-hulu' in classes:
                            chans.append('Hulu')

                    if chans:
                        tv = ', '.join(chans)
                    else:
                        tv = 'Local'

                    # combine into EventBot compatible dictionary
                    games.append({
                        'group': label,
                        'event': game,
                        'datetime': dt,
                        'channel': tv
                    })

    return games


# processes schedules from ESPN.com
def process_espn_racing(url, label):
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

                tv = cells[2].string
                if tv is None:
                    tv = 'Unknown'

                # combine into EventBot compatible dictionary
                races.append({
                    'group': label,
                    'event': race,
                    'datetime': dt,
                    'channel': tv
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

            tv = cells[3].string
            if tv is None:
                tv = 'ESPN?'

            # combine into EventBot compatible dictionary
            races.append({
                'group': label,
                'event': race,
                'datetime': dt,
                'channel': tv
            })

    return races


# processes schedules from IMSA
def process_imsa(url, label):
    races = []

    # get rows of table
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"})
    page = urlopen(req)
    html = page.read().decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.find_all("div", class_="rich-text-component-container")
    rows.pop(0)

    for row in rows:
        name = row.find('a', class_='onTv-event-title').string.strip()
        name = name.replace(' (Only Available To Stream In The United States On Peacock Premium)', '')
        name = name.replace(' (Available Globally)', '')
        date = row.find("span", class_='date-display-single').string.split(' -')[0]
        dt = datetime.strptime(date, '%A, %B %d, %Y – %I:%M %p')
        dt = dt - timedelta(hours=1)

        # determine TV channel by image
        tvimg = row.img['src'].upper()
        tv = 'IMSA TV'
        if 'TRACKPASS' in tvimg:
            tv = 'TrackPass'
        elif 'PEACOCK' in tvimg:
            tv = 'Peacock'
        elif 'NBC' in tvimg:
            tv = 'NBC'
        elif 'USA' in tvimg:
            tv = 'USA'

        # combine into EventBot compatible dictionary
        # if not qualifying
        #if "QUALIFYING" not in name.upper():
        # hide second day broadcasts starting at midnight eastern
        if dt.hour != 23 or dt.minute != 0:
            races.append({
                'group': label,
                'event': name,
                'datetime': dt,
                'channel': tv
            })

    # remove duplicate listings
    remove = []
    for i in range(len(races)):
        if i + 1 < len(races):
            if abs(races[i]['datetime'] - races[i+1]['datetime']) < timedelta(minutes=30) and races[i]['group'] == races[i+1]['group']:
                remove.append(i)
                races[i+1]['channel'] = f"{races[i]['channel']}, {races[i+1]['channel']}"

    for i in sorted(remove, reverse=True):
        del races[i]

    return races


# processes schedules from IndyCar
def process_indy(url, label):
    races = []

    # get rows of table
    page = urlopen(url)
    html = page.read().decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")
    items = soup.find_all("li", class_="schedule-list__item")

    for item in items:
        name = item.find('a', class_='schedule-list__title').span.string.strip()
        date = item.find("div", class_='schedule-list__date')
        month = date.contents[0].strip()
        day = date.find('span', class_='schedule-list__date-day').string.strip()
        time = item.find('span', class_='timeEst').string.replace('ET', '').strip()
        # use noon if time is not yet set
        if time == 'TBD':
            dt = datetime.strptime(f"{month} {day} {datetime.now().year} 12:00 PM", '%b %d %Y %I:%M %p')
        else:
            dt = datetime.strptime(f"{month} {day} {datetime.now().year} {time}", '%b %d %Y %I:%M %p')
            dt = dt - timedelta(hours=1)

        # determine TV channel by image
        tvimg = item.find("div", class_='schedule-list__broadcast').a['href'].upper()
        tv = 'PEAKCOCK'
        if 'PEACOCKTV' in tvimg:
            tv = 'Peacock'
        elif 'NBCSPORTS' in tvimg:
            tv = 'NBC'
        elif 'USANETWORK' in tvimg:
            tv = 'USA'

        # combine into EventBot compatible dictionary
        races.append({
            'group': label,
            'event': name,
            'datetime': dt,
            'channel': tv
        })

    return races
