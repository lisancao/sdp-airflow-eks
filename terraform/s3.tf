resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# SDP pipeline storage: checkpoints, table data, event logs.
resource "aws_s3_bucket" "pipeline" {
  bucket = "${var.pipeline_bucket_prefix}-${random_id.bucket_suffix.hex}"
  tags   = var.tags
}

resource "aws_s3_bucket_public_access_block" "pipeline" {
  bucket = aws_s3_bucket.pipeline.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "pipeline" {
  bucket = aws_s3_bucket.pipeline.id
  versioning_configuration {
    status = "Disabled"
  }
}

resource "aws_iam_policy" "pipeline_bucket_rw" {
  name        = "${var.cluster_name}-pipeline-bucket-rw"
  description = "Read/write access to the SDP pipeline storage bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:ListBucket", "s3:GetBucketLocation"]
        Resource = aws_s3_bucket.pipeline.arn
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:AbortMultipartUpload"]
        Resource = "${aws_s3_bucket.pipeline.arn}/*"
      }
    ]
  })
}
