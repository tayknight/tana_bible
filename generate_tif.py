import argparse
import json
import sys
import traceback

import pythonbible as bible

from pathlib import Path
from operator import itemgetter

from tqdm import tqdm

class Book:
    def __init__ (self, bookinfo, version):
        self.book = bookinfo["name"]
        self.chapters = bookinfo["chapters"]
        self.version = version
        self.verses = []
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)

def normalize_name(input):
    return input.replace(" ", "-").replace(":", "-")

if __name__ == '__main__':
    try:
        arg_desc = "Command line switches are optional."
        parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description = arg_desc)

        parser.add_argument("-o", "--output", help = "Output file name. Will be saved in output/{version}/tif/{input}.json). If ommited will default to {version}.json.", required=False)
        parser.add_argument("-b", "--books", nargs = "+", help = "Books groups to include. See README.md for valid options.", required=False)

        args = vars(parser.parse_args())

        # TODO fix the ref that looks like 'Job 38:26-Job 38:28'
        # TODO fix the ref that looks like '1 Chronicles 1:5-1 Chronicles 1:7'

        # Set these to None to run all books, or chapter, or verses.
        debug_book = None # or something like "James"
        debug_chapter = None # or a particular chapter integer
        debug_verse = None # or a particular verse integer

        with open(Path("config.json"), "r") as f:
            config = json.loads(f.read())

        with open(Path("books", "input", config["version"], "chapters_{}.json".format(config["version"])), 'r') as f:
            books = json.loads(f.read())

        # For output
        tif_folder = Path("books", "output", config["version"], "tif")
        tif_folder.mkdir(parents=True, exist_ok=True)

        tif_object = {
            "version": "TanaIntermediateFile V0.1",
            "attributes": [
                {
                    "name": "Version",
                    "dataType": "any"
                },
                {
                    "name": "Book (abbr)",
                    "dataType": "any"
                },
                {
                    "name": "Book",
                    "dataType": "any"
                },
                {
                    "name": "Chapter",
                    "dataType": "any"
                },
                {
                    "name": "Starting Verse",
                    "dataType": "any"
                },
                {
                    "name": "Ending Verse",
                    "dataType": "any"
                },
                {
                    "name": "Footnotes",
                    "dataType": "any"
                },
                {
                    "name": "Cross References",
                    "dataType": "any"
                }
            ],
            "nodes": [],
            "supertags": [
                {
                    "uid": "bibleverse",
                    "name": "verse"
                }
            ]
        }

        max_keys = 0

        # command line switch to only generate tana import files for certain Bible groups 
        # (https://github.com/avendesora/pythonbible/blob/main/pythonbible/book_groups.py)
        # The possible groups are:
        # OLD_TESTAMENT_LAW
        # OLD_TESTAMENT_HISTORY
        # OLD_TESTAMENT_POETRY_WISDOM
        # OLD_TESTAMENT_PROPHECY
        # OLD_TESTAMENT_MAJOR_PROPHETS
        # OLD_TESTAMENT_MINOR_PROPHETS
        # NEW_TESTAMENT
        # NEW_TESTAMENT_GOSPELS
        # NEW_TESTAMENT_HISTORY
        # NEW_TESTAMENT_EPISTLES
        # NEW_TESTAMENT_PAUL_EPISTLES
        # NEW_TESTAMENT_GENERAL_EPISTLES
        # NEW_TESTAMENT_APOCALYPTIC
        b = ()

        try:
            if args["books"]:
                for this_input in args["books"]:
                    b = b + bible.BookGroup[this_input].books
        except KeyError as e:
            print("Cound not find input book group.")
            print(e)

        for book in books["books"]:
            
            this_book = Book(bookinfo=book, version=config["version"])
            
            if bible.get_references(this_book.book)[0].book in b or args["books"] is None:
                print(this_book.book)

                for chapter_num in tqdm(range(1, this_book.chapters), initial=1, unit="verse", total=this_book.chapters):
                    with open(Path("books", "output", config["version"], config["output_format"], "{}-{}.json".format(this_book.book, chapter_num)), "r") as f:
                        o = json.load(f)
                
                    #for chapter_num in tqdm(range(1, this_book.chapters), initial=1, unit="verse", total=this_book.chapters):
                    for verse in o["verses"]:
                        node = {
                            "type": "node",
                            "uid": "{}".format(verse["verse_id"]),
                            #"uid": "{}-{}-{}".format(normalize_name(o["book"]),bible.get_chapter_number(verse["verse_id"]),verse["verse"]),
                            "name": "{} {}:{}".format(this_book.book,bible.get_chapter_number(verse["verse_id"]),bible.get_verse_number(verse["verse_id"])),
                            "supertags": ["bibleverse"],
                            "children": [
                                {
                                    "type": "field",
                                    #"uid": "{}-{}-{}-book-abbr".format(normalize_name(o["book"]),bible.get_chapter_number(verse["verse_id"]),verse["verse"]),
                                    "uid": "{}-book-abbr".format(verse["verse_id"]),
                                    "name": "Book (abbr)",
                                    "children": [
                                        {
                                            "type": "node",
                                            "uid": "{}-book-abbr-val".format(verse["verse_id"]),
                                            # "uid": "{}-{}-{}-book-abbr-val".format(normalize_name(o["book"]),bible.get_chapter_number(verse["verse_id"]),verse["verse"]),
                                            "name":this_book.book
                                        }
                                    ]
                                },
                                                {
                                    "type": "field",
                                    "uid": "{}-book-".format(verse["verse_id"]),
                                    # "uid": "{}-{}-{}-book".format(normalize_name(o["book"]),bible.get_chapter_number(verse["verse_id"]),verse["verse"]),
                                    "name": "Book",
                                    "children": [
                                        {
                                            "type": "node",
                                            "uid": "{}-book-val".format(verse["verse_id"]),
                                            # "uid": "{}-{}-{}-book-val".format(normalize_name(o["book"]),bible.get_chapter_number(verse["verse_id"]),verse["verse"]),
                                            "name": this_book.book
                                        }
                                    ]
                                },
                                                {
                                    "type": "field",
                                    "uid": "{}-chapter".format(verse["verse_id"]),
                                    # "uid": "{}-{}-{}-chapter".format(normalize_name(o["book"]),bible.get_chapter_number(verse["verse_id"]),verse["verse"]),
                                    "name": "Chapter",
                                    "children": [
                                        {
                                            "type": "node",
                                            "uid": "{}-chapter-val".format(verse["verse_id"]),
                                            # "uid": "{}-{}-{}-chapter-val".format(normalize_name(o["book"]),bible.get_chapter_number(verse["verse_id"]),verse["verse"]),
                                            "name": str(bible.get_chapter_number(verse["verse_id"]))
                                        }
                                    ]
                                },
                                                {
                                    "type": "field",
                                    "uid": "{}-starting-verse".format(verse["verse_id"]),
                                    # "uid": "{}-{}-{}-starting-verse".format(normalize_name(o["book"]),bible.get_chapter_number(verse["verse_id"]),verse["verse"]),
                                    "name": "Starting Verse",
                                    "children": [
                                        {
                                            "type": "node",
                                            "uid": "{}-starting-verse-val".format(verse["verse_id"]),
                                            # "uid": "{}-{}-{}-starting-verse-val".format(normalize_name(o["book"]),bible.get_chapter_number(verse["verse_id"]),verse["verse"]),
                                            "name": str(bible.get_verse_number(verse["verse_id"]))
                                        }
                                    ]
                                },
                                                {
                                    "type": "field",
                                    "uid": "{}-ending_verse".format(verse["verse_id"]),
                                    # "uid": "{}-{}-{}-ending-verse".format(normalize_name(o["book"]),bible.get_chapter_number(verse["verse_id"]),verse["verse"]),
                                    "name": "Ending Verse",
                                    "children": [
                                        {
                                            "type": "node",
                                            "uid": "{}-ending-verse-val".format(verse["verse_id"]),
                                            # "uid": "{}-{}-{}-ending-verse-val".format(normalize_name(o["book"]),bible.get_chapter_number(verse["verse_id"]),bible.get_verse_number(verse["verse_id"])),
                                            "name": str(bible.get_verse_number(verse["verse_id"]))
                                        }
                                    ]
                                },
                                {
                                    "type": "node",
                                    "uid": "{}-text".format(verse["verse_id"]),
                                    # "uid": "{}-{}-{}-text".format(normalize_name(o["book"]),bible.get_chapter_number(verse["verse_id"]),verse["verse"]),
                                    "name": verse["text"]
                                }
                            ]
                        }

                        children = []

                        f_i = 0

                        # For this verse, get all the footnotes that were found when parsing the html.
                        for footnote in verse["footnotes"]:
                            if verse["clsstr"] == 'Gen-2-14':
                                pass
                            for verse_key in list(footnote.keys()):
                                note = {
                                    "type": "node",
                                    "uid": "{}-fn-values-{}".format(verse["verse_id"], f_i),
                                    # "uid": "{}-{}-{}-fn-values".format(normalize_name(o["book"]),bible.get_chapter_number(verse["verse_id"]),verse["verse"]),
                                    "name": "{}: {}".format(verse_key, footnote[verse_key])
                                }
                                children.append(note)
                                f_i += 1

                        footnote_object = {
                            "type": "field",
                            "uid": "{}-fn".format(verse["verse_id"]),
                            "name": "Footnotes",
                            "children": children
                        }

                        node["children"].append(footnote_object)

                        # The "name" in this case is the text of the node.
                        cross_ref_name = ""

                        # Each verse may have multiple cross references. Keep track of where we are in the count.
                        c_i = 0

                        refs = []

                        # If there are cross references...
                        if len(verse["crossrefs"]) > 0:

                            # At the time of writing every verse parsed from the HTML for the NRSVUE
                            # only has one set of cross references.
                            # So, verse["crossrefs"] might look like 
                            # [{"A": "Psalm 8:3"}, {"A": "Isaiah 42:5"}]

                            # # Start with an empty key. In the NRSVUE the key is the capital letter at the end
                            # of the verse, it denotes a cross reference.
                            # Get the first element's key
                            key = list(verse["crossrefs"][0].keys())[0]

                            # Set up an object to hold information about this verse's footnotes.
                            cross_refs_object = {
                                "type": "node",
                                "uid": "{}-cr-values".format(verse["verse_id"]),
                                "name": key,
                                "children": []
                            }

                            for this_key in verse["crossrefs"]:
                                # Initialize a new bible reference. This is what we're searching
                                # for in the cross reference.
                                bible_ref = None

                                # If the key doesn't match the last key fetched then update the key
                                # and print info. At least for the NRSVUE this shouldn't happen.
                                if list(this_key.keys())[0] != key:
                                    if key != None:
                                            tqdm.write("New key in {} {}:{}".format(
                                            this_book.book,
                                            bible.get_chapter_number(verse["verse_id"]),
                                            bible.get_verse_number(verse["verse_id"])
                                            )
                                        )
                                    key = list(this_key.keys())[0]
                                    c_i += 1
                                try:
                                    # Try to get a reference from the text of the individual cross reference
                                    # element. Throw an error if the verse can't be processed.
                                    # TODO set a flag and continue so that the text of the reference can be
                                    # included.
                                    bible_ref = bible.get_references(this_key[key])
                                except ValueError as e:
                                    tqdm.write("Problem with {} {}:{}. {}".format(
                                        this_book.book,
                                        bible.get_chapter_number(verse["verse_id"]),
                                        bible.get_verse_number(verse["verse_id"]),
                                        this_key[key])
                                    )
                                    # break
                                    plain = True
                                
                                # If bible_ref represents one verse from one chapter that will be formatted as a link
                                # to a node.
                                if bible_ref:
                                    if len(bible_ref) == 1:
                                        if bible_ref[0].end_chapter == bible_ref[0].start_chapter and bible_ref[0].end_verse == bible_ref[0].start_verse:
                                            # What is the target refernce (i.e. 1001001 for Genesis 1:1.)
                                            target = bible.convert_reference_to_verse_ids(bible.get_references(this_key[key])[0])

                                            name = "{}".format(key)

                                            # Create a child for the actual cross reference elements.
                                            cross_ref_node = {
                                                "type": "node",
                                                "uid": "{}-cr-values-{}".format(verse["verse_id"], c_i),
                                                "name": "[{alias}]([[{uid}]])".format(
                                                    alias=this_key[key],
                                                    uid=target[0]
                                                ),
                                                "refs": ["{}".format(target[0])]
                                            }
                                            plain = False
                                            cross_refs_object["children"].append(cross_ref_node)
                                        else:
                                                plain = True
                                    else:
                                        plain = True
                                else:
                                    plain = True
                                
                                if plain:
                                    cross_ref_node = {
                                        "type": "node",
                                        "uid": "{}-cr-values-{}".format(verse["verse_id"], c_i),
                                        "name": this_key[key]
                                    }
                                    cross_refs_object["children"].append(cross_ref_node)
                                    
                                c_i += 1
                            
                            # Final ouput. Contains nested objects.
                            crossref_object = {
                                "type": "field",
                                "uid": "{}-cr".format(verse["verse_id"]),
                                "name": "Cross References",
                                "children": [cross_refs_object]
                            }
                            node["children"].append(crossref_object)
                        tif_object["nodes"].append(node)

        if len(tif_object["nodes"]) > 0:
            if args["output"]:
                if args["output"][-5:] == ".json":
                    filename = args["output"][:-5]
                else:
                    filename = args["output"]

                with open(Path(tif_folder, "{}.json".format(filename)), "w") as f:
                    output = json.dumps(tif_object, indent=2)
                    f.write(output)
            else:
                with open(Path(tif_folder, "{}.json".format(config["version"])), "w") as f:
                    output = json.dumps(tif_object, indent=2)
                    f.write(output)

    except Exception:
        traceback.print_exc()
    