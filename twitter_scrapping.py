import asyncio
import csv
import random
import time
import unicodedata
from datetime import datetime, timedelta
from datetime import datetime, timezone
from twikit import Client, TooManyRequests
import httpx
import math
# ================== CONFIG ==================
# QUERIES= [
#     "2024 election", "2024 US election", "2024 presidential election", "2024 elections", "presidential race 2024",
#     "election2024", "#Election2024", "#USElections", "Election Day 2024", "Vote2024", "#VoteBlue", "#VoteRed",
#     "Blue wave", "Red wave"
# ]

# QUERIES= [
#     "Biden", "Joe Biden", "President Biden", "Sleepy Joe", "@JoeBiden", "Uncle Joe", "Joey B","Trump", "Donald Trump", "President Trump", "The Donald", "Donnie", "Drumpf", "Orange Man", "@realDonaldTrump",
#     "#Trump2024", "#VoteTrump", "#MAGA", "#SaveAmerica"
# ]
# QUERIES=['Kamala Harris',"Trump","Democrat","Republican"]
# QUERIES= [
#     "Kamala", "Kamala Harris", "Vice President Harris", "@KamalaHarris", "VP Harris", "Madam VP","RFK", "RFK Jr", "Robert Kennedy Jr", "@RobertKennedyJr", "Bobby Kennedy", "Robert F. Kennedy Jr.", 
#     "#RFKJr", "#VoteRFK"
# ]
# QUERIES=['Democrat','Biden','Kamala Harris','Tim Walz']
QUERIES=['Republican','Trump','JD Vance','Vivek Ramaswamy']
# QUERIES= [
#     "Nikki Haley", "Haley", "@NikkiHaley", "Ambassador Haley", "#Haley2024","Vivek Ramaswamy", "Vivek", "@VivekGRamaswamy", "Mr. Ramaswamy", "#Vivek2024","Ron DeSantis", "DeSantis", "@RonDeSantis", "Ron D", "Governor Ron", "Gov. DeSantis", "#DeSantis2024"
# ]
# QUERIES = [
#     "Cornel West", "@CornelWest", "Dr. Cornel West", "Professor West", "#CornelWest2024","Mike Pence", "Pence", "@Mike_Pence", "VP Pence", "Vice President Pence"
# ]
# QUERIES= [
#     "Chris Christie", "@GovChristie", "Governor Christie",
#     "Marianne Williamson", "@marwilliamson", "Ms. Williamson",
#     "Tim Scott", "@SenatorTimScott", "Sen. Scott", "Timothy Scott",
#     "Asa Hutchinson", "@AsaHutchinson", "Governor Hutchinson",
#     "Doug Burgum", "@DougBurgum", "Governor Burgum"
# ]
# QUERIES= [
#     "Senator", "sen.", "Sen", "sen", "Sen.", "senator", "SENATOR",
#     "Governor", "Gov.", "Gov", "gov", "GOV", "governor",
#     "President", "president", "PRESIDENT", "Commander in Chief", "POTUS", "VEEP", "VP",
#     "Democrat", "democrat", "DEMOCRAT", "Republican", "republican", "GOP",
#     "left wing", "right wing", "liberal", "conservative",
#     "#Biden2024", "#VoteBiden", "#VoteBlueNoMatterWho"
# ]




     

# Using a three-month window before the election date (adjust accordingly)
START_DATE = "2024-06-04"
END_DATE = "2024-11-04"

MAX_TWEETS_PER_DAY = 50  # Max tweets per day
COOKIE_FILES = ["cookies.json", "cookies1.json"]
CSV_FILE = "tweets_cleaned2.csv"

