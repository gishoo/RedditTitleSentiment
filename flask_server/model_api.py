from flask import Flask, request, jsonify
from transformers import pipeline, DistilBertForSequenceClassification, DistilBertTokenizerFast
import torch
import mlflow.transformers
import os

# Label map for custom models
label_map = {0: "negative", 1: "neutral", 2: "positive"}

model = None
tokenizer = None
mode = None  


try:
    print("Trying to load model from MLflow Registry...")
    model_uri = "models:/RedditSentimentModel/Production"
    loaded = mlflow.transformers.load_model(model_uri)
    model = loaded["model"]
    tokenizer = loaded["tokenizer"]
    model.eval()
    mode = "registry"
    print("Loaded model from MLflow Registry.")
except Exception as e:
    print(f"Failed to load from MLflow Registry: {e}")


if model is None:
    try:
        print("Trying to load local model...")
        model_path = "../training/models/distilbert_reddit_sentiment/final_model"
        model = DistilBertForSequenceClassification.from_pretrained(model_path)
        tokenizer = DistilBertTokenizerFast.from_pretrained(model_path)
        model.eval()
        mode = "local"
        print("Loaded model from local disk.")
    except Exception as e:
        print(f"Failed to load from local disk: {e}")


if model is None:
    try:
        print("Falling back to Hugging Face sentiment pipeline...")
        sentiment_pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
        mode = "huggingface"
        print("Loaded Hugging Face sentiment pipeline.")
    except Exception as e:
        print(f"Failed to load fallback Hugging Face model: {e}")
        raise RuntimeError("All model loading attempts failed.")


app = Flask(__name__)

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    if not data or "title" not in data:
        return jsonify({"error": "Missing 'title' in request"}), 400

    title = data["title"]

    try:
        if mode in ["registry", "local"]:
            inputs = tokenizer(title, return_tensors="pt", padding=True, truncation=True, max_length=128)
            with torch.no_grad():
                outputs = model(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
                predicted_label = torch.argmax(probs, dim=1).item()
                confidence = probs[0][predicted_label].item()

            return jsonify({
                "sentiment": label_map[predicted_label],
                "confidence": round(confidence, 4),
                "source": mode
            })

        elif mode == "huggingface":
            result = sentiment_pipeline(title)[0]
            return jsonify({
                "sentiment": result["label"].lower(),
                "confidence": round(result["score"], 4),
                "source": "huggingface"
            })

        else:
            return jsonify({"error": "Model is not initialized"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
