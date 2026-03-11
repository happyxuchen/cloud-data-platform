from flask import Flask, jsonify, request
import os
import pandas as pd
import boto3
from werkzeug.utils import secure_filename

app = Flask(__name__)

s3 = boto3.client("s3")
BUCKET_NAME = "xuchen-cloud-data-platform-2026"

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {"csv"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def home():
    return "Cloud Data Platform API Running"


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "message": "API is running successfully"
    })


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only CSV files are allowed"}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    # 读取 CSV
    df = pd.read_csv(file_path)

    rows = len(df)
    columns = len(df.columns)
    file_size_bytes = os.path.getsize(file_path)

    # 缺失值统计
    missing_values = df.isnull().sum().to_dict()

    # 数值列统计
    numeric_summary = {}
    numeric_df = df.select_dtypes(include=["number"])
    if not numeric_df.empty:
        numeric_summary = numeric_df.describe().to_dict()

    # 上传到 S3
    s3.upload_file(file_path, BUCKET_NAME, filename)

    return jsonify({
        "message": "File uploaded, analyzed, and sent to S3",
        "rows": rows,
        "columns": columns,
        "column_names": list(df.columns),
        "file_size_bytes": file_size_bytes,
        "missing_values": missing_values,
        "numeric_summary": numeric_summary,
        "s3_bucket": BUCKET_NAME,
        "s3_key": filename
    })


if __name__ == "__main__":
    app.run(debug=True)