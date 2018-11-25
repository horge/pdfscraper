import subprocess
import re
import codecs
import csv
import glob, os
from sys import platform
import time
import asyncio
import shutil

if platform == "linux" or platform == "linux2":
    # linux
    DEL_CMD = "rm"
    SHELL   = False
elif platform == "darwin":
    # OS X
    DEL_CMD = "rm"
    SHELL   = False
elif platform == "win32":
    # Windows...
    DEL_CMD = "del"
    SHELL   = True

PDF_FOLDER = "pdf"
TMP_FOLDER = "tmp"
PDFTOTEXT  = "/3rdparty/pdftotext"


def debug_output(s):
    if __debug__:
        print (s)


def return_files_in_folder_with_suffix(folder, suffix):
    os.chdir(folder)
    files = []
    for file in glob.glob("*." + suffix):
        files.append(file)
    os.chdir("..")
    return files


def replace_german_signs(s):
    s = s.replace(u'ü', 'ue')
    s = s.replace(u'ä', 'ae')
    s = s.replace(u'ü', 'ue')
    s = s.replace(u'ß', 'ss')
    return s


def normalize_string(s):
    # lower search string and pdf content
    s = s.lower()
    # replace german signs
    s = replace_german_signs(s)
    # remove multiple blanks
    s = re.sub(' +', ' ', s)
    # remove line breaks
    s = s.replace("-\n", '')
    # remove new lines
    s = s.replace('\n', ' ')
    # remove multiple whitespaces
    #s = " ".join(s.split())
    # remove whitespaces before "/"
    s = s.replace(' /', '/')
    # remove whitespaces after "/"
    s = s.replace('/ ', '/')
    return s


def optimize_search_terms(search_terms):
    search_terms_optimized = []
    for str in search_terms:
        tmp = normalize_string(str)
        search_terms_optimized.append(tmp)
    return search_terms_optimized


def find_str_in_content(search_string, content):
    index = 0
    cnt = 0
    while index < len(content):
        index = content.find(search_string, index)
        if index == -1:
            break
        cnt += 1
        index += 2  # +2 because len('ll') == 2
    return cnt


def convert_pdf_to_txt(pdf_item):
    # Load pdf
    debug_output("Reading pdf " + pdf_item)
    # look at https://github.com/rcy222/PDF-Analytics/blob/master/PDF-Analyzer.py
    pdf_file   = os.getcwd() + "/" + PDF_FOLDER + "/" + pdf_item
    pdf_parsed = os.getcwd() + "/" + TMP_FOLDER + "/" + pdf_item + "_parsed.txt"
    cmd = [os.getcwd() + PDFTOTEXT, "-enc", "UTF-8", pdf_file, pdf_parsed]
    #debugOutput("Calling " + cmd)
    return subprocess.Popen(cmd, shell=SHELL, stdin=None, stdout=None, stderr=None, close_fds=True)


async def scrape_txt_file(txt_file, searchTerms):
    full_path = os.getcwd() + "/" + TMP_FOLDER + "/" + txt_file
    f = open(full_path, "r")
    txt_content_str = f.read()
    f.close()

    # normalize content str
    txt_content_str = normalize_string(txt_content_str)

    # Append to csv data
    csv_result = txt_file.replace('.pdf_parsed.txt', '')

    # Search for searchterms in pdfs
    for j in range(len(searchTerms)):
        items_found = find_str_in_content(searchTerms[j], txt_content_str)
        debug_output("Found occurrences of " + searchTerms[j] + ": %d" % items_found)
        csv_result += "," + str(items_found)
    return csv_result


def clean_up():
    #if os.path.isdir(os.getcwd() + "/" + TMP_FOLDER):
    #    os.removedirs(os.getcwd() + "/" + TMP_FOLDER)
    shutil.rmtree(os.getcwd() + "/" + TMP_FOLDER)


def main():
    procStart = time.perf_counter()

    searchFileName = "search_terms.txt"
    f = codecs.open(searchFileName, "r", "utf-8-sig")
    search_strings_in_unicode = f.read()
    f.close()
    searchTerms = search_strings_in_unicode.splitlines()

    pdfList = return_files_in_folder_with_suffix(PDF_FOLDER, "pdf")

    # fill out header of csv_data
    csv_data = "Dateiname"
    for i in range(len(searchTerms)):
        csv_data += "," + searchTerms[i]
    csvRowList = []
    csvRowList.append(csv_data)

    searchTerms = optimize_search_terms(searchTerms)

    if not os.path.isdir(os.getcwd() + "/" + TMP_FOLDER):
        os.makedirs(os.getcwd() + "/" + TMP_FOLDER)

    processes = []
    for i in range(len(pdfList)):
        processes.append(convert_pdf_to_txt(pdfList[i]))

    for process in processes:
        process.wait()

    txt_list = return_files_in_folder_with_suffix(TMP_FOLDER, "txt")
    tasks = []
    loop = asyncio.get_event_loop()
    for txt_file in txt_list:
        t = loop.create_task(scrape_txt_file(txt_file, searchTerms))
        tasks.append(t)

    csvResults = []
    done, pending = loop.run_until_complete(asyncio.wait(tasks))
    for future in done:
        csvResults.append(future.result())
    loop.close()

    csvResults = sorted(csvResults, key=str.lower)
    csvRowList.extend(csvResults)

    with open("output.csv", "w", newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        for line in csvRowList:
            writer.writerow(line.strip('"').split(','))

    # remove tmp folder
    clean_up()

    procEnd = time.perf_counter()
    print("Elapsed time {:0.2f}".format(procEnd - procStart) + " s")


if __name__ == "__main__":
    main()