# US location keywords (add common state abbreviations or names as necessary)
US_LOCATION_KEYWORDS = [
    # General terms
    "usa", "us", "united states ", "america", "u.s.a.", "u.s.", "united states of america",
    
    # States (Full names and abbreviations)
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado", "connecticut", "delaware", "florida", "georgia", 
    "hawaii", "idaho", "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana", "maine", "maryland", 
    "massachusetts", "michigan", "minnesota", "mississippi", "missouri", "montana", "nebraska", "nevada", "new hampshire", 
    "new jersey", "new mexico", "new york", "north carolina", "north dakota", "ohio", "oklahoma", "oregon", "pennsylvania", 
    "rhode island", "south carolina", "south dakota", "tennessee", "texas", "utah", "vermont", "virginia", "washington", 
    "west virginia", "wisconsin", "wyoming",

    # State abbreviations (two-letter codes)
    "al", "ak", "az", "ar", "ca", "co", "ct", "de", "fl", "ga", "hi", "id", "il", "in", "ia", "ks", "ky", "la", "me", "md", 
    "ma", "mi", "mn", "ms", "mo", "mt", "ne", "nv", "nh", "nj", "nm", "ny", "nc", "nd", "oh", "ok", "or", "pa", "ri", "sc", 
    "sd", "tn", "tx", "ut", "vt", "va", "wa", "wv", "wi", "wy",

    # Major US Cities
    "new york", "los angeles", "chicago", "houston", "phoenix", "philadelphia", "san antonio", "san diego", "dallas", 
    "san jose", "austin", "jacksonville", "fort worth", "columbus", "san francisco", "charlotte", "indianapolis", "seattle", 
    "denver", "washington", "boston", "el paso", "nashville", "detroit", "oklahoma city", "portland", "las vegas", 
    "memphis", "louisville", "baltimore", "milwaukee", "albuquerque", "tucson", "fresno", "sacramento", "mesa", "kansas city", 
    "atlanta", "long beach", "colorado springs", "raleigh", "miami", "virginia beach", "oakland", "minneapolis", 
    "tulsa", "bakersfield", "wichita", "arlington", "aurora", "tampa", "new orleans", "cleveland", "honolulu", 
    "anaheim", "lexington", "stockton", "pittsburgh", "st. louis", "cincinnati", "anchorage", "henderson", "greensboro", 
    "plano", "newark", "lincoln", "toledo", "orlando", "chula vista", "irvine", "fort wayne", "jersey city", "durham", 
    "st. petersburg", "lubbock", "madison", "gilbert", "norfolk", "reno", "winston-salem", "glendale", "hialeah", 
    "garland", "scottsdale", "irving", "chesapeake", "north las vegas", "fremont", "baton rouge", "richmond", "boise", 
    "san bernardino"
]

# ================== HELPERS ==================
def date_range(start: str, end: str) -> list:
    start_date = datetime.strptime(start, "%Y-%m-%d")
    end_date = datetime.strptime(end, "%Y-%m-%d")
    return [start_date + timedelta(days=x) 
            for x in range((end_date - start_date).days + 1)]

def is_us_location(location: str) -> bool:
    if location:
        location_lower = location.lower()
        return any(kw in location_lower for kw in US_LOCATION_KEYWORDS)
    return False

def compute_weight(tweet, user) -> float:
    """Calculate a bot probability score between 0 (bot) and 1 (human)."""
    score = 1.0  # Start with assumption of human

    # 1. Check for posting during late-night hours (UTC 3-5 AM)
    try:
        tweet_time = datetime.strptime(tweet.created_at, "%a %b %d %H:%M:%S %z %Y")
        if tweet_time.hour in [3, 4, 5]:
            score -= 0.1  # Small penalty for UTC nighttime activity
    except:
        pass  # If time parsing fails, no penalty

    # 2. Check for high tweet volume (possible automation)
    if user.statuses_count > 10000:
        score -= 0.3  # Large penalty for extreme activity
    elif user.statuses_count > 5000:
        score -= 0.2

    # 3. Account age analysis (new accounts are suspicious)
    try:
        user_created = datetime.strptime(user.created_at, "%a %b %d %H:%M:%S %z %Y")
        account_age = (datetime.now(user_created.tzinfo) - user_created).days
        
        if account_age < 7:
            score -= 0.4  # Very new account
        elif account_age < 30:
            score -= 0.25
        elif account_age < 365:
            score -= 0.1
    except:
        score -= 0.15  # Moderate penalty for unparseable date

    # 4. Profile completeness check
    if not user.description:
        score -= 0.15
    if user.followers_count < 10:
        score -= 0.1
    if user.following_count > 5000:  # Following too many accounts
        score -= 0.2

    # 5. Content patterns
    text = tweet.text.lower()
    if "check out" in text and "http" in text:
        score -= 0.25  # Spam-like content
    if any(phrase in text for phrase in ["win", "free", "click here"]):
        score -= 0.15

    # 6. Engagement ratio check
    if user.followers_count > 0:
        engagement_ratio = user.following_count / user.followers_count
        if engagement_ratio > 100:  # Following way more than followers
            score -= 0.2
    smoothed_score = 1 / (1 + math.exp(-10 * (score - 0.5)))
    # tweet_time = datetime.strptime(tweet.created_at, "%a %b %d %H:%M:%S %z %Y")
    # days_old = (datetime.now(tweet_time.tzinfo) - tweet_time).days
    # decay_factor = max(0.7, 1 - (days_old * 0.02))  # Linear decay (e.g., 2% per day)
    # final_score = smoothed_score * decay_factor
    # Ensure score stays within [0, 1] range
    return smoothed_score


