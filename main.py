from pyscript import when
from js import videojs, document, XMLHttpRequest
from io import StringIO
from pyodide.http import open_url
from bs4 import BeautifulSoup as bs
import datetime
import re
import json


def debug(message, level):
    debug_div = document.getElementById("debug_div")
    debug_message = document.createElement("p")
    debug_message.setAttribute("class", f"debug {level}")
    debug_message.innerText = message
    debug_div.appendChild(debug_message)


def get_times():
    utcnow = datetime.datetime.utcnow()
    us_east_time = (utcnow - datetime.timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S")
    gr_time = (utcnow + datetime.timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
    debug(f"Time in Eastern US (as of page load): {us_east_time}", "info")
    debug(f"Time in Greece (as of page load): {gr_time}", "info")


@when("click", "#skaiButton")
def play_skai():
    player = videojs("ptv-player")
    player.src("https://skai-live-back.siliconweb.com/media/cambria4/index.m3u8")
    player.play()


@when("click", "#skaiNews")
def play_skai_news():
    player = videojs("ptv-player")
    videoSrc = parse_skai_news()
    player.src(videoSrc)
    player.play()


def parse_skai_news():
    date_string = datetime.date.today().strftime("%Y-%m-%d-14")
    news_page = open_url(
        "https://www.skaitv.gr/show/enimerosi/oi-eidiseis-tou-ska-stis-2/sezon-2023-2024"
    )
    news_page_soup = bs(news_page.read(), "html.parser")
    news_page_links = news_page_soup.find_all("a", class_="resio", href=True)
    try:
        episode_page = get_episode_page(
            news_page_links=news_page_links, date_string=date_string
        )
    except IndexError:
        debug(
            f"Error: Today's news link does not exist yet. Falling back to previous day.",
            "Error",
        )
        previous_day = (datetime.date.today() - datetime.timedelta(days=1)).strftime(
            "%Y-%m-%d-14"
        )
        try:
            episode_page = get_episode_page(
                news_page_links=news_page_links, date_string=previous_day
            )
        except IndexError:
            debug(
                f"Error: No links found for previous day, please raise a github issue",
                "Error",
            )
    episode_page_link = f"https://www.skaitv.gr{episode_page}"
    episode_playlist_link = parse_episode_page(episode_page_url=episode_page_link)
    debug(f"News Episode Link: {episode_playlist_link}", "info")
    return episode_playlist_link


def get_episode_page(news_page_links, date_string):
    episode_page = [
        _link["href"]
        for _link in news_page_links
        if _link["href"].endswith(date_string)
    ][0]
    return episode_page


def parse_episode_page(episode_page_url):
    episode_page = open_url(episode_page_url)
    episode_soup = bs(episode_page.read(), "html.parser")
    episode_page_html = str(episode_soup.html())
    episode_javascript_blob = re.search(r"var data = ({.+})", episode_page_html).group(
        1
    )
    episode_json = json.loads(episode_javascript_blob)
    try:
        media_item = episode_json["episode"][0]["media_item_file"]
        playlist_link = f"https://videostream.skai.gr/skaivod/_definst_/mp4:skai/{media_item}/chunklist.m3u8"
        return playlist_link
    except KeyError:
        debug("Error: Media Item File not found", "Error")


debug("Begin debug window:", "info")
player = videojs("ptv-player")
get_times()
