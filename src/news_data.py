"""
News Data Module (point-in-time)
=================================
Събира новини за компанията и ги подготвя за ТРЕНИРОВЪЧНИЯ pipeline —
за разлика от sentiment.py (който остава недокоснат и продължава да
обслужва живия UI), тук всяка статия пази точен timestamp на наличност
(available_at) и минава през dedup, преди да влезе в агрегатни features.

Източник: Google News RSS (същият безплатен feed като sentiment.py, без
API ключ) — проверено на живо, че поддържа историческо търсене по дата
(`after:`/`before:` в заявката).

КРИТИЧНО ограничение, проверено на живо: за исторически резултати
(търсене с after:/before:) Google връща само ДАТА, не точен час — 5
различни статии от един ден се появиха с ИДЕНТИЧЕН pubDate. За живи
заявки (без date filter) часът е реален. Затова:

- Историческа (backfill) статия: available_at = ден(pubDate) + 1, 00:00
  UTC — пълен еднодневен embargo, защото не можем да се доверим на часа.
- Жива статия (текущ fetch, без date filter): available_at = реалния
  parsed pubDate — точен до минутата.
"""

import os
import re
import json
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import List, Dict, Optional

import numpy as np
import pandas as pd

import sentiment as _sentiment  # reuse съществуващия keyword-heuristic sentiment

_NEWS_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'news')
_RAW_DIR = os.path.join(_NEWS_DIR, 'raw')

_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'


# ---------------------------------------------------------------- fetch

def _rss_query(query: str, max_results: int = 40, timeout: int = 15) -> List[Dict]:
    """Единична RSS заявка към Google News. Не гърми при мрежова грешка."""
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=en-US&gl=US&ceid=US:en"
    req = urllib.request.Request(url, headers={'User-Agent': _USER_AGENT})

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            xml_data = response.read().decode('utf-8')
    except Exception as e:
        print(f"[NEWS][WARN] RSS заявка неуспешна: {e}")
        return []

    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        print(f"[NEWS][WARN] Невалиден RSS отговор: {e}")
        return []

    items = root.findall('.//item')[:max_results]
    out = []
    for item in items:
        title = item.find('title')
        source = item.find('source')
        pub_date = item.find('pubDate')
        link = item.find('link')
        out.append({
            'title': title.text if title is not None else '',
            'source': source.text if source is not None else '',
            'raw_pub_date': pub_date.text if pub_date is not None else '',
            'url': link.text if link is not None else '',
        })
    return out


def parse_pub_date(raw: str) -> Optional[datetime]:
    """
    Парсва RFC-822 pubDate стринг (напр. 'Tue, 02 Jan 2024 08:00:00 GMT')
    в tz-aware UTC datetime. Лош/непознат формат -> None, никога изключение
    — една невалидна статия не бива да съборя целия backfill.
    """
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def fetch_live_news(ticker: str, company_name: str = '', max_results: int = 20) -> List[Dict]:
    """
    Текущи новини (без date filter) — pubDate-ите тук са реални, с час.
    available_at = реалния parsed timestamp.
    """
    query = f"{company_name} stock" if company_name else f"{ticker} stock"
    raw = _rss_query(query, max_results=max_results)

    articles = []
    for a in raw:
        parsed = parse_pub_date(a['raw_pub_date'])
        articles.append({
            **a,
            'ticker': ticker.upper(),
            'available_at': parsed,
            'is_historical': False,
        })
    return articles


def fetch_historical_news(ticker: str, company_name: str, start_date: datetime,
                          end_date: datetime, chunk_days: int = 7,
                          min_request_interval: float = 1.2,
                          max_results_per_chunk: int = 40) -> List[Dict]:
    """
    Historical backfill чрез Google News RSS-ия after:/before: синтаксис.

    Разделя диапазона на chunk-ове (по подразбиране седмица), за да не
    пропуска статии в натоварени седмици (RSS връща ограничен брой
    резултати на заявка) и да не удря rate limit с прекалено широки
    заявки. Между заявките спазва min_request_interval пауза — Google
    News RSS показа нестабилност (timeout) при бързи последователни
    заявки при проверка на живо.

    available_at = ден(pubDate) + 1 ден, 00:00 UTC (виж модулния
    docstring защо — часът в историческите резултати не е надежден).
    """
    query_base = company_name or ticker
    articles = []

    current = start_date
    while current < end_date:
        chunk_end = min(current + timedelta(days=chunk_days), end_date)
        query = (f"{query_base} stock after:{current.strftime('%Y-%m-%d')} "
                 f"before:{chunk_end.strftime('%Y-%m-%d')}")

        print(f"[NEWS] Backfill {ticker}: {current.date()} -> {chunk_end.date()}...")

        raw = []
        for attempt in range(3):
            raw = _rss_query(query, max_results=max_results_per_chunk)
            if raw:
                break
            time.sleep(min_request_interval * (attempt + 1))

        for a in raw:
            parsed = parse_pub_date(a['raw_pub_date'])
            if parsed is None:
                continue
            embargo_start = datetime(parsed.year, parsed.month, parsed.day, tzinfo=timezone.utc) \
                + timedelta(days=1)
            articles.append({
                **a,
                'ticker': ticker.upper(),
                'available_at': embargo_start,
                'is_historical': True,
            })

        current = chunk_end
        time.sleep(min_request_interval)

    print(f"[NEWS] Backfill за {ticker}: {len(articles)} статии (преди dedup)")
    return articles


