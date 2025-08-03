from flask import Flask, request, render_template
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import ipaddress
import re
from flask_sqlalchemy import SQLAlchemy
import os


app = Flask(__name__)


# DB config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///url_titles.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

with app.app_context():
    db.create_all()

# Model: stores URLs and their scraped titles
class URLTitle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), unique=True, nullable=False)
    title = db.Column(db.String(300), nullable=False)


def is_valid_url(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False
        if not parsed.hostname:
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


def call_external_api(title, keyword):
    try:
        response = requests.post(
            'http://127.0.0.1:5001/analyze-sentiment',
            json={"title": title, "keyword": keyword},
            timeout=3
        )
        response.raise_for_status()
        sentiment_score = response.json().get("sentiment")

        if sentiment_score == 1:
            return "Good"
        elif sentiment_score == 0:
            return "Neutral"
        elif sentiment_score == -1:
            return "Bad"
        else:
            return "Unknown"
    except Exception as e:
        return f"API Error: {e}"


def scrape_and_analyze(url, keyword):
    # Check if URL already exists in DB
    cached = URLTitle.query.filter_by(url=url).first()
    
    if cached:
        title = cached.title
    else:
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
        except requests.RequestException as e:
            return {"title": "Error fetching page", "sentiment": f"Error: {e}"}

        soup = BeautifulSoup(response.text, 'html.parser')
        h1_tag = soup.find('h1')
        title = h1_tag.get_text(strip=True) if h1_tag else "No title found"

        # Save new URL and title to DB
        new_entry = URLTitle(url=url, title=title)
        db.session.add(new_entry)
        db.session.commit()

    # Call external sentiment API using the title
    sentiment = call_external_api(title, keyword)

    return {"title": title, "sentiment": sentiment}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    url = request.form.get('url', '').strip()
    keyword = request.form.get('keyword', '').strip()

    if not url or not keyword:
        return "Missing URL or keyword", 400

    if not is_valid_url(url):
        return "Invalid or potentially unsafe URL", 400

    result = scrape_and_analyze(url, keyword)

    return render_template('results.html', post_title=result['title'], analysis=result['sentiment'])


if __name__ == '__main__':
    app.run(debug=True, port=5000)
