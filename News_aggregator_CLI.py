#!/usr/bin/env python3
"""
News Aggregator CLI - A command-line tool to fetch, filter, and export news articles
from multiple sources using NewsAPI.
"""

import argparse
import json
import sqlite3
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import hashlib
import requests
from dataclasses import dataclass, asdict
from openpyxl import Workbook
import os

# Your API key
YOUR_API_KEY = "5a90753eb9a84155a5e4914cb1ac2894"

@dataclass
class Article:
    """Data class for news articles"""
    title: str
    source: str
    author: str
    published_date: str
    description: str
    url: str
    content: str
    category: str
    unique_hash: str

class NewsAggregator:
    def __init__(self, api_key: str = None):
        """
        Initialize the News Aggregator with API key.
        If no API key provided, uses the default one.
        """
        # Use provided API key, or the default one, or try environment variable
        self.api_key = api_key or YOUR_API_KEY or os.getenv('NEWSAPI_KEY')
        if not self.api_key:
            raise ValueError("API key required. Set NEWSAPI_KEY environment variable or pass it directly.")
        
        self.base_url = "https://newsapi.org/v2"
        self.articles: List[Article] = []
        self.db_path = Path.home() / ".news_aggregator" / "news.db"
        self.setup_database()
    
    def setup_database(self):
        """Create database directory and initialize SQLite database"""
        self.db_path.parent.mkdir(exist_ok=True)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                source TEXT,
                author TEXT,
                published_date TEXT,
                description TEXT,
                url TEXT UNIQUE,
                content TEXT,
                category TEXT,
                unique_hash TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"Database initialized at: {self.db_path}")
    
    def generate_hash(self, title: str, source: str, date: str) -> str:
        """Generate unique hash for deduplication"""
        unique_string = f"{title}{source}{date}".encode('utf-8')
        return hashlib.md5(unique_string).hexdigest()
    
    def fetch_news(self, category: str = "general", country: str = "us", 
                   page_size: int = 100, keyword: str = None) -> List[Article]:
        """
        Fetch news articles from NewsAPI
        """
        if keyword:
            endpoint = f"{self.base_url}/everything"
            params = {
                'apiKey': self.api_key,
                'q': keyword,
                'pageSize': min(page_size, 100),
                'sortBy': 'publishedAt',
                'language': 'en'
            }
            print(f"Searching for news about: {keyword}")
        else:
            endpoint = f"{self.base_url}/top-headlines"
            params = {
                'apiKey': self.api_key,
                'country': country,
                'pageSize': min(page_size, 100),
                'category': category
            }
            print(f"Fetching {category} news from {country.upper()}")
        
        try:
            print(f"Making API request to NewsAPI...")
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'ok':
                articles = []
                for item in data['articles']:
                    # Generate unique hash
                    published_date = item['publishedAt'][:10] if item['publishedAt'] else ''
                    unique_hash = self.generate_hash(
                        item['title'] or '',
                        item['source']['name'] or '',
                        published_date
                    )
                    
                    article = Article(
                        title=item['title'] or 'No Title',
                        source=item['source']['name'] or 'Unknown',
                        author=item['author'] or 'Unknown',
                        published_date=published_date,
                        description=item['description'] or 'No description available',
                        url=item['url'] or '',
                        content=item['content'] or 'No content available',
                        category=category,
                        unique_hash=unique_hash
                    )
                    articles.append(article)
                
                print(f"Successfully fetched {len(articles)} articles")
                return articles
            else:
                print(f"API Error: {data.get('message', 'Unknown error')}")
                return []
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching news: {e}")
            return []
    
    def save_to_database(self, articles: List[Article]):
        """Save articles to SQLite database with deduplication"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        saved_count = 0
        duplicate_count = 0
        
        for article in articles:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO articles 
                    (title, source, author, published_date, description, url, content, category, unique_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article.title, article.source, article.author, article.published_date,
                    article.description, article.url, article.content, article.category,
                    article.unique_hash
                ))
                
                if cursor.rowcount > 0:
                    saved_count += 1
                else:
                    duplicate_count += 1
                    
            except sqlite3.IntegrityError:
                duplicate_count += 1
        
        conn.commit()
        conn.close()
        
        print(f"Saved {saved_count} new articles to database ({duplicate_count} duplicates skipped)")
    
    def load_from_database(self, source: str = None, keyword: str = None, 
                          date: str = None, category: str = None) -> List[Article]:
        """Load articles from database with optional filters"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        query = "SELECT title, source, author, published_date, description, url, content, category, unique_hash FROM articles WHERE 1=1"
        params = []
        
        if source:
            query += " AND source LIKE ?"
            params.append(f"%{source}%")
        
        if keyword:
            query += " AND (title LIKE ? OR description LIKE ?)"
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        
        if date:
            query += " AND published_date = ?"
            params.append(date)
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        query += " ORDER BY published_date DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        articles = []
        for row in rows:
            article = Article(
                title=row[0],
                source=row[1],
                author=row[2],
                published_date=row[3],
                description=row[4],
                url=row[5],
                content=row[6],
                category=row[7],
                unique_hash=row[8]
            )
            articles.append(article)
        
        conn.close()
        return articles
    
    def export_to_csv(self, articles: List[Article], filename: str):
        """Export articles to CSV file"""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['title', 'source', 'author', 'published_date', 'description', 
                         'url', 'content', 'category']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for article in articles:
                writer.writerow({
                    'title': article.title,
                    'source': article.source,
                    'author': article.author,
                    'published_date': article.published_date,
                    'description': article.description,
                    'url': article.url,
                    'content': article.content,
                    'category': article.category
                })
        
        print(f"Exported {len(articles)} articles to {filename}")
    
    def export_to_excel(self, articles: List[Article], filename: str):
        """Export articles to Excel file"""
        wb = Workbook()
        ws = wb.active
        ws.title = "News Articles"
        
        # Headers
        headers = ['Title', 'Source', 'Author', 'Published Date', 'Description', 
                  'URL', 'Content', 'Category']
        ws.append(headers)
        
        # Data
        for article in articles:
            ws.append([
                article.title,
                article.source,
                article.author,
                article.published_date,
                article.description,
                article.url,
                article.content,
                article.category
            ])
        
        # Adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        wb.save(filename)
        print(f"Exported {len(articles)} articles to {filename}")
    
    def print_articles(self, articles: List[Article], limit: int = None):
        """Pretty print articles"""
        if limit:
            articles = articles[:limit]
        
        if not articles:
            print("No articles to display")
            return
        
        for i, article in enumerate(articles, 1):
            print(f"\n{'='*80}")
            print(f"{i}. {article.title}")
            print(f"   Source: {article.source} | Author: {article.author} | Date: {article.published_date}")
            print(f"   Category: {article.category}")
            desc = article.description[:100] + "..." if len(article.description) > 100 else article.description
            print(f"   Description: {desc}")
            print(f"   URL: {article.url}")
        print(f"\n{'='*80}")
        print(f"Total: {len(articles)} articles")