# ---------------------------------------------------------------- dedup

def _normalize_title(title: str) -> str:
    t = title.lower().strip()
    t = re.sub(r'[^\w\s]', '', t)
    t = re.sub(r'\s+', ' ', t)
    return t


def deduplicate_articles(articles: List[Dict]) -> List[Dict]:
    """
    Премахва копия на една и съща новина от различни източници.

    Ключ: точен URL (ако е наличен) ИЛИ (нормализирано заглавие, source).
    При дубликат пази статията с НАЙ-РАННИЯ available_at — това е
    реалният момент, в който новината за пръв път е станала публична;
    по-късните копия (re-publish от друг сайт) не са нова информация.
    """
    by_key: Dict[str, Dict] = {}

    for a in articles:
        url = (a.get('url') or '').strip()
        title_key = _normalize_title(a.get('title', ''))
        key = url if url else f"{title_key}|{a.get('source', '')}"

        existing = by_key.get(key)
        if existing is None:
            by_key[key] = a
            continue

        a_time = a.get('available_at')
        e_time = existing.get('available_at')
        if a_time is not None and (e_time is None or a_time < e_time):
            by_key[key] = a

    # Допълнителен пас: заглавие+source еднакви дори при различен URL
    # (напр. синдикирана статия, препубликувана с ?utm параметри)
    seen_titles: Dict[str, Dict] = {}
    result = []
    for a in by_key.values():
        title_key = _normalize_title(a.get('title', ''))
        tkey = f"{title_key}|{a.get('source', '')}"
        existing = seen_titles.get(tkey)
        if existing is None:
            seen_titles[tkey] = a
            result.append(a)
        else:
            a_time = a.get('available_at')
            e_time = existing.get('available_at')
            if a_time is not None and (e_time is None or a_time < e_time):
                idx = result.index(existing)
                result[idx] = a
                seen_titles[tkey] = a

    return result


# ---------------------------------------------------------------- sentiment + persistence

def enrich_with_sentiment(articles: List[Dict]) -> List[Dict]:
    """Добавя sentiment_score/sentiment_label към всяка статия (по заглавие)."""
    out = []
    for a in articles:
        s = _sentiment.analyze_sentiment(a.get('title', ''))
        out.append({**a, 'sentiment_score': s['score'], 'sentiment_label': s['label'],
                    'sentiment_confidence': s['confidence']})
    return out


def save_articles(ticker: str, articles: List[Dict]):
    """Append-ва статии в data/news/raw/{ticker}.jsonl (raw кеш, не се презаписва)."""
    os.makedirs(_RAW_DIR, exist_ok=True)
    path = os.path.join(_RAW_DIR, f'{ticker.upper()}.jsonl')

    with open(path, 'a', encoding='utf-8') as f:
        for a in articles:
            row = dict(a)
            if isinstance(row.get('available_at'), datetime):
                row['available_at'] = row['available_at'].isoformat()
            f.write(json.dumps(row, ensure_ascii=False) + '\n')

    print(f"[NEWS] Записани {len(articles)} статии в {path}")


def load_cached_articles(ticker: str) -> List[Dict]:
    """Зарежда raw кеша, дедупликирайки автоматично (append могат да съдържат copies)."""
    path = os.path.join(_RAW_DIR, f'{ticker.upper()}.jsonl')
    if not os.path.exists(path):
        return []

    articles = []
    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                print(f"[NEWS][WARN] Невалиден JSON ред {line_num} в {path}, пропускам")
                continue
            if row.get('available_at'):
                try:
                    row['available_at'] = datetime.fromisoformat(row['available_at'])
                except ValueError:
                    row['available_at'] = None
            articles.append(row)

    return deduplicate_articles(articles)


