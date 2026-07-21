"""
News Sentiment Analysis Module
==============================
Събира новини за компанията и анализира sentiment-а.

Източници:
- Google News RSS (безплатен, без API key)

Метод:
- Keyword-based sentiment scoring
- Bullish/Bearish/Neutral класификация
"""

import re
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json


# Sentiment речници - клавиши за пазарен sentiment
BULLISH_WORDS = {
    # Strong bullish
    'surge', 'soar', 'rally', 'boom', 'breakout', 'record high', 'all-time high',
    'upgrade', 'outperform', 'buy', 'strong buy', 'bullish', 'beat', 'beats',
    'exceeded', 'exceeds', 'profit', 'growth', 'revenue', 'innovation',
    # Moderate bullish
    'rise', 'gain', 'up', 'higher', 'positive', 'optimistic', 'recovery',
    'partnership', 'expansion', 'launch', 'approval', 'deal', 'contract',
    'dividend', 'buyback', 'boost', 'momentum', 'strength', 'demand',
}

BEARISH_WORDS = {
    # Strong bearish
    'crash', 'plunge', 'collapse', 'tumble', 'slump', 'sell-off', 'panic',
    'downgrade', 'underperform', 'sell', 'bearish', 'miss', 'misses',
    'lawsuit', 'fraud', 'investigation', 'ban', 'recall', 'bankruptcy',
    # Moderate bearish
    'fall', 'drop', 'decline', 'down', 'lower', 'negative', 'concern',
    'risk', 'loss', 'debt', 'warning', 'cut', 'reduction', 'layoff',
    'competition', 'threat', 'slowdown', 'inflation', 'recession', 'tariff',
}


def fetch_news(ticker: str, company_name: str = '', max_results: int = 20) -> List[Dict]:
    """
    Събира новини от Google News RSS.

    Параметри:
    ----------
    ticker : str
        Тикер на компанията
    company_name : str
        Име на компанията (за по-добро търсене)
    max_results : int
        Максимален брой новини

    Връща:
    -------
    List[Dict]
        Списък с новини (title, source, date, url)
    """
    try:
        search_query = f"{ticker} stock"
        if company_name:
            search_query = f"{company_name} stock"

        # Google News RSS feed (URL-encoded)
        encoded_query = urllib.parse.quote(search_query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"

        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read().decode('utf-8')

        # Parse RSS
        root = ET.fromstring(xml_data)
        items = root.findall('.//item')[:max_results]

        news = []
        for item in items:
            title = item.find('title')
            source = item.find('source')
            pub_date = item.find('pubDate')
            link = item.find('link')

            news.append({
                'title': title.text if title is not None else '',
                'source': source.text if source is not None else '',
                'date': pub_date.text if pub_date is not None else '',
                'url': link.text if link is not None else ''
            })

        return news

    except Exception as e:
        print(f"Warning: Could not fetch news for {ticker}: {e}")
        return []


def analyze_sentiment(text: str) -> Dict:
    """
    Анализира sentiment на един текст.

    Връща:
    -------
    Dict
        score (-1 до 1), label (bullish/bearish/neutral), confidence
    """
    text_lower = text.lower()
    words = set(re.findall(r'\b\w+\b', text_lower))

    # Also check multi-word phrases
    bullish_count = 0
    bearish_count = 0

    for phrase in BULLISH_WORDS:
        if ' ' in phrase:
            if phrase in text_lower:
                bullish_count += 2  # Multi-word phrases get more weight
        elif phrase in words:
            bullish_count += 1

    for phrase in BEARISH_WORDS:
        if ' ' in phrase:
            if phrase in text_lower:
                bearish_count += 2
        elif phrase in words:
            bearish_count += 1

    total = bullish_count + bearish_count

    if total == 0:
        return {'score': 0, 'label': 'neutral', 'confidence': 0}

    score = (bullish_count - bearish_count) / max(total, 1)
    confidence = min(total / 5, 1.0) * 100  # Normalize to 0-100

    if score > 0.15:
        label = 'bullish'
    elif score < -0.15:
        label = 'bearish'
    else:
        label = 'neutral'

    return {
        'score': round(score, 3),
        'label': label,
        'confidence': round(confidence, 1)
    }


def get_news_sentiment(ticker: str, company_name: str = '') -> Dict:
    """
    Получава и анализира sentiment от новини за компанията.

    Връща:
    -------
    Dict
        overall sentiment, individual articles, breakdown
    """
    news = fetch_news(ticker, company_name, max_results=15)

    if not news:
        return {
            'overall': 'neutral',
            'score': 0,
            'confidence': 0,
            'article_count': 0,
            'articles': [],
            'bullish_count': 0,
            'bearish_count': 0,
            'neutral_count': 0
        }

    # Analyze each article
    articles = []
    bullish = 0
    bearish = 0
    neutral = 0
    total_score = 0

    for article in news:
        sentiment = analyze_sentiment(article['title'])
        articles.append({
            'title': article['title'],
            'source': article['source'],
            'date': article['date'],
            'sentiment': sentiment['label'],
            'score': sentiment['score']
        })

        total_score += sentiment['score']
        if sentiment['label'] == 'bullish':
            bullish += 1
        elif sentiment['label'] == 'bearish':
            bearish += 1
        else:
            neutral += 1

    # Overall sentiment
    avg_score = total_score / len(news) if news else 0

    if avg_score > 0.1:
        overall = 'bullish'
    elif avg_score < -0.1:
        overall = 'bearish'
    else:
        overall = 'neutral'

    # Confidence based on agreement between articles
    total = len(news)
    max_agreement = max(bullish, bearish, neutral) / total if total > 0 else 0
    confidence = max_agreement * 100

    return {
        'overall': overall,
        'score': round(avg_score, 3),
        'confidence': round(confidence, 1),
        'article_count': len(news),
        'articles': articles[:10],  # Top 10
        'bullish_count': bullish,
        'bearish_count': bearish,
        'neutral_count': neutral
    }
