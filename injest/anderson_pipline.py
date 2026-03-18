import os
import json
import re
from bs4 import BeautifulSoup
import mysql.connector
from tqdm import tqdm
from openai import OpenAI

# --------------------------------------------
# CONFIG
# --------------------------------------------

HTML_FILE = r"C:\Users\Administrator\story_universe_platform\injest\anderson.html"

OPENAI_KEY = os.getenv("OPENAI_API_KEY")


DB = {
    "host":"localhost",
    "user":"rtcwa",
    "password":"!Wdfez69",
    "database":"andersen"
}

client = OpenAI(api_key=OPENAI_KEY)

# --------------------------------------------
# DB
# --------------------------------------------

def db_connect():
    return mysql.connector.connect(**DB)

# --------------------------------------------
# EMBEDDINGS
# --------------------------------------------

def embed(text):

    r = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    return r.data[0].embedding

# --------------------------------------------
# MORAL DETECTION
# --------------------------------------------

def detect_moral(paragraphs):

    for p in paragraphs:

        m = re.search(r"moral[:\.]?\s*(.*)",p,re.IGNORECASE)

        if m:
            return m.group(1)

    return None

# --------------------------------------------
# PARSE HTML
# --------------------------------------------

def parse_html():

    with open(HTML_FILE, encoding="cp1252") as f:
        soup = BeautifulSoup(f,"html.parser")

    stories = []

    anchors = soup.find_all("a", attrs={"name": True})

    for anchor in anchors:

        name = anchor.get("name")

        if not name:
            continue

        h3 = anchor.find_next_sibling("h3")

        if not h3:
            continue

        title = " ".join(h3.get_text(" ", strip=True).split())

        paragraphs = []

        next_anchor = anchor.find_next("a", attrs={"name": True})
        node = h3.next_sibling

        while node is not None and node != next_anchor:

            if getattr(node, "name", None) == "p":
                text = " ".join(node.get_text(" ", strip=True).split())

                if len(text) > 40:
                    paragraphs.append(text)

            node = node.next_sibling

        if len(paragraphs) > 0:

            stories.append({
                "anchor":name,
                "title":title,
                "paragraphs":paragraphs
            })

    return stories

# --------------------------------------------
# INSERT STORY
# --------------------------------------------

def insert_story(cursor,story):

    sql="""
    INSERT INTO stories
    (story_anchor,title,source)
    VALUES(%s,%s,%s)
    """

    cursor.execute(sql,(
        story["anchor"],
        story["title"],
        "Andersen"
    ))

    return cursor.lastrowid

# --------------------------------------------
# INSERT PARAGRAPH
# --------------------------------------------

def insert_paragraph(cursor,story_id,i,text):

    emb = embed(text)

    sql="""
    INSERT INTO paragraphs
    (story_id,paragraph_index,paragraph_text,embedding)
    VALUES(%s,%s,%s,%s)
    """

    cursor.execute(sql,(
        story_id,
        i,
        text,
        json.dumps(emb)
    ))

# --------------------------------------------
# PIPELINE
# --------------------------------------------

def run():

    stories = parse_html()

    print("Stories discovered:",len(stories))

    db = db_connect()
    cursor = db.cursor()

    for story in tqdm(stories):

        story_id = insert_story(cursor,story)

        for i,p in enumerate(story["paragraphs"]):

            insert_paragraph(cursor,story_id,i,p)

    db.commit()

    cursor.close()
    db.close()

    print("Andersen ingestion complete")

# --------------------------------------------

if __name__ == "__main__":
    run()
