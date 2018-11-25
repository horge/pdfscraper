# pdfscraper
Count multiple words in multiple pdf files. 

This script searches for multiple search terms in multiple pdfs and creates a csv file which contains the result set.

# Dependencies
This project uses the binary file `pdftotext` from [Xpdf tools](http://www.xpdfreader.com/download.html). `pdftotext` must be placed inside of the folder `3rdparty`.

# Usage
1. Put the pdf files which you would like to scrape inside of the folder `pdf`
2. Enter your search terms inside of `search_terms.txt` - each line represents a new search term
3. Call `pdfscraper.py`, this will create a file called `output.csv` with the result set
