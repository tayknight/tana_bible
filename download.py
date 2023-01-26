import json
import time
import urllib3
import requests
import traceback

from pathlib import Path
from urllib3 import Retry

import pythonbible as bible

from bs4 import BeautifulSoup, NavigableString, Tag, ResultSet
from requests.adapters import HTTPAdapter, Retry
from tqdm import tqdm

if __name__ == '__main__':
    with open(Path("config.json"), "r") as f:
        config = json.loads(f.read())

    # Most Bible versions are copywritten. You should comply with the Copyright
    # notice on the version's page on Bible Gateway. 

    # Bible Gateway has a page that lists available books and chapters in 
    # those books. Parse this page instead of hardcoding books and number
    # of chapters. 
    # The human_name entry in config.json file needs to exactly match the
    # URL entry for a version listed on https://www.biblegateway.com/versions/.
    # The version needs to match the version abbreviation.
    # For instance, for the English Standard version the URL is:
    #   https://www.biblegateway.com/versions/English-Standard-Version-ESV-Bible/#booklist
    # human_name needs to be "English-Standard-Version"
    # translation needs to be "ESV".

    # TODO, Figure out how to include the apocrapha.
    # This script relies on pythonbible. Several apocrapha aren't consistent between biblegateway
    # and pythonbible. Thus, the script will only download books in the Protestant canon (for which
    # pythonbible is well covered).

    book_url = "https://www.biblegateway.com/versions/{human_name}-{version}-Bible/#booklist".format(
        human_name=config["human_name"],
        version=config["version"]
    )

    s = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[ 502, 503, 504 ])
    s.mount('http://', HTTPAdapter(max_retries=retries))
    s.mount('https://', HTTPAdapter(max_retries=retries))

    book_info = {
        "version": config["version"],
        "books": []
    }

    try:
        resp = s.get(book_url)
        soup = BeautifulSoup(resp.text, "html.parser")
        stop = False

        for row in tqdm(soup.find("table", {"class", "chapterlinks"}).find_all("tr"), unit="Book"):
            count = 1
            ref = None
            links = row.find_all("a")

            # See notes about apocrypha.
            if stop:
                break
            try:
                found = {}
                skip = False
                for link in links:
                    if stop:
                        break
                    if not skip:
                        # Try to turn the href title into a book-chaper reference
                        ref = bible.get_references(link.attrs["title"])
                        if ref:
                            # Only get the book of the Protestant canon (Genesis as 1 through Revelation as 66)
                            if 1 <= ref[0].book.value <= 66:
                                if bible.get_book_titles(ref[0].book):
                                    title = bible.get_book_titles(ref[0].book).short_title
                            else:
                                tqdm.write("Skipping {}.".format(link.attrs["title"]))
                                skip = True
                                # Stop fetching books.
                                stop = True
                                continue
                        else:
                            tqdm.write("Couldn't get pythonbible ref for {}.".format(link.attrs["title"]))
                            skip = True
                            continue
                        
                        # Download the html
                        chapter_path = path = "https://www.biblegateway.com/passage/?search={title}%20{chapter}&version={version}&interface=print".format(
                            title=title,
                            chapter=count,
                            version=config["version"]
                        )

                        r = s.get(path)
                        chapter_path = output_path = Path("books", "input", config["version"], "html")
                        chapter_path.mkdir(parents=True, exist_ok=True)



                        # with open(Path(chapter_path, "{}-{}.html".format(
                        #     title,
                        #     count
                        # )), "wb") as f:
                        #     for chunk in r.iter_content(chunk_size=128):
                        #         f.write(chunk)
                        passage_soup = BeautifulSoup(r.text, "html.parser")
                        passage = passage_soup.find(class_="passage-col")

                        with open(Path(chapter_path, "{}-{}.html".format(
                            title,
                            count
                        )), "w", encoding='utf-8') as f:
                            f.write(str(passage))
                    
                    count = count + 1
                if not stop:
                    found = {
                        "name": title,
                        "chapters": count - 1
                    }
                    book_info["books"].append(found)
            except bible.errors.InvalidChapterError as e:
                tqdm.write("WARNING: " + str(e))
                continue

        output_path = Path("books", "input", config["version"])
        output_path.mkdir(parents=True, exist_ok=True)
        with open(Path(output_path, "chapters_{}.json".format(config["version"])), "w") as f:
            f.write(json.dumps(book_info, indent=4))
        
    except Exception as e:
        traceback.print_exc()
