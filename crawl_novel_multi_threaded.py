import os
import re
import time
import random
import pymongo
import requests
import unidecode
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from rich.panel import Panel
from rich.console import Console
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn, MofNCompleteColumn

load_dotenv('.env')

clerkId = "user_2dbbs9Wcnrb2PXFWIgvCB4kgi9u"
max_workers = 10  # Number of threads
max_retries = 3  # Maximum retries
retry_delay = 5  # Delay between retries (in seconds)

# MongoDB connection setup
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI is not set in the environment variables.")

client = pymongo.MongoClient(MONGO_URI)
db = client['read_novel_v3']
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
# Remove special characters and replace spaces with hyphens
def generate_slug(novel_name):
    slug = unidecode.unidecode(novel_name)  # Normalize Vietnamese characters
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    return slug.lower()

def extract_chapter_title(full_title):
    chapter_title = full_title.split(":")[-1].strip()
    return chapter_title.strip()

def crawl_chapter(chapter_index, chapter_url, novel_slug, progress, task_id):
    for attempt in range(max_retries):
        try:
            chapter_response = requests.get(chapter_url)
            chapter_response.raise_for_status()

            chapter_soup = BeautifulSoup(chapter_response.content, 'html.parser')

            full_title = chapter_soup.find('a', class_="chapter-title", title=True)
            if not full_title:
                continue

            chapter_title = extract_chapter_title(full_title.get_text())
            chapter_content = chapter_soup.find('div', class_='chapter-c')

            if chapter_content:
                first_div = chapter_content.find('div')
                if first_div:
                    first_div.decompose()

                str_content = str(chapter_content).replace("div", "p")

                current_time = datetime.now(timezone.utc)
                chapter_data = {
                    "novelSlug": novel_slug,
                    "chapterName": chapter_title,
                    "chapterIndex": chapter_index,
                    "content": str_content,
                    "state": "đã duyệt",
                    "isApprove": True,
                    "isLock": False,
                    "isPublic": True,
                    "publishedDate": None,
                    "createdAt": current_time,
                    "updatedAt": current_time,
                }

                chapters_collection.insert_one(chapter_data)
                # Update progress
                progress.update(task_id, advance=1)
                break

            else:
                time.sleep(retry_delay)

        except requests.exceptions.RequestException:
            time.sleep(retry_delay)

def crawl_novel(url, total_chapters):
    console = Console()
    console.print(f"[bold cyan]Starting crawl for URL:[/bold cyan] {url}")
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    novel_name = soup.find('h3', class_='title').text.strip()
    author = soup.find('a', itemprop='author').text.strip()
    url_cover = soup.find('img', itemprop='image')['src'].strip()
    description = soup.find('div', itemprop='description')

    # Create novel slug
    novel_slug = generate_slug(novel_name)

    # Randomly select 2 to 4 genres
    selected_genres = random.sample(novel_genres, random.randint(2, 4))

    # Insert the novel data into the novels collection
    current_time = datetime.now(timezone.utc)
    novel_data = {
        "novelName": novel_name,
        "novelSlug": novel_slug,
        "author": author,
        "genres": selected_genres,
        "tags": [],
        "urlCover": url_cover,
        "uploader": clerkId,
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

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        # TextColumn("[progress.completed] {task.completed}/{task.total} chương"),
        TimeRemainingColumn(),
    ) as progress:
        console.print(Panel(f"[bold green]{novel_name}[/bold green] - [bold blue]{author}[/bold blue] - [bold yellow]{total_chapters}[/bold yellow] chương"))
        task_id = progress.add_task("[cyan]Crawling novel chapters...", total=total_chapters)

        novels_collection.insert_one(novel_data)

        # Concurrently crawl and insert chapters
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for chapter_index in range(1, total_chapters + 1):
                chapter_url = f"{url}chuong-{chapter_index}/"
                executor.submit(crawl_chapter, chapter_index, chapter_url, novel_slug, progress, task_id)

copyright_text = Text("Bản quyền thuộc về Hoan Cu Te", style="bold blue")
fb_link = Text("https://www.facebook.com/hoanit02/", style="link")
console = Console()
console.print(Panel(Text.assemble(copyright_text, " - ", fb_link), title="Thông tin liên hệ", expand=False))

with open("novel_data.txt", "r") as file:
    for line in file:
        line = line.strip()
        if line:
            url, total_chapters = line.split(" ")
            crawl_novel(url, int(total_chapters))

print("Finished processing all novels in the file.")