def main():
    parser = argparse.ArgumentParser(description='News Aggregator CLI')
    parser.add_argument('--api-key', help='NewsAPI API key (optional, default key is used if not provided)')
    
    # Fetch commands
    parser.add_argument('--fetch', action='store_true', help='Fetch latest news')
    parser.add_argument('--category', default='general', help='News category (general, business, technology, entertainment, health, science, sports)')
    parser.add_argument('--country', default='us', help='Country code (us, gb, ca, au, etc.)')
    parser.add_argument('--keyword', help='Search keyword')
    parser.add_argument('--page-size', type=int, default=20, help='Number of articles to fetch (max 100)')
    
    # Filter commands
    parser.add_argument('--list', action='store_true', help='List articles from database')
    parser.add_argument('--source', help='Filter by source name')
    parser.add_argument('--filter-keyword', help='Filter by keyword in title/description')
    parser.add_argument('--date', help='Filter by date (YYYY-MM-DD)')
    parser.add_argument('--filter-category', help='Filter by category')
    
    # Export commands
    parser.add_argument('--export-csv', metavar='FILENAME', help='Export to CSV file')
    parser.add_argument('--export-excel', metavar='FILENAME', help='Export to Excel file')
    
    # Display options
    parser.add_argument('--limit', type=int, help='Limit number of articles displayed')
    
    args = parser.parse_args()
    
    try:
        # Initialize aggregator with your API key
        print("Initializing News Aggregator...")
        aggregator = NewsAggregator(api_key=args.api_key)
        
        # Fetch news
        if args.fetch:
            articles = aggregator.fetch_news(
                category=args.category,
                country=args.country,
                page_size=args.page_size,
                keyword=args.keyword
            )
            
            if articles:
                aggregator.save_to_database(articles)
                print("\nLatest Articles:")
                aggregator.print_articles(articles, limit=args.limit)
            else:
                print("No articles fetched")
        
        # List articles from database
        if args.list:
            articles = aggregator.load_from_database(
                source=args.source,
                keyword=args.filter_keyword,
                date=args.date,
                category=args.filter_category
            )
            
            if articles:
                print(f"\nFound {len(articles)} articles matching criteria:")
                aggregator.print_articles(articles, limit=args.limit)
            else:
                print("No articles found matching the criteria")
        
        # Export to CSV
        if args.export_csv:
            articles = aggregator.load_from_database(
                source=args.source,
                keyword=args.filter_keyword,
                date=args.date,
                category=args.filter_category
            )
            
            if articles:
                aggregator.export_to_csv(articles, args.export_csv)
            else:
                print("No articles to export")
        
        # Export to Excel
        if args.export_excel:
            articles = aggregator.load_from_database(
                source=args.source,
                keyword=args.filter_keyword,
                date=args.date,
                category=args.filter_category
            )
            
            if articles:
                aggregator.export_to_excel(articles, args.export_excel)
            else:
                print("No articles to export")
        
        # If no arguments provided, show help
        if not any([args.fetch, args.list, args.export_csv, args.export_excel]):
            parser.print_help()
            print("\nExample usage:")
            print("  python news_aggregator.py --fetch --category technology --limit 5")
            print("  python news_aggregator.py --list --source 'BBC' --export-csv news.csv")
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())