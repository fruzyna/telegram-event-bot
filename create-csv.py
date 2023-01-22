from schedule import process_espn, process_espn_racing, process_espn_f1, process_imsa, process_indy


races = process_espn_racing("https://www.espn.com/racing/schedule", "NCS")
races += process_espn_racing("https://www.espn.com/racing/schedule/_/series/xfinity", "NXS")
races += process_espn_racing("https://www.espn.com/racing/schedule/_/series/camping", "NCWTS")
races += process_espn_racing("https://www.espn.com/racing/schedule/_/series/indycar", "INDY")
races += process_indy("https://www.indycar.com/INDYNXT/Schedule", "NXT")
races += process_espn_f1("https://www.espn.com/f1/schedule", "F1")
races += process_imsa("https://www.imsa.com/weathertech/tv-streaming-schedule/", "IMSA")
races += process_imsa("https://www.imsa.com/michelinpilotchallenge/tv-streaming-schedule/", "PILOT")
races.sort(key=lambda r: r['datetime'])

with open('races.csv', 'w') as f:
    f.write(f"Series, Event, Time, Channel\n")
    for race in races:
        f.write(f"{race['group']}, {race['event']}, {race['datetime']}, {race['channel']}\n")