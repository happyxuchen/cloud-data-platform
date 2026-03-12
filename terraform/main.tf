provider "aws" {
  region = "us-east-2"
}

resource "aws_s3_bucket" "data_platform_bucket" {
  bucket = "xuchen-cloud-data-platform-terraform-2026"
}

resource "aws_s3_bucket_versioning" "bucket_versioning" {
  bucket = aws_s3_bucket.data_platform_bucket.id

  versioning_configuration {
    status = "Enabled"
  }
}