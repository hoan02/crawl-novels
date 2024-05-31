# Novel Crawler


This project is a web crawler designed to collect novels and their chapters from the website truyenfull.vn. The collected data is then stored in a MongoDB database for use in the development of the online novel reading platform doctruyen.io.vn.

## Prerequisites

- Python 3.7+
- MongoDB
- Required Python packages (see below)

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/novel-crawler.git
   cd novel-crawler
   ```
2. Create a virtual environment and activate it:

    ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows use `venv\Scripts\activate`
   ```
3. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```
4. Create a .env file in the project root directory and add your MongoDB URI:

   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows use `venv\Scripts\activate`
   ```
5. Create a novel_data.txt file in the project root directory and add the URLs and total chapters of the novels to crawl:

   ```bash
   url_1 total_chapters_1
   url_2 total_chapters_2
   ```
## Usage
Run the crawler:
  ```bash
  python crawl_novel_multi_threaded.py     # Or crawl_novel_single_threaded.py
  ```
## License
This project is licensed under the MIT License. See the LICENSE file for more details.

## Copyright
Copyright © 2024 Hoan Cu Te

## Contact
Facebook: [Lê Công Hoan](https://www.facebook.com/hoanit02/)

