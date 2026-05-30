import os
import uuid
import boto3
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

TABLE_NAME = os.getenv('AWS_DYNAMODB_TABLE')

table = dynamodb.Table(TABLE_NAME)


def save_analysis_history(
        resume_name,
        s3_key,
        job_description,
        matched_skills,
        missing_skills,
        match_score,
        advice
):
    resume_id  = str(uuid.uuid4())
    item = {
        "resume_id":resume_id,
        "resume_name": resume_name,
        "s3_key":s3_key,
        "job_description":job_description,
        "matched_skills":matched_skills,
        "missing_skills":missing_skills,
        "match_score":str(match_score),
        "advice":advice,
        "created_at":datetime.now().strftime("%y-%m-%d %H:%M:%S")
    }

    table.put_item(Item = item)

def get_analysis_history():
    response = table.scan()
    return response.get("Items",[])

def delete_analysis_history(resume_id):
    table.delete_item(
        Key = {
            "resume_id":resume_id
        }
    )
    return True




