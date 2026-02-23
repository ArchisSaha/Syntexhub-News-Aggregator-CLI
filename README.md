# News Aggregator CLI

A command-line tool to fetch, filter, and export news articles from multiple sources using NewsAPI.

## Features
- Fetch latest news from multiple categories (technology, business, sports, etc.)
- Search by keywords
- Filter articles by source, keyword, date, and category
- Store articles in SQLite database for later queries
- Export to CSV and Excel formats
- Automatic deduplication to avoid duplicate articles

## Installation

1. Clone the repository:
`bash
git clone https://github.com/YOUR_USERNAME/news-aggregator-cli.git
cd news-aggregator-cli

2. Install required packages:

-pip install requests openpyxl

3. Get a free API key from NewsAPI.org

Usage Examples

1. Fetch News

# Fetch technology news
python News_aggregator_CLI.py --fetch --category technology --limit 5

# Fetch business news
python News_aggregator_CLI.py --fetch --category business --limit 5

# Search for specific topics
python News_aggregator_CLI.py --fetch --keyword "artificial intelligence"

2. list and Filter Articles

# List all saved articles
python News_aggregator_CLI.py --list

# Filter by source
python News_aggregator_CLI.py --list --source "BBC"

# Filter by date
python News_aggregator_CLI.py --list --date "2024-01-15"

Export Articles

# Export to CSV
python News_aggregator_CLI.py --list --export-csv news.csv

# Export to Excel
python News_aggregator_CLI.py --list --export-excel news.xlsx

# Export filtered articles
python News_aggregator_CLI.py --list --source "TechCrunch" --export-excel techcrunch_news.xlsx

Command Line Arguments

Argument	                                Description

--fetch	                                  Fetch latest news
--category	                              News category (general, business, technology, entertainment, health, science, sports)
--country	                                Country code (us, gb, ca, au, etc.)
--keyword	                                Search keyword
--page-size	                              Number of articles to fetch (max 100)
--list	                                  List articles from database
--source	                                Filter by source name
--filter-keyword	                        Filter by keyword in title/description
--date	                                  Filter by date (YYYY-MM-DD)
--filter-category	                        Filter by category
--export-csv	                            Export to CSV file
--export-excel	                          Export to Excel file
--limit	Limit                             number of articles displayed


Project Structure:

news-aggregator-cli/
├── News_aggregator_CLI.py  # Main script
├── requirements.txt        # Python dependencies
├── README.md              # Documentation
└── .gitignore             # Git ignore file

Database:

Articles are automatically saved to SQLite database at:

1. Windows: C:\Users\[Username]\.news_aggregator\news.db
2. Linux/Mac: ~/.news_aggregator/news.db

Requirements:

1. Python 3.6 or higher
2. requests library
3. openpyxl library
