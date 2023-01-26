import json
import re

from pathlib import Path

import pythonbible as bible

from bs4 import BeautifulSoup, NavigableString, Tag, ResultSet
from tqdm import tqdm

class Book:
    def __init__ (self, name, version):
        self._b = self._get_book(name) 
        if self._b[0]:
            self.book = self._b[1].book
        else:
            self.book = None

        self.version = version
        self.verses = []
        self.short_title = self._get_short_title(name)
        self.chapters = self._get_chapters()
    
    def _get_chapters(self):
        if self._b:
            return self._b[1].end_chapter
        else:
            return 0

    def _get_book(self, name):
        ref = bible.get_references(name)
        if ref:
            return (True, ref[0])
        else:
            return (False, None)

    def _get_short_title(self, name):
        if self.book:
            t = bible.get_book_titles(self.book)
            if t:
                return t.short_title 
            else:
                return name
        else:
            return name
        
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)
    
class BookEncoder(json.JSONEncoder):
    def default(self, o):
        return o.__dict__

class Verse():
    """Verse object for bible verses
    """
    def __init__(self, verse_id, version, clsstr, text="", footnotes=None, crossrefs=None):
        # super().__init__(book, chapter, verse)
        # self.reference = reference
        self.verse_id = verse_id
        self.text = text
        self.version = version
        self.clsstr = clsstr
    
        # need to intantiate empty list here to prevent all Verse instances
        #  sharing a reference to a single list object.
        if footnotes is None:
            self.footnotes = []
        else:
            self.footnotes = footnotes

        if crossrefs is None:
            self.crossrefs = []
        else:
            self.crossrefs = crossrefs

    def __repr__(self):
        # TODO
        return "<Verse: {}>".format(super().to_string())
        # return ""

    def to_string(self):
        return "{} `{}` ({})".format(super().to_string(),self.text,self.version)

    def to_dict(self):
        return dict(
            book = self.book,
            chapter = self.chapter,
            verse = self.verse,
            version = self.version,
            text = self.text,
            footnotes = self.footnotes,
            crossrefs = self.crossrefs
        )

    @classmethod
    def from_dict(cls,obj):
        return cls(**obj)

    def add_crossref(self, crossref):
        self.crossrefs.append(crossref)

    def add_footnote(self, footnote):
        self.footnotes.append(footnote)

    def equals(self, other):
        """Checks if provided Verse is equal to this one
        """
        if not isinstance(other,Verse):
            return False
        return self.version == other.version\
            and self.chapter == other.chapter\
            and self.book == other.book\
            and self.verse == other.verse

def find_class(tag, class_name):
    if tag.has_attr("class"):
        for attr in tag.attrs:
            if attr == "class":
                for c in tag["class"]:
                    if c == class_name:
                        return True
    return False

def format_tag(config, verse_text, tag):
    if isinstance(tag, ResultSet):
        print("1. Shouldn't be here.")
    if isinstance(tag, Tag):
        if find_class(tag, "text"):
            # This is the first entry in poetry:
            for child in tag:
                verse_text = format_tag(config, verse_text, child)
        
        # If this is an opening section add a paragraph mark.
        if find_class(tag, "chapternum") or find_class(tag, "versenum") or tag.name == "versenum":
            if find_class(tag, "opening"):
                verse_text = "¶ "
        # Superscript elements. These are used inline for footnotes and cross references. 
        elif tag.name == "sup":
            if find_class(tag, "footnote") or find_class(tag, "crossreference"):
                if config["output_format"] == "markdown":
                    verse_text += tag.text.replace("[", " __[").replace("]", "]__").replace("(", " __(").replace(")", ")__")
                elif config["output_format"] == "html":
                    verse_text += tag.text.replace("[", " <i>[").replace("]", "]</i>").replace("(", " <i>(").replace(")", ")</i>")
                
                # Verse footnote placement isn't consistent between versions. Strip double spaces in output.
                verse_text = verse_text.replace("  ", " ")
        elif tag.name == "div":
            if find_class(tag, "poetry"):
                # Poetry is handled in the calling code, but keep it here for completeness.
                pass
        # Handle small-capped LORD
        elif find_class(tag, "small-caps"):
            if config["output_format"] == "markdown":
                verse_text += "**LORD**"
            elif config["output_format"] == "html":
                verse_text += "<b>LORD</b>"
        elif tag.name == "versenum": # Numbers 23
            # Some chapters tstart in the middle of a paragraph.
            pass
    elif isinstance(tag, NavigableString):
        # If the tag is just text append it.
        verse_text += str(tag.string)
    else:
        # Something went wrong and the tag wasn't handled by one of the cases above.
        print("3 Shouldn't be here.")
        return verse_text
    
    # Return a true or false if the verse text should get passed up to book object.
    return verse_text