# ---------------------------------------------------------------- aggregated features

NEWS_FEATURE_WINDOWS_HOURS = (1, 6, 24)

NEWS_FEATURE_COLUMNS = (
    [f'news_count_{w}h' for w in NEWS_FEATURE_WINDOWS_HOURS]
    + ['positive_news_count_24h', 'negative_news_count_24h', 'neutral_news_count_24h']
    + [f'avg_sentiment_{w}h' for w in NEWS_FEATURE_WINDOWS_HOURS]
    + ['sentiment_std_24h', 'positive_negative_ratio']
)


def compute_news_features(articles: List[Dict], target_timestamps) -> pd.DataFrame:
    """
    Агрегирани rolling news features за всеки target timestamp.

    За timestamp t използва САМО статии с available_at <= t (и > t -
    window за съответния прозорец) — никога статия от бъдещето спрямо t.
    Прозорецът е полуотворен (t-window, t] — статия ТОЧНО на t-window
    границата се брои за предходния прозорец, не за текущия. Това е
    умишлено консервативно (изключва граничен случай), не бъг.

    Параметри:
    ----------
    articles : list[dict]
        Всяка статия трябва да има 'available_at' (datetime),
        'sentiment_score' (float), 'sentiment_label' (str). Статии без
        available_at (неуспешно parse-нат timestamp) се игнорират — по-
        добре по-малко данни, отколкото грешно позиционирана статия.
    target_timestamps : iterable
        Моментите, за които се смятат features (обикновено краят на
        всеки ден от цената на акцията).

    Връща:
    -------
    pandas.DataFrame
        Колона 'timestamp' + NEWS_FEATURE_COLUMNS. Дни без новини
        получават 0 за count-овете и 0.0 (неутрално) за sentiment-а —
        семантично коректно, не "случайно 0 за всичко".
    """
    targets = pd.to_datetime(pd.Series(list(target_timestamps)), utc=True)

    valid = [a for a in articles if a.get('available_at') is not None]
    if not valid:
        out = pd.DataFrame({'timestamp': targets})
        for c in NEWS_FEATURE_COLUMNS:
            out[c] = 0.0
        return out

    df = pd.DataFrame(valid).sort_values('available_at').reset_index(drop=True)
    avail = pd.to_datetime(df['available_at'], utc=True).values.astype('datetime64[ns]')
    scores = df['sentiment_score'].astype(float).values
    labels = df['sentiment_label'].values

    t_arr = targets.values.astype('datetime64[ns]')

    results = {c: [] for c in NEWS_FEATURE_COLUMNS}

    for t in t_arr:
        end_idx = np.searchsorted(avail, t, side='right')

        for w in NEWS_FEATURE_WINDOWS_HOURS:
            start_t = t - np.timedelta64(w, 'h')
            start_idx = np.searchsorted(avail, start_t, side='right')
            window_scores = scores[start_idx:end_idx]

            results[f'news_count_{w}h'].append(len(window_scores))
            results[f'avg_sentiment_{w}h'].append(
                float(window_scores.mean()) if len(window_scores) else 0.0
            )

            if w == 24:
                window_labels = labels[start_idx:end_idx]
                # bullish/bearish/neutral (речникa на sentiment.py) -> positive/negative/neutral
                pos = int((window_labels == 'bullish').sum())
                neg = int((window_labels == 'bearish').sum())
                neu = int((window_labels == 'neutral').sum())
                results['positive_news_count_24h'].append(pos)
                results['negative_news_count_24h'].append(neg)
                results['neutral_news_count_24h'].append(neu)
                results['sentiment_std_24h'].append(
                    float(window_scores.std()) if len(window_scores) > 1 else 0.0
                )
                results['positive_negative_ratio'].append(
                    (pos / neg) if neg > 0 else float(pos)
                )

    out = pd.DataFrame({'timestamp': targets})
    for c, values in results.items():
        out[c] = values
    return out


if __name__ == "__main__":
    print("[START] Тестване на News Data Module\n")

    live = fetch_live_news('AAPL', 'Apple')
    live = enrich_with_sentiment(live)
    print(f"[NEWS] Живи статии: {len(live)}")
    for a in live[:3]:
        print(f"  - [{a['sentiment_label']}] {a['title'][:70]}  ({a['available_at']})")

    deduped = deduplicate_articles(live)
    print(f"[NEWS] След dedup: {len(deduped)}")
