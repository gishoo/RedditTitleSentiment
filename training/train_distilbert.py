import os
import pandas as pd
from datasets import Dataset
from transformers import (
    DistilBertTokenizerFast,
    DistilBertForSequenceClassification,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback
)
import mlflow
import mlflow.transformers
import yaml
import configparser
from datetime import datetime
import json
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

# --- Load credentials from middleware.yml ---
with open("../Infrastructure/group_vars/middleware.yml", "r") as f:
    middleware_cfg = yaml.safe_load(f)

access_key = middleware_cfg["do_spaces_access_key_id"]
secret_key = middleware_cfg["do_spaces_secret_access_key"]
endpoint_url = middleware_cfg["s3_endpoint"]
mlflow_port = middleware_cfg.get("mlflow_port", 5000)

# --- Load middleware host from inventory.ini ---
config = configparser.ConfigParser(allow_no_value=True, delimiters=(' ',))
config.optionxform = str  # preserve case
config.read("../Infrastructure/inventory.ini")

middleware_host = None
if "middleware" in config.sections():
    middleware_host = next(iter(config["middleware"]), None)

if not middleware_host:
    raise ValueError("Could not extract middleware IP from inventory.ini")

tracking_uri = f"http://{middleware_host}:{mlflow_port}"

# --- Set environment variables for DigitalOcean Spaces ---
os.environ["AWS_ACCESS_KEY_ID"] = access_key
os.environ["AWS_SECRET_ACCESS_KEY"] = secret_key
os.environ["MLFLOW_S3_ENDPOINT_URL"] = endpoint_url

# --- Set MLflow tracking ---
mlflow.set_tracking_uri(tracking_uri)
mlflow.set_experiment("reddit_sentiment_experiment")

# --- Load and preprocess dataset ---
df = pd.read_csv("../data/Reddit_Data.csv")
df['label'] = df['sentiment'].map({-1: 0, 0: 1, 1: 2})

dataset = Dataset.from_pandas(df[['comment', 'label']])
tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")

def tokenize(example):
    return tokenizer(example['comment'], padding="max_length", truncation=True, max_length=128)

dataset = dataset.map(tokenize, batched=True)
dataset.set_format("torch", columns=["input_ids", "attention_mask", "label"])
dataset = dataset.rename_column("label", "labels")

train_test = dataset.train_test_split(test_size=0.2)
train_dataset = train_test["train"]
eval_dataset = train_test["test"]

model = DistilBertForSequenceClassification.from_pretrained("distilbert-base-uncased", num_labels=3)

output_dir = "./models/distilbert_reddit_sentiment"
training_args = TrainingArguments(
    output_dir=output_dir,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=10,
    weight_decay=0.01,
    logging_dir="./logs",
    load_best_model_at_end=True,
    report_to="none"
)

# --- MLflow logging and training ---
with mlflow.start_run(run_name=f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
    mlflow.log_params({
        "learning_rate": training_args.learning_rate,
        "epochs": training_args.num_train_epochs,
        "batch_size": training_args.per_device_train_batch_size,
        "model": "distilbert-base-uncased"
    })

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        tokenizer=tokenizer,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)]
    )

    trainer.train()

    # --- Evaluate model ---
    preds = trainer.predict(eval_dataset)
    y_true = preds.label_ids
    y_pred = np.argmax(preds.predictions, axis=1)

    # --- Compute metrics ---
    acc = accuracy_score(y_true, y_pred)
    clf_report = classification_report(y_true, y_pred, output_dict=True, target_names=["negative", "neutral", "positive"])
    conf_matrix = confusion_matrix(y_true, y_pred)

    # --- Log primary metrics ---
    mlflow.log_metric("eval_accuracy", acc)
    mlflow.log_metric("f1_macro", clf_report["macro avg"]["f1-score"])
    mlflow.log_metric("precision_macro", clf_report["macro avg"]["precision"])
    mlflow.log_metric("recall_macro", clf_report["macro avg"]["recall"])

    # --- Save full classification report ---
    report_path = os.path.join(output_dir, "classification_report.json")
    with open(report_path, "w") as f:
        json.dump(clf_report, f, indent=2)
    mlflow.log_artifact(report_path)

    # --- Confusion matrix plot ---
    plt.figure(figsize=(6, 5))
    sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Blues',
                xticklabels=["negative", "neutral", "positive"],
                yticklabels=["negative", "neutral", "positive"])
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.title("Confusion Matrix")

    conf_matrix_path = os.path.join(output_dir, "confusion_matrix.png")
    plt.savefig(conf_matrix_path)
    plt.close()

    mlflow.log_artifact(conf_matrix_path)

    print("Logged evaluation metrics and confusion matrix to MLflow.")


    # Save final model and tokenizer
    model_path = os.path.join(output_dir, "final_model")
    model.save_pretrained(model_path)
    tokenizer.save_pretrained(model_path)

    # Log model
    mlflow.transformers.log_model(
        transformers_model={"model": model, "tokenizer": tokenizer},
        artifact_path="model",
        task="text-classification"
    )

    # Register model
    mlflow.register_model(
        model_uri="runs:/{}/model".format(mlflow.active_run().info.run_id),
        name="RedditSentimentModel"
    )

    # --- Example: Log a config file as artifact to remote Spaces ---
    config_dict = {
        "tokenizer": "distilbert-base-uncased",
        "num_labels": 3,
        "s3_endpoint": endpoint_url,
        "tracking_uri": tracking_uri
    }
    config_path = os.path.join(output_dir, "training_config.json")
    with open(config_path, "w") as f:
        json.dump(config_dict, f, indent=2)

    mlflow.log_artifact(config_path)

    print(f"Training complete. Model saved to: {model_path}")