# ================== STORAGE ==================
unique_tweets = {}  # {tweet_id: (tweet_data, likes, weight)}

def save_data():
    with open(CSV_FILE, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["Tweet ID", "Username", "Text", "Date", "Retweets", "Likes", "Weight"])
        for tweet_id, (tweet, likes, weight) in unique_tweets.items():
            clean_text = unicodedata.normalize('NFKC', tweet.text)
            clean_text = clean_text.replace("\n", " ").replace("\r", " ")
            writer.writerow([
                tweet_id,
                tweet.user.name.encode('utf-8', 'ignore').decode('utf-8'),
                clean_text,
                tweet.created_at,
                tweet.retweet_count,
                likes,
                weight
            ])

# ================== SCRAPING CORE ==================
async def process_date(client, query: str, date: datetime) -> int:
    date_str = date.strftime("%Y-%m-%d")
    next_str = (date + timedelta(days=1)).strftime("%Y-%m-%d")
    full_query = f"{query} since:{date_str} until:{next_str}"
    added = 0

    # Use safe_search_tweet for the initial fetch
    resp = await safe_search_tweet(client, full_query, product='Latest')
    if resp is None:
        return added

    tweets = list(resp)
    cursor = getattr(resp, 'min_position', None)
    pages = 1

    while cursor and pages < 10:
        resp = await safe_search_tweet(client, full_query, product='Latest', cursor=cursor)
        if resp is None:
            break
        pages += 1
        more = list(resp)
        if not more:
            break
        tweets.extend(more)
        cursor = getattr(resp, 'min_position', None)

    print(f"📅 {date_str}: fetched {len(tweets)} tweets over {pages} pages")
    
    if len(tweets) > MAX_TWEETS_PER_DAY:
        random.shuffle(tweets)

    for tweet in tweets[:MAX_TWEETS_PER_DAY]:
        # Uncomment the lines below if you want to skip verified accounts or non‑US tweets
        # if tweet.user.verified or not is_us_location(tweet.user.location):
        #     continue

        weight = compute_weight(tweet, tweet.user)
        tid, likes = tweet.id, tweet.favorite_count

        if tid not in unique_tweets or likes > unique_tweets[tid][1]:
            unique_tweets[tid] = (tweet, likes, weight)
            added += 1

    print(f"    → Added {added} unique tweets")
    return added

# ================== NETWORK HELPER ==================
async def safe_search_tweet(client, full_query, product, cursor=None, retries=3, delay=10):
    """Attempt to get tweets with retries in case of a ReadTimeout."""
    attempt = 0
    while attempt < retries:
        try:
            if cursor:
                return await client.search_tweet(full_query, product=product, cursor=cursor)
            else:
                return await client.search_tweet(full_query, product=product)
        except httpx.ReadTimeout:
            attempt += 1
            print(f"ReadTimeout on attempt {attempt}/{retries} for query '{full_query}'. Retrying after {delay}s...")
            await asyncio.sleep(delay)
    print(f"Failed after {retries} attempts for query '{full_query}'. Moving on.")
    return None

async def scrape_tweets():
    dates = date_range(START_DATE, END_DATE)
    cookie_idx = 0

    for query in QUERIES:
        for date in dates:
            print(f"\n🔎 Accessing tweets for {date.strftime('%Y-%m-%d')} with query '{query}'")
            client = Client(language='en-US')
            client.load_cookies(COOKIE_FILES[cookie_idx])
            cookie_idx = (cookie_idx + 1) % len(COOKIE_FILES)

            try:
                await process_date(client, query, date)
            except Exception as e:
                print(f"An unexpected error occurred: {e}")

            save_data()
            delay = random.randint(15, 30)
            print(f"⏳ Next date in {delay}s…")
            time.sleep(delay)

    print(f"\n✅ Finished! Collected {len(unique_tweets)} tweets.")
    save_data()


# Run the scraper
asyncio.run(scrape_tweets())
