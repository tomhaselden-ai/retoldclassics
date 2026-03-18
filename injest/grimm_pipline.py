import os
import json
import re
from urllib.parse import urljoin, urlparse
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
import mysql.connector
from openai import OpenAI

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

HTML_FILE = r"C:\Users\Administrator\story_universe_platform\injest\grimms.html"

BASE_URL = "https://www.cs.cmu.edu/~spok/grimmtmp/"

OPENAI_API_KEY =  os.getenv("OPENAI_API_KEY")


DB_CONFIG = {
    "host": "localhost",
    "user": "rtcwa",
    "password": "!Wdfez69",
    "database": "grimm"
}

client = OpenAI(api_key=OPENAI_API_KEY)

# --------------------------------------------------
# DATABASE
# --------------------------------------------------

def db_connect():
    return mysql.connector.connect(**DB_CONFIG)

# --------------------------------------------------
# EMBEDDINGS
# --------------------------------------------------

def get_embedding(text):

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    return response.data[0].embedding

# --------------------------------------------------
# PARSE STORY LIST
# --------------------------------------------------

def extract_story_links():

    with open(HTML_FILE, encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    stories = []

    links = soup.find_all("a")

    for link in links:

        href = link.get("href")

        if href and href.endswith(".txt"):

            title = link.text.strip()
            filename = os.path.basename(urlparse(href).path)
            number_text = filename.replace(".txt", "")

            if not number_text.isdigit():
                continue

            story_num = int(number_text)

            stories.append({
                "number": story_num,
                "title": title,
                "url": urljoin(BASE_URL, href)
            })

    return stories

# --------------------------------------------------
# DOWNLOAD STORY
# --------------------------------------------------

def download_story(url):

    r = requests.get(url)

    text = r.text

    paragraphs = []

    for p in text.split("\n"):

        p = p.strip()

        if len(p) > 30:
            paragraphs.append(p)

    return paragraphs

# --------------------------------------------------
# MORAL DETECTION
# --------------------------------------------------

def detect_moral(paragraphs):

    for p in paragraphs:

        m = re.search(r"moral[:\.]?\s*(.*)", p, re.IGNORECASE)

        if m:
            return m.group(1)

    return None

# --------------------------------------------------
# INSERT STORY
# --------------------------------------------------

def insert_story(cursor, story):

    sql = """
    INSERT INTO stories
    (story_number,title,source)
    VALUES (%s,%s,%s)
    """

    cursor.execute(sql,(
        story["number"],
        story["title"],
        "Grimm"
    ))

    return cursor.lastrowid

# --------------------------------------------------
# INSERT PARAGRAPH
# --------------------------------------------------

def insert_paragraph(cursor,story_id,idx,text):

    emb = get_embedding(text)

    sql = """
    INSERT INTO paragraphs
    (story_id,paragraph_index,paragraph_text,embedding)
    VALUES (%s,%s,%s,%s)
    """

    cursor.execute(sql,(
        story_id,
        idx,
        text,
        json.dumps(emb)
    ))

# --------------------------------------------------
# PIPELINE
# --------------------------------------------------

def run():

    stories = extract_story_links()

    print("Stories discovered:",len(stories))

    db = db_connect()
    cursor = db.cursor()

    for story in tqdm(stories):

        paragraphs = download_story(story["url"])

        story_id = insert_story(cursor,story)

        for i,p in enumerate(paragraphs):

            insert_paragraph(cursor,story_id,i,p)

    db.commit()

    cursor.close()
    db.close()

    print("Grimm pipeline complete")

# --------------------------------------------------

if __name__ == "__main__":
    run()
