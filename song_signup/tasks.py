import dataclasses
import os
import re
from logging import getLogger
from typing import Iterable, Optional

import bs4
import requests
import sherlock
from celery import shared_task
from redis import Redis

from .models import GroupSongRequest, SongLyrics, SongRequest

logger = getLogger(__name__)

GENIUS_URL_FORMAT = re.compile("genius\.com\/.*-lyrics$")
USER_AGENT = "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36"
SEARCH_MKT = "en-US"

bing_endpoint = os.environ["BING_ENDPOINT"]
bing_key = os.environ["BING_KEY"]

# Lock for throttling requests to the same site. Will only be acquired, not released, and then let to expire.
sherlock.configure(
    backend=sherlock.backends.REDIS, expire=1, client=Redis(host="redis")
)


@dataclasses.dataclass
class LyricsResult:
    lyrics: str
    title: str
    artist: str
    url: str | None


class LyricsWebsiteParser:
    URL_FORMAT = re.compile("")
    SITE = ""

    def bing_api(self, query):
        params = {"q": query, "mkt": SEARCH_MKT, "responseFilter": "Webpages"}
        headers = {"Ocp-Apim-Subscription-Key": bing_key}
        res = requests.get(bing_endpoint, headers=headers, params=params)
        return res.json()["webPages"]["value"]

    def fix_url(self, url):
        # Perform any necessary fixups on URL before requesting
        return url

    def parse_lyrics(self, soup: bs4.BeautifulSoup) -> Optional[LyricsResult]:
        return None

    def get_lyrics(self, song_name: str, author: str) -> Iterable[LyricsResult]:
        lock = sherlock.Lock(self.SITE)
        seen_urls = set()
        search_query = "{} lyrics {} site:{}".format(song_name, author, self.SITE)

        for _ in range(3):
            search_results = self.bing_api(search_query)
            if len(search_results) > 0:
                break
            logger.info("No search results, retrying")

        for search_result in search_results:
            url = self.fix_url(search_result["url"])

            if url in seen_urls:
                continue
            seen_urls.add(url)

            if not self.URL_FORMAT.search(url):
                continue

            lock.acquire()  # Expires on its own after an interval (for throttling)
            logger.info(f"Performing query on {url}")
            r = requests.get(url, headers={"User-Agent": USER_AGENT})

            if not r.status_code == 200:
                logger.warning(f"Received status {r.status_code} for URL {url}")
                continue

            soup = bs4.BeautifulSoup(r.content.decode(), features="html.parser")

            try:
                result = self.parse_lyrics(soup)

                if not result:
                    logger.warning(
                        f"Unable to parse search result {search_result['url']}"
                    )
                    # Something is broken in the parser, let's skip it
                    break

                result.url = url
                yield result
            except Exception as e:
                # Skip exceptions in individual parsers
                logger.exception(f"Exception in parser for url {search_result['url']}")


class GenuisParser(LyricsWebsiteParser):
    URL_FORMAT = re.compile("genius\.com\/.*-lyrics$")
    SITE = "genius.com"

    def fix_url(self, url):
        # Common URLs that are close enough that we can just fixup
        return url.removesuffix("/q/writer").removesuffix("/q/producer")

    def parse_lyrics(self, soup: bs4.BeautifulSoup) -> LyricsResult:
        page_title = soup.find("title").text
        artist, title = page_title.split("–")[
            :2
        ]  # Note that this is a unicode character
        artist = artist.strip()
        if "Lyrics" in title:
            title = title[: title.index("Lyrics")]
        title = title.strip()

        for br in soup.find_all("br"):
            br.replace_with("\n")

        return LyricsResult(
            lyrics="\n\n".join(
                verse.get_text()
                for verse in soup.findAll("div", {"data-lyrics-container": "true"})
            ),
            artist=artist,
            title=title,
            url=None,
        )


class AllMusicalsParser(LyricsWebsiteParser):
    URL_FORMAT = re.compile("allmusicals\.com\/lyrics\/.*\.htm$")
    SITE = "allmusicals.com"

    def parse_lyrics(self, soup: bs4.BeautifulSoup) -> LyricsResult:
        page_title = soup.find("title").text
        title, artist = page_title.split("-")[:2]

        if "Lyrics" in title:
            title = title[: title.index("Lyrics")]
        title = title.strip()
        artist = artist.strip()

        for element in soup.find_all(attrs={"class": "muted"}):
            element.replace_with("")

        for element in soup.find_all(attrs={"class": "visible-print"}):
            element.replace_with("")

        return LyricsResult(
            lyrics=soup.find("div", {"class": "main-text"}).text.strip(),
            artist=artist,
            title=title,
            url=None,
        )


