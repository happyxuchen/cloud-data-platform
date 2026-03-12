from flask import Flask, jsonify, request
import os
import pandas as pd
import boto3

from db import engine, SessionLocal
from models import Base, UploadRecord

app = Flask(__name__)
s3 = boto3.client("s3")
BUCKET_NAME = "xuchen-cloud-data-platform-2026"

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

Base.metadata.create_all(bind=engine)


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
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(file_path)

        s3.upload_file(file_path, BUCKET_NAME, file.filename)

        df = pd.read_csv(file_path)

        rows = len(df)
        columns = len(df.columns)
        column_names = list(df.columns)

        null_counts = df.isnull().sum().to_dict()

        numeric_summary = {}
        numeric_df = df.select_dtypes(include="number")
        if not numeric_df.empty:
            numeric_summary = numeric_df.describe().to_dict()

        preview = df.head(3).fillna("").to_dict(orient="records")

        # 写入 PostgreSQL
        db = SessionLocal()
        record = UploadRecord(
            filename=file.filename,
            rows=rows,
            columns=columns,
            s3_bucket=BUCKET_NAME,
            s3_key=file.filename
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        db.close()

        return jsonify({
            "message": "File uploaded, analyzed, sent to S3, and saved to PostgreSQL",
            "rows": rows,
            "columns": columns,
            "column_names": column_names,
            "null_counts": null_counts,
            "numeric_summary": numeric_summary,
            "preview": preview,
            "s3_bucket": BUCKET_NAME,
            "s3_key": file.filename,
            "db_record_id": record.id
        })

    except Exception as e:
        return jsonify({
            "error": str(e),
            "type": type(e).__name__
        }), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)