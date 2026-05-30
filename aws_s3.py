import os
import boto3
from dotenv import load_dotenv
from datetime import datetime
from io import BytesIO

load_dotenv()

s3_client =  boto3.client(
    's3',
    aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name = os.getenv('AWS_REGION')
)


BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')

def upload_resume_to_s3(file_bytes, original_filename):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        s3_key = f"resumes/{timestamp}_{original_filename}.pdf"

        s3_client.upload_fileobj(
            BytesIO(file_bytes),
            BUCKET_NAME,
            s3_key
        )

        return s3_key

    except Exception as e:
        print("Error uploading file to S3:", e)
        return None


def download_resume_from_s3(s3_key):
    try:
        response = s3_client.get_object(
            Bucket=BUCKET_NAME,
            Key=s3_key
        )

        file_bytes = response["Body"].read()
        resume_file = BytesIO(file_bytes)
        resume_file.seek(0)

        return resume_file

    except Exception as e:
        print("S3 DOWNLOAD ERROR:", e)
        return None



def list_resumes_from_s3():
    try:
        response = s3_client.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix="resumes/"
        )

        resumes = []

        if "Contents" in response:

            for item in response["Contents"]:
                key = item["Key"]

                # skip folder object
                if key.endswith("/"):
                    continue

                if key.endswith(".pdf"):
                    resumes.append({
                        "key": key,
                        "name": key.split("/")[-1],
                        "last_modified": str(item["LastModified"])
                    })

        print("S3 Resume List:", resumes)

        return resumes

    except Exception as e:
        print("Error listing resumes:", e)
        return []
    
def delete_resume_from_s3(s3_key):
    try:
        s3_client.delete_object(
            Bucket=BUCKET_NAME,
            Key=s3_key
        )
        print(f"Deleted resume from S3: {s3_key}")
        return True
    except Exception as e:
        print("Error deleting resume from S3:", e)
        return False