class AzLyricsParser(LyricsWebsiteParser):
    URL_FORMAT = re.compile("azlyrics.com\/lyrics\/.*html$")
    SITE = "azlyrics.com"

    def parse_lyrics(self, soup: bs4.BeautifulSoup) -> Optional[LyricsResult]:
        page_title = soup.find("title").text
        artist, title = page_title.split("-")[:2]

        if "Lyrics" in title:
            title = title[: title.index("Lyrics")]
        title = title.strip()
        artist = artist.strip()

        if "request for access" in title:
            # Oops we're blocked, need to find workaround later :(
            return None

        for br in soup.find_all("br"):
            br.replace_with("\n")

        return LyricsResult(
            lyrics=max(soup.findAll("div", {"class": None}), key=len).text.strip(),
            artist=artist,
            title=title,
            url=None,
        )


class TheMusicalLyricsParser(LyricsWebsiteParser):
    URL_FORMAT = re.compile("themusicallyrics\.com\/.*\/.*-lyrics\/.*-lyrics\.html$")
    SITE = "themusicallyrics.com"

    def fix_url(self, url):
        # Something is broken with the SSL cert on this site when using
        # requests (but not when using browser). For now just use http
        return url.replace("https://", "http://")

    def parse_lyrics(self, soup: bs4.BeautifulSoup) -> LyricsResult:
        page_title = soup.find("title").text
        artist, title = page_title.split("-")[:2]

        if "Lyrics" in title:
            title = title[: title.index("Lyrics")]
        title = title.strip()
        artist = artist.strip()

        for br in soup.find_all("br"):
            br.replace_with("\n")

        # Remove extra title
        for tag in soup.find_all("strong"):
            tag.replace_with("")

        return LyricsResult(
            lyrics=soup.find_all("p")[1].text.strip(),
            artist=artist,
            title=title,
            url=None,
        )


class LyricsTranslateParser(LyricsWebsiteParser):
    URL_FORMAT = re.compile("-lyrics\.html$")
    SITE = "lyricstranslate.com"

    def parse_lyrics(self, soup: bs4.BeautifulSoup) -> LyricsResult:
        page_title = soup.find("title").text
        artist, title = page_title.split("-")[:2]

        if "[" in title:
            title = title[: title.index("[")]

        if "lyrics" in title:
            title = title[: title.index("lyrics")]
        title = title.strip()
        artist = artist.strip()

        for br in soup.find_all("br"):
            br.replace_with("\n")

        return LyricsResult(
            lyrics="\n\n".join(
                verse.get_text() for verse in soup.find_all("div", {"class": "par"})
            ),
            artist=artist,
            title=title,
            url=None,
        )


class ShironetParser(LyricsWebsiteParser):
    URL_FORMAT = re.compile("type=lyrics")
    SITE = "shironet.mako.co.il"

    def parse_lyrics(self, soup: bs4.BeautifulSoup) -> LyricsResult:
        artist = ""
        title = ""

        title_tag = soup.find("h1", {"class": "artist_song_name_txt"})
        if title_tag:
            title = title_tag.text.strip()
        artist_tag = soup.find("a", {"class": "artist_singer_title"})
        if artist_tag:
            artist = artist_tag.text.strip()

        for br in soup.find_all("br"):
            br.replace_with("\n")

        return LyricsResult(
            lyrics=soup.find("span", {"itemprop": "Lyrics"}).text.strip(),
            artist=artist,
            title=title,
            url=None,
        )


PARSERS = {parser.__name__: parser for parser in LyricsWebsiteParser.__subclasses__()}


@shared_task
def get_lyrics(song_id: int | None = None, group_song_id: int | None = None):
    if song_id is not None:
        assert group_song_id is None
        song = SongRequest.objects.get(id=song_id)

        # Delete old lyrics
        SongLyrics.objects.filter(song_request=song).delete()
    else:
        assert group_song_id is not None
        song = GroupSongRequest.objects.get(id=group_song_id)

        # Delete old lyrics
        SongLyrics.objects.filter(group_song_request=song).delete()

    for parser_name in PARSERS:
        get_lyrics_for_provider.delay(parser_name, song_id, group_song_id)


@shared_task(rate_limit="0.5/s")
def get_lyrics_for_provider(
    parser_name: str, song_id: int | None, group_song_id: int | None
):
    parser = PARSERS[parser_name]

    if song_id is not None:
        assert group_song_id is None
        song = SongRequest.objects.get(id=song_id)
    else:
        assert group_song_id is not None
        song = GroupSongRequest.objects.get(id=group_song_id)

    for i, result in enumerate(parser().get_lyrics(song.song_name, song.musical)):
        SongLyrics.objects.create(
            song_name=result.title,
            artist_name=result.artist,
            url=result.url,
            lyrics=result.lyrics,
            song_request=song if song_id is not None else None,
            group_song_request=song if group_song_id is not None else None,
        )

        # 2 lyrics per site is plenty for now
        if i == 1:
            break