def format_footnote(text, tag):
    if isinstance(tag, Tag):
        if tag.name == "i":
            if config["output_format"] == "markdown":
                text += "__{}__".format(tag.text)
            elif config["output_format"] == "html":
                text += "<i>{}</i>".format(tag.text)
        elif find_class(tag, "small-caps"):
            if config["output_format"] == "markdown":
                text += "**LORD**"
            elif config["output_format"] == "html":
                text += "<b>LORD</b>"
        elif tag.name == "a":
            text += "[[{}]]".format(tag.text)
    elif isinstance(tag, NavigableString):
        text += tag.text
    else:
        print("4 Shouldn't be here.")
    
    return text

def normalize_verse_class(text):
    m = re.match("(.+)-(\d+)-(\d+)", text)
    if m:
        if len(m.groups()) == 3:
            return {
                "ref": m.group(0),
                "book": m.group(1),
                "chapter": m.group(2),
                "verse": m.group(3),
            }
        else:
            return None
    else:
        return None

def find_class_verse(tag):
    # If this somehow got called with a NavigableString or List bail out.
    if isinstance(tag, Tag):

        # check for a class attribute. The verse will get parsed from 
        # the tag's class.
        if tag.has_attr("class"):
            for attr in tag.attrs:
                if attr == "class":
                    for clsstr in tag.attrs['class']:
                        n = normalize_verse_class(clsstr)
                        found = None
                        if n:
                            found = bible.get_references("{} {}:{}".format(n["book"], n["chapter"], n["verse"]))
                        if found:
                            return {
                                "found": True,
                                "clsstr": n["ref"],
                                "verse_id": bible.convert_reference_to_verse_ids(found[0])[0]
                            }
                            # return [True, (n["ref"], found)]
    else:
        raise TypeError("find_class_verse expects a Tag.")
    
    return {"found": None, "clsstr": None, "bcv": None}

