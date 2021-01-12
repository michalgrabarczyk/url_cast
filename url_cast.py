import pychromecast
import pychromecast.controllers.dashcast as dashcast
import time
import datetime as dt
from datetime import timedelta
from dateutil import tz
from suntime import Sun

latitude = 47.48
longitude = 7.73

app_id_chromecast_screensaver = 'E8C28D3C'
app_id_dashcast = '84912283'


def kill_cast(cast):
    cast.quit_app()
    t = 5
    while cast.status.app_id is not None and t > 0:
        time.sleep(0.1)
        t = t - 0.1


def is_casting_dashcast(cast):
    return cast.app_id == app_id_dashcast


def is_casting_screensaver(cast):
    return cast.app_id == app_id_chromecast_screensaver


def is_casting(cast):
    return not cast.is_idle or not is_casting_screensaver(cast)


def cast_url(dashcast, url):
    # load_url apparently has to be called twice
    # first run launches dashcast, second actually loads url
    dashcast.load_url(url)
    time.sleep(1)
    dashcast.load_url(url, force = True)

    
def stop_casting_datetime():
    sun = Sun(latitude, longitude)
    today_lss = sun.get_local_sunset_time()
    stop_casting_at = today_lss - timedelta(hours=1) # stop casting an hour before sunset
    return stop_casting_at

    
def start_casting_datetime():
    sun = Sun(latitude, longitude)
    today_lsr = sun.get_local_sunrise_time()
    start_casting_at = today_lsr + timedelta(hours=1) # start casting an hour after sunrise
    return start_casting_at


def sleep_if_no_casting_time(cast):
    now = dt.datetime.now(tz.tzlocal())
    current_hour = dt.datetime.now().hour # 24h format
    if (now >= stop_casting_datetime()):
        if is_casting(cast):
            kill_cast(cast)
        time_to_wakeup = start_casting_datetime() + timedelta(days=1) - now
        print ('Next cast at {}'.format(dt.datetime.now() + time_to_wakeup))
        time.sleep(time_to_wakeup.total_seconds())


def try_to_cast_url(cast, dashcast, url):
    if is_casting_screensaver(cast) or cast.app_id == app_id_dashcast:
        if is_casting_dashcast(cast):
            kill_cast(cast)
        cast_url(dashcast, url)


def cast_urls_in_loop(cast, dashcast, urls):
    while (True):
        for url, seconds_to_change in urls.items():
            sleep_if_no_casting_time(cast)
            try_to_cast_url(cast, dashcast, url)
            time.sleep(seconds_to_change)

casts = pychromecast.get_chromecasts()
if len(casts) == 0:
    print("No Chromecasts found")
    exit()

cast = casts[0]
print('Found Chromecast: {} on {}:{}'.format(cast.name, cast.host, cast.port))

cast.wait()
d = dashcast.DashCastController()
cast.register_handler(d)

print()
print(cast.status)
print()

url_windy_temp = "https://www.windy.com/-Temperature-temp?temp,47.439,8.297,5"
url_windy_rain = "https://www.windy.com/-Rain-thunder-rain?rain,47.439,8.297,5"
url_domoticz_dashboard = "http://192.168.0.101:8080/#/Dashboard"
url_coinmarketcap = "https://coinmarketcap.com/"

secs_per_url_map = {
    url_windy_rain: 300,
    url_windy_temp: 100,
    url_domoticz_dashboard: 30,
    url_coinmarketcap: 30
    }

cast_urls_in_loop(cast, d, secs_per_url_map)

