from flask import Flask, request, jsonify

mock_api = Flask(__name__)

@mock_api.route('/analyze-sentiment', methods=['POST'])
def analyze_sentiment():
    data = request.get_json()
    title = data.get('title', '').lower()
    keyword = data.get('keyword', '').lower()
    combined = f"{title} {keyword}"

    if "good" in combined or "excellent" in combined:
        score = 1
    elif "bad" in combined or "terrible" in combined:
        score = -1
    else:
        score = 0

    return jsonify({"sentiment": score})

if __name__ == '__main__':
    mock_api.run(debug=True, port=5001)
