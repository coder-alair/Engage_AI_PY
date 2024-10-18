from typing import Union, List
from fastapi import UploadFile
from neondb import models
from resume_parse.parse import parse_pdf, parse_docx
from llm_connect.llm import analyze_resume
from neondb.helper import engine
from sqlalchemy.orm import Session
from botocore.exceptions import NoCredentialsError
from fastapi import HTTPException
import os

def check_resume_type(files: List[UploadFile]):
    for file in files:
        if not (file.filename.endswith('pdf') or file.filename.endswith('docx')):
            return False
    return True

def save_to_db(session, result, user_id):
        try:
            resume = models.Resumefiles(
                filename=result['filename'], 
                extracted_data=result['text'], 
                user_id=user_id, 
                url=result['file_path']
            )
            session.add(resume)
            session.flush()

            return resume.file_id
        except Exception:
            return None
        
def upload_to_s3(s3_client, file):
    try:
        s3_key = f'resumes/{file.filename}'
        bucket_name = os.environ['BUCKET_NAME']
        print("BUCKET_NAME: ", bucket_name)
        s3_client.upload_fileobj(
            file.file,
            bucket_name,
            s3_key,
            ExtraArgs={'ContentType': file.content_type}
        )
        s3_url = f'https://{bucket_name}.s3.amazonaws.com/{s3_key}'
        print("S3 URL: ", s3_url)
        return s3_url
    except NoCredentialsError:
        print("AWS CREDS NOT FOUND")
        raise HTTPException(status_code=500, detail="AWS credentials not available")


def process_file(s3_client, file, jd, usr_prompt, sys_prompt):
    print("PARSING START!")
    if file.filename.endswith('pdf'):
        text = parse_pdf(file.file)
    elif file.filename.endswith('docx'):
        text = parse_docx(file.file)
    print("PARSING END!")
    
    analysis = analyze_resume(job_description=jd, resume=text, usr_prompt=usr_prompt, sys_prompt=sys_prompt)
    
    if os.environ['ENVIRONMENT']=='staging':
        file_path = f"media/{file.filename}"
        with open(file_path, "wb") as f:
            f.write(file.file.read())
    else:
        file_path = upload_to_s3(s3_client, file)
    
    result =  {
        'filename': file.filename,
        'text': text,
        'analysis': analysis,
        'file_path': file_path
    }
    
    return result
