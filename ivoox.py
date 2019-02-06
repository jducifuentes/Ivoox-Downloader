import argparse
import os

import bs4
import requests
import unicodedata
import string



global valid_filename_chars
valid_filename_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
global char_limit
char_limit = 255


def new_bs(url):
    return bs4.BeautifulSoup(requests.get(url).content, "html5lib")


def get_urls_page(soup: bs4.BeautifulSoup):
    ans = []
    global title
    rect = soup.find_all("p", "title-wrapper text-ellipsis-multiple")
    #print ("*************************")
    #print (rect)
    for r in rect:
        ans += [r.find('a').get('href')]
        title += [r.find('a').get('title')]
    return ans

def clean_filename(filename, whitelist=valid_filename_chars, replace=' '):
    # replace spaces
    #print ("*/*/*/*/*/*/*/*/*/*/*/*/*/*/")
    #print (type(filename))
    for r in replace:
        filename = filename.replace(r,'_')    
    # keep only valid ascii chars
    cleaned_filename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore').decode()
    
    # keep only whitelisted chars
    cleaned_filename = ''.join(c for c in cleaned_filename if c in whitelist)
    if len(cleaned_filename)>char_limit:
        print("Warning, filename truncated because it was over {}. Filenames may no longer be unique".format(char_limit))
    return cleaned_filename[:char_limit]

def hasnext(soup: bs4.BeautifulSoup):
    new_url = None
    pag = soup.find("ul", "pagination")
    if not pag:
        return new_url
    pags = pag.find_all("li")
    sig = pags[-1]
    if sig.get("class") is None or "disabled" not in sig.get("class"):
        new_url = sig.find('a').get('href')
    return new_url


def get_urls(root_url: str):
    soup = new_bs(root_url)
    ans = []
    while 1:
        ans += get_urls_page(soup)
        next_page = hasnext(soup)
        if not next_page:
            break
        soup = new_bs(next_page)
    return ans


def get_download_url(url: str):
    link = new_bs(url).find_all('script')

    import re

    bingo = re.compile(".downloadlink'\)")

    def search():
        for l in link:
            if len(l.contents) > 0:
                for r in l.contents[0].split('\n'):
                    if bingo.search(r):
                        return "https://www.ivoox.com/" + r.strip(' ')[25:-3]

    return new_bs(search()).find('a').get('href')


def get_download_urls(root):
    pages = get_urls(root)
    return list(map(lambda x: get_download_url(x), pages))


def format_n(n):
    return ("000" + str(n))[-3:]

if __name__ == '__main__':
    title = []
   

    # Lectura
    parser = argparse.ArgumentParser()
    parser.add_argument("url", type=str, help="url of audio")
    parser.add_argument("dir_name", type=str, help="name of directory")
    parser.add_argument("path", type=str, help="path to save")
    #parser.add_argument("-r", "--reversed",
    #                    action="store_true", dest="rev", default=False,
    #                    help="reversed order")

    args = parser.parse_args()

    url_r = args.url
    name = args.dir_name
    download_path = os.path.join(args.path, name)
    #rev = args.rev

    if not os.path.exists(download_path):
        os.makedirs(download_path)

    print("Getting urls##########################################################")
    links = get_download_urls(url_r)

    #links = links[::-1]

    print("Start Download#######################################################")
    for i, _url in enumerate(links):
        fichero2 = title[i]
        fichero2 = fichero2.replace('.',' ')
        fichero2 = fichero2.rstrip()
        fichero = clean_filename(fichero2)
        fichero = fichero.replace('_',' ')
        
        local_filename = os.path.join(download_path, f"{fichero}.mp3")
        print(_url)
        req = requests.get(_url, stream=True)
        with open(local_filename, 'wb') as f:
            for chunk in req.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        print(f"Download : {100*(i+1) / len(links):.2f}%")


