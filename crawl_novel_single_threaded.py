import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import pymongo
import re
import random
import unidecode
from datetime import datetime, timezone

load_dotenv('.env')

# MongoDB connection setup
MONGO_URI = os.getenv("MONGO_URI")
client = pymongo.MongoClient(MONGO_URI)
db = client['read_novel_v2']
novels_collection = db['novels']
chapters_collection = db['chapters']

# List of available genres
novel_genres = [
    {"label": "Kiếm hiệp", "value": "kiem-hiep"},
    {"label": "Huyền Huyễn", "value": "huyen-huyen"},
    {"label": "Võng Du", "value": "vong-du"},
    {"label": "Đồng Nhân", "value": "dong-nhan"},
    {"label": "Cạnh Kỹ", "value": "canh-ky"},
    {"label": "Tiên Hiệp", "value": "tien-hiep"},
    {"label": "Kỳ Ảo", "value": "ky-ao"},
    {"label": "Khoa Huyễn", "value": "khoa-huyen"},
    {"label": "Đô thị", "value": "do-thi"},
    {"label": "Đã sử", "value": "da-su"},
    {"label": "Huyền Nghi", "value": "huyen-nghi"},
]

# Function to generate slug from novel name
def generate_slug(novel_name):
    # Normalize Vietnamese characters
    slug = unidecode.unidecode(novel_name)
    # Remove special characters and replace spaces with hyphens
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    return slug.lower()

def extract_chapter_title(full_title):
    chapter_title = full_title.split(":")[-1].strip()
    return chapter_title.strip()

def crawl_novel(url, total_chapters):
    print("Starting crawl for URL:", url)
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    novel_name = soup.find('h3', class_='title').text.strip()
    print("Story title:", novel_name)
    author = soup.find('a', itemprop='author').text.strip()
    print("Author:", author)
    url_cover = soup.find('img', itemprop='image')['src'].strip()
    description = soup.find('div', itemprop='description')
    print("Description and cover URL fetched.")
    
    # Create novel slug
    novel_slug = generate_slug(novel_name)
    print("Generated novel slug:", novel_slug)

    # Randomly select 2 to 4 genres
    selected_genres = random.sample(novel_genres, random.randint(2, 4))
    print("Selected genres:", selected_genres)

    # Insert the novel data into the novels collection
    current_time = datetime.now(timezone.utc)
    novel_data = {
        "novelName": novel_name,
        "novelSlug": novel_slug,
        "author": author,
        "genres": selected_genres,
        "tags": [],
        "urlCover": url_cover,
        "uploader": "user_2dbbs9Wcnrb2PXFWIgvCB4kgi9u",
        "description": str(description),
        "shortDescription": "",
        "reviews": {
            "count": 0,
            "avgScore": 0,
            "avgScoreCharacter": 0,
            "avgScorePlot": 0,
            "avgScoreWorld": 0,
            "totalScoreCharacter": 0,
            "totalScorePlot": 0,
            "totalScoreWorld": 0,
        },
        "nominationCount": 0,
        "readCount": 0,
        "chapterCount": total_chapters,
        "commentCount": 0,
        "state": "Đang ra",
        "isLock": False,
        "isPublic": True,
        "publishedDate": None,
        "createdAt": current_time,
        "updatedAt": current_time,
    }
    novels_collection.insert_one(novel_data)
    print("Novel data inserted into MongoDB.")

    # Insert each chapter's data into the chapters collection
    for chapter_index in range(1, total_chapters + 1):
        chapter_url = f"{url}chuong-{chapter_index}/"
        chapter_response = requests.get(chapter_url)
        chapter_soup = BeautifulSoup(chapter_response.content, 'html.parser')
        
        # Extract the chapter title
        full_title = chapter_soup.find('a', class_="chapter-title", title=True).get_text()
        chapter_title = extract_chapter_title(full_title)  
        chapter_content = chapter_soup.find('div', class_='chapter-c')

        current_time = datetime.now(timezone.utc)
        chapter_data = {
            "novelSlug": novel_slug,
            "chapterName": chapter_title,
            "chapterIndex": chapter_index,
            "content": str(chapter_content),
            "state": "đã duyệt",
            "isApprove": True,
            "isLock": False,
            "isPublic": True,
            "publishedDate": None,
            "createdAt": current_time,
            "updatedAt": current_time,
        }
        chapters_collection.insert_one(chapter_data)
        print(f"Inserted chapter {chapter_index}: {chapter_title}")

    print("Finished inserting all chapters.")

# Đọc url và total_chapters từ tệp văn bản
with open("novel_data.txt", "r") as file:
    for line in file:
        url, total_chapters = line.strip().split(" ")
        crawl_novel(url, int(total_chapters))

print("Data has been inserted into MongoDB.")
