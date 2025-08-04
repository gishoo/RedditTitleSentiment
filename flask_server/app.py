from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import ipaddress
import re
import praw
from urllib.parse import urlparse
import os

app = Flask(__name__)

# DB setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///url_titles.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class URLTitle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), unique=True, nullable=False)
    title = db.Column(db.String(300), nullable=False)

with app.app_context():
    db.create_all()


# Reddit API setup (you can move to environment variables or config later)
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "your-client-id")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "your-client-secret")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "RedditSentimentApp/0.1")

reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)

def extract_reddit_title(url):
    try:
        parsed = urlparse(url)
        path_parts = parsed.path.strip("/").split("/")

        if "comments" in path_parts:
            # Link to a specific post
            submission_id = path_parts[path_parts.index("comments") + 1]
            submission = reddit.submission(id=submission_id)
            return submission.title
        elif len(path_parts) >= 1 and path_parts[0].lower().startswith("r"):
            # Link to a subreddit
            subreddit_name = path_parts[1] if path_parts[0].lower() == "r" else path_parts[0][2:]
            subreddit = reddit.subreddit(subreddit_name)
            for post in subreddit.hot(limit=1):
                return post.title
        else:
            return "Could not determine Reddit content type."
    except Exception as e:
        return f"Reddit extraction error: {e}"


def is_valid_url(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False
        if not parsed.hostname:
            return False
        if "reddit.com" not in parsed.netloc:
            return False
        try:
            ip = ipaddress.ip_address(parsed.hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                return False
        except ValueError:
            if not re.match(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", parsed.hostname):
                return False
        return True
    except Exception:
        return False


def call_external_api(title):
    try:
        response = requests.post(
            'http://127.0.0.1:5001/analyze',  # Make sure this matches api.py's port
            json={"title": title},
            timeout=5
        )
        response.raise_for_status()
        result = response.json()

        label = result.get("sentiment", "").lower()
        if label == "positive":
            return "Good"
        elif label == "neutral":
            return "Neutral"
        elif label == "negative":
            return "Bad"
        else:
            return "Unknown"
    except Exception as e:
        return f"API Error: {e}"


def scrape_and_analyze(url):
    cached = URLTitle.query.filter_by(url=url).first()

    if cached:
        title = cached.title
    else:
        title = extract_reddit_title(url)
        new_entry = URLTitle(url=url, title=title)
        db.session.add(new_entry)
        db.session.commit()

    sentiment = call_external_api(title)
    return {"title": title, "sentiment": sentiment}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    url = request.form.get('url', '').strip()

    if not url:
        return "Missing URL", 400

    if not is_valid_url(url):
        return "Invalid or potentially unsafe URL", 400

    result = scrape_and_analyze(url)

    return render_template('results.html', post_title=result['title'], analysis=result['sentiment'])


@app.route('/history')
def history():
    all_entries = URLTitle.query.all()
    return render_template('history.html', entries=all_entries)


@app.route('/reanalyze', methods=['POST'])
def reanalyze():
    url = request.form.get('url', '').strip()

    if not url:
        return "Missing URL", 400

    if not is_valid_url(url):
        return "Invalid or potentially unsafe URL", 400

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
    except requests.RequestException as e:
        return f"Error fetching URL: {e}", 400

    soup = BeautifulSoup(response.text, 'html.parser')
    h1_tag = soup.find('h1')
    new_title = h1_tag.get_text(strip=True) if h1_tag else "No title found"

    entry = URLTitle.query.filter_by(url=url).first()
    if entry:
        entry.title = new_title
    else:
        entry = URLTitle(url=url, title=new_title)
        db.session.add(entry)

    db.session.commit()

    sentiment = call_external_api(new_title)
    return render_template('results.html', post_title=new_title, analysis=sentiment)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