if __name__ == '__main__':

    problem_verses = []

    # Set these to None to run all books, or chapter, or verses.
    debug = None # "Gen-2-1"

    with open(Path("config.json"), "r") as f:
        config = json.loads(f.read())

    with open(Path("books", "input", config["version"], "chapters_{}.json".format(config["version"])), 'r') as f:
        books = json.loads(f.read())

    for book in books["books"]:

        found_types = []
        
        INDENT = "    "
        refs = []

        this_book = Book(name=book["name"], version=config["version"])
        print(this_book.short_title)

        for chapter_num in tqdm(range(1, this_book.chapters), initial=1, unit="verse", total=this_book.chapters):
            
            # Verses will hold all the individual verses that make up a book.
            # Verses is flat, the verse object itself holds the chapter info.
            this_book.verses = []

            this_book.chapters = chapter_num

            # Open the html saves from download.py
            with open(Path("books", "input", config["version"], "html", "{}-{}.html".format(
                    book["name"], 
                    str(chapter_num)))
                , "r", encoding='utf-8') as f:

                # Initialize the bs4 parser. html.parser works fine with the
                # html served by biblegateway.
                soup = BeautifulSoup(f, "html.parser")

                # Create an empty dict to hold chapter verse info.
                # As far as the author can tell all the text we want from biblegateway
                # is always conatined in a tag (or child) that has a class "text".
                verse_ids = dict()
                
                # Build a unique list of verses on this chapter's html page.
                for node in soup.find_all(class_="text"):
                    class_verse = find_class_verse(node)
                    if class_verse["found"]:
                        if len(this_book.verses) > 0:
                            exists = next((item for item in this_book.verses if item.verse_id == class_verse["verse_id"]), None)
                        else:
                            exists = False
                        if not exists:
                            skeleton_verse = Verse(class_verse["verse_id"], this_book.version, class_verse["clsstr"])
                            this_book.verses.append(skeleton_verse)

                # Start looping through the verses.
                for v in this_book.verses:
                    
                    # Uncomment out this block to process a specific verse
                    if debug != None:
                        if debug != v.clsstr:
                            continue
                    
                    # What will be the output of this verse
                    text = ""
                    
                    # Find all the verses with this verse's class string (i.e. Gen-1-1)
                    text_passages = soup.find_all("span", {"class": "text {}".format(v.clsstr)})
                    
                    # We need to keep track of how many times we've looped through this
                    # verse's elements.
                    i = 0
                    if text_passages:
                        for passage in text_passages:

                            # h3 are section headers. They can occur before a chapter-verse
                            # or within a verse (but include one after).
                            if passage.parent.name == "h3":

                                # If the element has a previous sibling then it needs a a newline
                                # before the heading.
                                if passage.parent.previous_sibling:
                                    if config["output_format"] == "markdown":
                                        text += "\n**{}**\n".format(passage.text)
                                    elif config["output_format"] == "html":
                                        text += "\n<b>{}</b>\n".format(passage.text)
                                # Otherwise it doesn't (but do include one after).
                                else:
                                    if config["output_format"] == "markdown":
                                        text += "**{}**\n".format(passage.text)
                                    if config["output_format"] == "html":
                                        text += "<b>{}</b>\n".format(passage.text)
                            
                            # If the element's parent is a versenum then this 
                            # element is a verse.
                            elif passage.parent.name == "versenum":
                                if passage.parent.previous_sibling:
                                    if config["output_format"] == "markdown":
                                        text += "\n**{}**\n".format(passage.text)
                                    elif config["output_format"] == "html":
                                        text += "\n<b>{}</b>\n".format(passage.text)
                                else:
                                    if config["output_format"] == "markdown":
                                        text += "**{}**\n".format(passage.text)
                                    if config["output_format"] == "html":
                                        text += "<b>{}</b>\n".format(passage.text)
                            else:

                                # If the element doesn't have previous siblings or isn't
                                # an h3, then it needs a paragraph mark.
                                if not passage.previous_sibling:
                                    text += "¶ "

                                # Poetry check.
                                # Does this element have a poetry encestor?
                                if passage.find_parents("div", {"class": "poetry"}):
                                    # Is this element indented?
                                    # The following will calculate how many 
                                    # indent levels are needed.
                                    for parent in passage.find_parents("span"):
                                        for clsstr in parent.attrs['class']:
                                            m = re.search("indent-(\d+)", clsstr)
                                            if m:
                                                if m.groups(0):
                                                    indent_string = INDENT * int(m.groups(0)[0])
                                                    continue
                                    # newlines after the first poetry line.
                                    if i == 0:
                                        text += INDENT
                                    else:
                                        # lines at the same indent level may have leading spaces (2nd line in Gen 1:27)
                                        if passage.previous_sibling:
                                            if passage.previous_sibling.has_attr("class"):
                                                for clsstr in passage.previous_sibling.attrs["class"]:
                                                    m = re.search("indent-(\d+)-breaks", clsstr)
                                                    if m:
                                                        previous_text = passage.previous_sibling.text
                                                        leading_indent = previous_text.replace(u'\xa0', ' ')
                                                        text = text + leading_indent
                                        else:
                                            text = text # + "\n" + INDENT

                                    # So far we've been dealing with parent tags, format_tag
                                    # will format the element with the text.
                                    text = format_tag(config, text, passage)

                                    # Each line of poetry should have a newline at the end
                                    text += "\n" + INDENT
                                    if config["output_format"] == "html":
                                        indent_string = INDENT.replace(" ", "&nbsp;")
                                    else:
                                        indent_string = INDENT
                                    i += 1
                                else:
                                    # So far we've been dealing with parent tags, format_tag
                                    # will format the element with the text.
                                    text = format_tag(config, text, passage)

                        # Set the verse's text to all the text accumulated.
                        v.text += text

                # Find footnotes on the page.
                if soup.find("div", {"class": "footnotes"}):

                    # Each footnote is stored in a orderered list item.
                    footnotes = soup.find("div", {"class": "footnotes"}).find_all("li")
                    for footnote in footnotes:
                        store = {}
                        store["text"] = ""
                        verse_id = None
                        c = None
                        v = None

                        # Each footnote will be referenced with something like fen-NRSVUE-30261a.
                        # The last letter(s) after the digits represent the footnote "letter".
                        ref = re.search("[A-Za-z]+-[A-Za-z]+-\d+([a-z]+)", footnote.attrs["id"]).groups()[0]

                        # Find the footnote href element.
                        # In the NRSVUE this is represented as a two sets of digits separated by a dot. i.e. 10:15
                        # In the ASV this is a whole verse refeernce. i.e. Genesis 1:1
                        if footnote.find("a"):
                            store["verse_ref"] = footnote.find("a").text
                        
                        # Find the text of the footnote. Format as necessary.
                        if footnote.find("span", {"class": "footnote-text"}):
                            objs = footnote.find("span", {"class": "footnote-text"})
                            for obj in objs:
                                store["text"] = format_footnote(store["text"], obj)
                        try:
                            # In the NSRVUE the footnote may be formatted like
                            # 10.15
                            # 2.31-32 (1 Samuel 2:31, 1 Kings 4:20-21) bible.convert_references_to_verse_ids(bible.get_references("1 Samuel 2:31-32"))
                            # 34.17-35.2 (Isaiah 35:17) bible.convert_references_to_verse_ids(bible.get_references("Isaiah 34:17-35:2"))
                            # pythonbible makes this easy.
                            # This will only work where biblegateway is formatting the footnote like "1.2".
                            if this_book.version == "NRSVUE":
                                references = bible.get_references("{} {}".format(this_book.short_title, store["verse_ref".replace(".", ":")]))
                                verse_ids = bible.convert_references_to_verse_ids(references)
                            elif this_book.version == "ASV":
                                references = bible.get_references("{}".format(store["verse_ref"]))
                                verse_ids = bible.convert_references_to_verse_ids(references)
                            
                            for verse_id in verse_ids:
                                found_verse_object = next((item for item in this_book.verses if item.verse_id == verse_id), None)
                                if found_verse_object:
                                    found_verse_object.add_footnote({ref: store["text"]})
                        except ValueError as e:
                            problem_verses.append("No valid verse format found in {} {}.".format(this_book.book, store["verse_ref"]))

                        

                # Cross references
                if soup.find("div", {"class": "crossrefs"}):
                    # Each set of cross references is stored in a orderered list item.
                    crossrefs = soup.find("div", {"class": "crossrefs"}).find_all("li")
                    for crossref in crossrefs:
                        store = {}
                        store["text"] = ""

                        # List of found references in the html.
                        store["clist"] = []
                        
                        # Each footnote will be referenced with something like cen-NRSVUE-2B.
                        # The last uppercase letter(s) after the digits represent the footnote "letter".
                        ref = re.search("[A-Za-z]+-[A-Za-z]+-\d+([A-Z]+)", crossref.attrs["id"]).groups()[0]
                        
                        # Find the footnote href element.
                        # In the NRSVUE this is represented as a two sets of digits separated by a dot. i.e. 10:15
                        try:
                            if crossref.find("a"):
                                store["verse_ref"] = crossref.find("a").text

                                # Full text of a reference is found in a data-bibleref attribute
                                clist = [r.strip() for r in crossref.find(class_="crossref-link").attrs["data-bibleref"].split(",")]

                                source_verse = bible.get_references("{} {}".format(this_book.short_title, store["verse_ref".replace(".", ":")]))
                                source_verse_id = bible.convert_reference_to_verse_ids(source_verse[0])
                                for c in clist:
                                    found_verse_object = next((item for item in this_book.verses if item.verse_id == source_verse_id[0]), None)
                                    found_verse_object.add_crossref({ref: c})
                                    # TODO Think about how to store references like Job 38.26–28 or Gen 3.7, 10, 11.
                                    # verse_ids = bible.convert_references_to_verse_ids(bible.get_references(c))
                                    # if verse_ids:
                                    #     for verse_id in verse_ids:
                                    #         found_verse_object = next((item for item in this_book.verses if item.verse_id == verse_id), None)
                                    #         if found_verse_object:
                                    #             found_verse_object.add_crossref({ref: verse_id})
                        except ValueError as e:
                            problem_verses.append("No valid verse format found in {} {}.".format(this_book.book, store["verse_ref"]))
                            
            # Check for empty verses, this indicates something went wrong parsing the verse.
            # If debug is not None this will be all wonky, do don't show.
            if debug == None:
                for v in this_book.verses:
                    if v.text == "":
                        problem_verses.append("Something wrong with {} {} {}.".format(this_book.book.title, chapter_num, v.verse))
                    # Some part of the process is appending a newline (or <br>) before section
                    # headings. # TODO figure out why.
                    if v.text.startswith("\n<b>"):
                        v.text = v.text[1:]

            if config["output_format"] == "html":
                Path("books", "output", config["version"], "html").mkdir(parents=True, exist_ok=True)
                with open(Path("books", "output", config["version"], "html", "{}-{}.json".format(book["name"], str(chapter_num))), "w", encoding='utf-8') as f:
                    f.write(json.dumps(this_book, indent=4, cls=BookEncoder))
            elif config["output_foramt"] == "markdown":
                Path("books", "output", config["version"], "markdown").mkdir(parents=True, exist_ok=True)
                with open(Path("books", "output", config["version"], "html", "{}-{}.json".format(book["name"], str(chapter_num))), "w", encoding='utf-8') as f:
                    f.write(json.dumps(this_book, indent=4, cls=BookEncoder))
    
    for problem in problem_verses:
        print(problem)
            
    # TODO space in 2nd clause of Matthew 1:6
    # TODO double line breaks in poetry
    # TODO fix James 1 in NRSVUE
    # TODO use pythonbible to find references in footnote and crossreference strings.
    # TODO let pythonbible try to find footnote verse_ref, if fails prepend book name
    #      and try again.
