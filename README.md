# Tana Bible

Tana Bible is a Python library that can generate Tana Import Formatted files from Christian Bibles fetched from the BibleGateway. Bibles that have footnotes and cross references are supported and simple verses mentioned in footnotes and cross references are linked as node references.

# *Caveat Utilitor*
*As of Jan. 26, 2023 the `books/output/ASV/tif/ASV.json` fails when it is imported into Tana. Part of the reason for this project is to try to troubleshoot this large import. The import works on a smaller subset of books. For instance `python.exe generate_tif.py -o OT_L.json -b OLD_TESTAMENT_LAW` will create a file that can be successfully imported. However, as far as the author can tell the there is no way to "rescan" a workspace to hook up node references that didn't exist at import time. So, for instance, it currently doesn't seem possible to import just OLD_TESTAMENT_LAW, and then OLD_TESTAMENT_HISTORY and have the references work correctly.*

## *Caveat Lector*
The public domain ASV and the public domain KJV at BibleGateway don't contain very many cross references or footnotes. The NRSVUE version does have cross references and footnoes and this project can sucessfully parse them.

# Installation

Use pip to install the requirements.

```bash
pip install -r requirements.txt
```

## Usage

This project will attempt to pull down all the chapters for the English Protestant Canon from specified Bible [versions](https://www.biblegateway.com/versions/) on [BibleGateway](biblegateway.com) (see the notes at the beginning of `download.py` for more information / limitations). 

__Most Bible versions are copywritten. You should comply with the Copyright notice on the version's page on BibleGateway when using this project. The ASV and KJV are two public domain Bibles.__

This project makes heavy use of a library called [pythonbible](https://github.com/avendesora/pythonbible). pythonbible parses verse references like `Genesis 1:1` or `1st Kings 1:2-4` into book-chapter-verse(s) tuples.

The `config.json` file needs to be updated if you want to use a version other than the ASV. Please see the [versions](https://www.biblegateway.com/versions/) page at BibleGateway for available version. If you change config.json you need to update `human_name` and `version`. Human Name comes from the URL of the version. For instance, the URL for the ASV is 

```https://www.biblegateway.com/versions/American-Standard-Version-ASV-Bible/#booklist```.

The `human_name` of this version is `American-Standard-Version`. The version is the part between the `human_name` and `-Bible` in the URL. So, in this case, `ASV`.

`output_format` can be `html` or `markdown`, but the script has really only been tested for the Tana Import Format with `html`. This switch only affects how text *inside* the node inside the json file is formatted. It doesn't output markdown formatted files.

## Scripts
### download.py
`download.py` will attempt to download the Protestant Canon from the configured version. The html files will be saved to `books/input/{version}/html`. One file per book per chapter.

### parse.py
`parse.py` will attempt to extract all the verses from each book. Json files will be saved in `books/output/{output_format}/Book_Chapter.json`. The script tries to create a json document that looks the example in `books/output/example/html/book_chapter.json`.

### generate_tif.py
`generate_tif.py` will try to turn the `.json` files into Tana Import Format files. The general structure of the file will look something like the example below. This command accepts command line arguments:

`-o` output. What to name the output file?

`-b` books. Which groups of books should be included. Valid values are:
  * OLD_TESTAMENT_
  * OLD_TESTAMENT_LAW
  * OLD_TESTAMENT_HISTORY
  * OLD_TESTAMENT_POETRY_WISDOM
  * OLD_TESTAMENT_PROPHECY
  * OLD_TESTAMENT_MAJOR_PROPHETS
  * OLD_TESTAMENT_MINOR_PROPHETS
  * NEW_TESTAMENT
  * NEW_TESTAMENT_GOSPELS
  * NEW_TESTAMENT_HISTORY
  * NEW_TESTAMENT_EPISTLES
  * NEW_TESTAMENT_PAUL_EPISTLES
  * NEW_TESTAMENT_GENERAL_EPISTLES
  * ~~NEW_TESTAMENT_APOCALYPTIC~~

For example `python.exe generate_tif.py -b OLD_TESTAMENT_LAW OLD_TESTAMENT_HISTORY -o 1.json`

Please see `books/output/example/tif/example_version.json` for an example of what can be imported into Tana.

## Default Bible
The [American Standard Version](https://www.biblegateway.com/versions/American-Standard-Version-ASV-Bible/#booklist) is in the public domain. It has been processed through `download.py`, `parse.py`, and `generate_tif.py`. The downloaded html is saved in `books/input/ASV/html/`, the intermediate json files are in `books/output/ASV/html/`, and the output Tana intermediate format is saved in `books/output/ASV/tif/ASV.json`.

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)