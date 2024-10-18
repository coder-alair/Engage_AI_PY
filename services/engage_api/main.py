from typing import Union, List
import uuid
import boto3
from llm_connect.llm import analyze_resume, generate_custom_option, is_software_req, generate_jd, get_predefined_choices, get_salary_range
from fastapi import FastAPI, File, Form, UploadFile, Depends
from engage_api.schemas import CheckReqPayload, CustomChoicesPayModel, JDPayModel, Meta, RangePayModel, ResponseModel, RolePayModel, PredefinedPayModel
from sqlalchemy import create_engine, select
from typing import Annotated
from sqlalchemy.orm import sessionmaker, Session
from contextlib import asynccontextmanager
from sqlalchemy.sql import func, text
from engage_api import settings
from datetime import datetime
from neondb import models
from resume_parse.parse import parse_pdf, parse_docx
from resume_parse.check import check_resume_type, process_file, save_to_db
from authentication.jwt_auth import JWTBearer
from authentication.auth_handler import JWT_ALGORITHM, JWT_SECRET
from neondb.helper import add_roles, check_user, delete_old_jobs, empty_prompts, fetch_location, get_prompt, get_resumes_used, get_total_resumes, get_user_company, get_user_sub, save_jd
from fastapi_utilities import repeat_every
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor
import jwt
import os
from neondb.helper import engine
from fastapi.middleware.cors import CORSMiddleware


no_user = "User Not Found"
@asynccontextmanager
async def lifespan(app: FastAPI):
    startup_event()
    yield

app = FastAPI(lifespan=lifespan)
s3_client = None
# @repeat_every(seconds=60 * 60 * 24) # 24 Hours
# def del_jobs():
#     with Session(engine) as session:
#         delete_old_jobs(db=session)
#     return {"message": "Success"}

def startup_event():
    global s3_client
    s3_client = boto3.client('s3')
    with Session(engine) as db:
        db.execute(text("SELECT 1"))

@app.get("/")
def status():
    """
        Provides the status of the app
    """
    return {"status": "App launched Successfully"}


origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/check_role/")
def check_req(data: CheckReqPayload, token: str = Depends(JWTBearer())) -> ResponseModel:
    """
        Checks if the given role is related to software development or not
    """
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM]) 
    found = False
    with Session(engine) as session:
        stmt = select(models.User).where(models.User.user_id == payload.get('user_id'))
        if session.scalar(stmt) is not None:
            found = True
    if found:
        return ResponseModel(data={"status": is_software_req(data.role)}, meta=Meta(code=1, message="Check Role Successfully"))
    return ResponseModel(data=None, meta=Meta(code=0, message=no_user))


@app.post('/api/get_roles/', response_model=ResponseModel)
def roles(data: RolePayModel):
    """
        Provides the available roles from the db
    """
    try:
        session = Session(engine)
        roles = session.query(models.Softwareroles).filter(models.Softwareroles.name.ilike(f'{data.keyword}%')).limit(10).all()
        dict_result = [obj.to_dict() for obj in roles]
        session.close()
        return ResponseModel(data=dict_result, meta=Meta(code=1, message="Fetched Successfully"))
    except Exception as e:
        return ResponseModel(data=None, meta=Meta(code=0, message=str(e)))


@app.post('/api/get_predefined_options/', response_model=ResponseModel)
def get_predefined_options(data: PredefinedPayModel, token: str = Depends(JWTBearer())):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM]) 
        user_id = payload.get("user_id")
        with Session(engine) as session:
            user = check_user(db=session, user_id=user_id)
        if user:
            return ResponseModel(data=get_predefined_choices(data.job_title), meta=Meta(code=1, message="Options Fetched Successfully"))
        else:
            return ResponseModel(data=None, meta=Meta(code=0, message=no_user))
    except Exception as e:
        return ResponseModel(data=None, meta=Meta(code=0, message=str(e)))


@app.get('/api/fetch_locations/', response_model=ResponseModel)
def get_locations():
    try:
        with Session(engine) as session:
            stmt = select(models.Locations)
            result = session.scalars(stmt).all()
            dict_result = [obj.to_dict() for obj in result]
        return ResponseModel(data=dict_result, meta=Meta(code=1, message="Fetched Locations Successfully"))
    except Exception as e:
        return ResponseModel(data=None, meta=Meta(code=0, message=str(e)))

        
@app.get('/api/get_jobs/', response_model=ResponseModel)
def get_job(token: str = Depends(JWTBearer())):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        with Session(engine) as session:
            stmt = select(models.Jobs).where(models.Jobs.user_id == payload.get("user_id"))
            result = session.scalars(stmt).all()
            dict_result = [obj.to_dict() for obj in result]

        return ResponseModel(data=dict_result, meta=Meta(code=1, message="Fetched Job Descriptions Successfully"))
    except Exception as e:
        return ResponseModel(data=None, meta=Meta(code=0, message=str(e)))

    
@app.post("/api/generate_description/", response_model=ResponseModel)
async def generate(data: JDPayModel, token: str = Depends(JWTBearer())):
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM]) 
        session = Session(engine)
        if check_user(db=session, user_id=payload.get("user_id")):
            created = datetime.now().strftime("%d-%m-%y_%H:%M:%S")
            job_name = f"{data.role}_{created}"
        
            company = get_user_company(db=session, user_id=payload.get("user_id"))
            if data.city and data.state and data.country:
                job_desc = generate_jd(data.role, data.responsibilities, data.qualifications, data.technologies, data.experience, data.iscontract, data.salary_range, data.currency, data.working_mode, company.companyName, company.bio, data.city, data.state, data.country)
            else:
                job_desc = generate_jd(data.role, data.responsibilities, data.qualifications, data.technologies, data.experience, data.iscontract, data.salary_range, data.currency, data.working_mode, company.companyName, company.bio, company.city, company.province, company.country)

            job_id = save_jd(db=session, user_id=payload.get("user_id"), job_name=job_name, job_description=job_desc, responsibilities=data.responsibilities, qualifications=data.qualifications, experience=data.experience, technologies=data.technologies, isContract=data.iscontract, salary_range=data.salary_range, working_mode=data.working_mode)
            session.close()

            return ResponseModel(data={"description": job_desc, "job_id": job_id}, meta=Meta(code=1, message="Generated Job Description Successfully"))
        else:
            session.close()
            return ResponseModel(data=None, meta=Meta(code=0, message=no_user))
    except Exception as e:
        return ResponseModel(data=None, meta=Meta(code=0, message=str(e)))


@app.post('/api/get_options/', response_model=ResponseModel)
async def get_custom_options(data: CustomChoicesPayModel, token: str = Depends(JWTBearer())):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        session = Session(engine)
        if check_user(db=session, user_id=user_id):
            session.close()
            return ResponseModel(data=generate_custom_option(data.question, data.role), meta=Meta(code=1, message="Generated Job Description Successfully"))
        else:
            session.close()
            return ResponseModel(data=None, meta=Meta(code=0, message=no_user))
        
    except Exception as e:
        return ResponseModel(data=None, meta=Meta(code=0, message=str(e)))


@app.post('/api/get_range/', response_model=ResponseModel)
def getranges(data: RangePayModel, token: str = Depends(JWTBearer())):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM]) 
        user_id = payload.get("user_id")
        found = False
        with Session(engine) as session:
            if check_user(db=session, user_id=user_id):
                company = get_user_company(db=session, user_id=user_id)
                location = None
                print(data)
                print("|||||||||||||||||||||||||||||||")
                if data.city and data.country:
                    location = {"city": data.city, "state": data.state, "country": data.city}
                found = True

        if found:
            return ResponseModel(data=get_salary_range(data.role, data.iscontract, company, location), meta=Meta(code=1, message="Generated Ranges Successfully"))
        else:
            return ResponseModel(data=None, meta=Meta(code=0, message=no_user))
    except Exception as e:
        return ResponseModel(data=None, meta=Meta(code=0, message=str(e)))
    

@app.get('/api/reset_prompts/', response_model=ResponseModel)
def reset_prompts():
    """
        Resets the Prompts in the db.\n
        Warning: It'll delete the prompts and set the default ones. This might remove any changes made to it
    """
    try:
        with Session(engine) as session:

            empty_prompts(db=session)

            prompt1 = models.Prompts(prompt_name='CUSTOM_ROLE_CHECK', user_prompt="Question: Is 'CUSTOM_ROLE' a software development role?, Answer: should be in Yes/No")

            prompt2 = models.Prompts(prompt_name='PREDEFINED_OPTIONS', user_prompt="Provide the combined response to the following prompts strictly in JSON format only, without any additional text, explanations, or notes. The JSON should be formatted exactly as specified, and any additional information should be excluded.\n\n1. Provide the five main high-level job responsibilities for a 'JOB_TITLE'.\n{\n  \"job_responsibilities\": [\"resp1\", \"resp2\", \"resp3\", \"resp4\", \"resp5\"]\n}\n\n2. Provide the five main high-level qualifications for a 'JOB_TITLE'.\n{\n  \"qualifications\": [\"qual1\", \"qual2\", \"qual3\", \"qual4\", \"qual5\"]\n}\n\n3. List five other technologies which a 'JOB_TITLE' should be aware of.\n{\n  \"technologies\": [\"tech1\", \"tech2\", \"tech3\", \"tech4\", \"tech5\"]\n}\n\n4. Generate the five seniority levels for a 'JOB_TITLE' role.\n{\n  \"seniorityLevels\": [\"level1\", \"level2\", \"level3\", \"level4\", \"level5\"]\n}\n\nCombine all responses into the following exact JSON format without any additional text or notes:\n{\n  \"options\": [\n    {\n      \"question1\": {\n        \"job_responsibilities\": []\n      }\n    },\n    {\n      \"question2\": {\n        \"qualifications\": []\n      }\n    },\n    {\n      \"question3\": {\n        \"technologies\": []\n      }\n    },\n    {\n      \"question4\": {\n        \"seniorityLevels\": []\n      }\n    }\n ] \n}")

            prompt3 = models.Prompts(prompt_name='GET_SALARY_RANGE', user_prompt="Generate a JSON object containing HOURLY_YEARLY salary ranges for \"JOB_ROLE\" across all experience levels in CITY, STATE, COUNTRY. The response should be in this exact JSON format:\n\n{ \"currency\": [currency_code], \"pay_ranges\": [ { \"level\": \"[Level name]\", \"pay\": { \"min\": [minimum HOURLY_YEARLY rate], \"max\": [maximum HOURLY_YEARLY rate] } } ] }\n\nReplace \"currency_code\" with the appropriate currency code and Replace \"minimum HOURLY_YEARLY rate\" and \"maximum HOURLY_YEARLY rate\" with the different HOURLY_YEARLY rate ranges for the specified level and location. Do not include any additional information or notes.")

            prompt4 = models.Prompts(prompt_name='GENERATE_JOB_DESCRIPTION', user_prompt="Based on the provided details, generate a detailed job description for a 'JOB_ROLE'. Responsibilities include 'RESPONSIBILITIES'. Working Model is 'WORKING_MODEL'. Qualifications require 'QUALIFICATIONS'. Technologies such as 'TECHNOLOGIES'. The role is for a 'EXPERIENCE' on a 'CONTRACT_FULLTIME' basis, with an 'HOURLY_YEARLY' ranging between 'CURRENCY' 'SALARY_RANGE'. Company Name: 'COMPANY_NAME', Company Bio: 'COMPANY_BIO', Company Location: 'CITY', 'STATE', 'COUNTRY'. Extra Info: 'QA_PAIR'. Do not provide any additional information or notes. Only provide the comprehensive description.")

            prompt5 = models.Prompts(prompt_name='GET_CUSTOM_OPTIONS', user_prompt="'CUSTOM_QUESTION' for a 'JOB_ROLE'. The response should not contain additional details or information. The response should be in this exact JSON format:\n{{\n  \"title\": \"[heading]\", \"options\": [\"optn1\", \"optn2\", \"optn3\", \"optn4\", \"optn5\"]\n}}\nReplace \"optn1\" through \"optn5\" with the appropriate options.")

            prompt6 = models.Prompts(prompt_name='ANALYZE_RESUME', system_prompt="'You are an HR analyst with a very strict evaluation standard. Your task is to compare a job description to a candidate's resume. Analyze the following job description and resume with a focus on stringent assessment, providing your evaluation in the exact format specified. Any experience or skills not directly relevant to JOB_ROLE should result in a score close to 0. Please do not provide any additional notes or details. Please only provide your analysis in the following JSON format, replacing the placeholders with appropriate content: { \"candidate_name\": <extract name from resume>, \"qualifications_percent_score\": Provide an integer between 0 and 100. These are the given qualifications - QUALIFICATIONS_STRING. These qualifications may not match explicitly but there can be advanced qualifications mentioned which should be given higher score., the score should be between 0 and 20. \"responsibilities_percent_score\": Provide an integer between 0 and 100. These are the given responsibilities - RESPONSIBILITIES_STRING. If the responsibilities do not align directly with the listed responsibilities, score between 0 and 20. \"technologies_percent_score\": Provide an integer between 0 and 100. These are the given technologies - TECHNOLOGIES_STRING. If the candidate does not have direct experience with the listed technologies, score between 0 and 20. \"brief_analysis\": <provide a concise and critical analysis of the candidate's fit for the role, focusing on gaps and concerns>, \"interview_points\": <list 3-5 key points or questions to focus on during the candidate's interview based on gaps or missing skills>, \"experience_percent_score\": Provide an integer between 0 and 100. If the candidate has less experience for a JOB_ROLE, score between 0 and 10. } Ensure that: 1. The \"percent_score\" is an integer between 0 and 100, and very low if relevance is lacking. 2. The \"brief_analysis\" is concise, critical, and highlights any major gaps or concerns. 3. The \"interview_points\" are specific to gaps in the candidate's resume compared to the job requirements. 4. All the keys are present in the JSON output. 5. The \"qualifications_percent_score\" is very low if qualifications are not met or relevant. 6. The \"responsibilities_percent_score\" is very low if responsibilities are not met or relevant. 7. The \"technologies_percent_score\" is very low if technologies are not relevant or mentioned. 8. The \"experience_percent_score\" is near 0 if the candidate does not meet the experience requirement, especially for senior roles. 9. The response and all the keys are present in the JSON output.'")

            session.add(prompt1)
            session.add(prompt2)
            session.add(prompt3)
            session.add(prompt4)
            session.add(prompt5)
            session.add(prompt6)
            session.commit()

        return ResponseModel(data=None, meta=Meta(code=1, message="Restored Prompts Successfully"))
    except Exception as e:
        return ResponseModel(data=None, meta=Meta(code=0, message=str(e)))


@app.get('/api/resumes_left/')
def get_resumes_left(token: str = Depends(JWTBearer())):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        found = False
        with Session(engine) as session:
            if check_user(db=session, user_id=user_id):
                total_res = get_total_resumes(db=session, user_id=user_id)
                used_res = get_resumes_used(db=session, user_id=user_id)
                found = True
        if found:
            return ResponseModel(data={"resumes_left": (total_res - used_res)}, meta=Meta(code=1, message="Fetch Resumes Left Successfully"))
        return ResponseModel(data=None, meta=Meta(code=0, message=no_user))
                
    except Exception as e:
        return ResponseModel(data=None, meta=Meta(code=0, message=str(e)))
    
@app.get('/api/add_roles')
def add_software_roles():
    try:
        add_roles()
        return {'status': 'add success'}
    except Exception as e:
        return {'status': f"ERROR: {e}"}

@app.post("/api/upload_resumes/", response_model=ResponseModel)
def create_upload_file(files: List[UploadFile] = File(...), job_id: str = Form(...), token: str = Depends(JWTBearer())):

    if not os.path.isdir('media'):
        os.mkdir('media')
    
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM]) 
    user_id = payload.get("user_id")

    session = Session(engine)

    stmt = select(
        models.Jobs.job_description,
        models.Jobs.qualifications,
        models.Jobs.responsibilities,
        models.Jobs.experience,
        models.Jobs.technologies
    ).where(
        models.Jobs.job_id == job_id,
        models.Jobs.user_id == user_id
    )

    result = session.execute(stmt).first()

    if result:
        jd, qualifications, responsibilities, experience, technologies = result
    else:
        jd = qualifications = responsibilities = experience = technologies = None
        
    stmt = select(
        models.Company
    ).join(
        models.User.company
    ).where(
        models.User.user_id == user_id
    )

    company_result = session.execute(stmt).first()
    company = company_result[0]
    print(company.companyName)
    print(company.state)
    print(company.country)
    print(company.bio)
    print(company.industry)

    responsibilities_string = ", ".join(responsibilities)
    qualifications_string = ", ".join(qualifications)
    technologies_string = ", ".join(technologies)
    experience_string = ", ".join(experience)

    sys_prompt, usr_prompt = get_prompt(db=session, prompt_name='ANALYZE_RESUME')
    sys_prompt = sys_prompt.replace('JOB_ROLE', experience_string)
    sys_prompt = sys_prompt.replace('TECHNOLOGIES_STRING', technologies_string)
    sys_prompt = sys_prompt.replace('RESPONSIBILITIES_STRING', responsibilities_string)
    sys_prompt = sys_prompt.replace('QUALIFICATIONS_STRING', qualifications_string)
    sys_prompt = sys_prompt.replace('COMPANY_NAME', company.companyName)
    sys_prompt = sys_prompt.replace('COMPANY_STATE', company.state)
    sys_prompt = sys_prompt.replace('COMPANY_COUNTRY', company.country)
    sys_prompt = sys_prompt.replace('COMPANY_BIO', company.bio)
    sys_prompt = sys_prompt.replace('COMPANY_INDUSTRY', company.industry)
    print(sys_prompt)
    if jd:
        if check_resume_type(files):
            if len(files) <= 10:      
                
                analysis_objects = []
                resume_objects = []
                with ThreadPoolExecutor() as executor:
                    futures = [executor.submit(process_file, s3_client, file, jd, usr_prompt, sys_prompt) for file in files]
                    results = []
                    for future in as_completed(futures):
                        result = future.result()
                        results.append(result)
                        file_id = save_to_db(session, result, user_id)
                        experience_percent_score=int(result['analysis']['experience_percent_score'])
                        qualifications_percent_score=int(result['analysis']['qualifications_percent_score'])
                        technologies_percent_score=int(result['analysis']['technologies_percent_score'])
                        percent_score=int(experience_percent_score*0.2+qualifications_percent_score*0.2+technologies_percent_score*0.6)
                        
                        if file_id:
                            analysis = models.ResumeAnalysis(
                                    candidate_name=result['analysis']['candidate_name'],
                                    qualifications_percent_score=qualifications_percent_score,
                                    technologies_percent_score=technologies_percent_score,
                                    responsibilities_percent_score=0,
                                    experience_percent_score=experience_percent_score,
                                    percent_score=int(percent_score),
                                    brief_analysis=result['analysis']['brief_analysis'],
                                    interview_points="\n".join(result['analysis']['interview_points']),
                                    job_id=job_id,
                                    resume_id=file_id
                                )
                            analysis_objects.append(analysis)
                session.add_all(analysis_objects)

                session.commit()
                session.close()

                return ResponseModel(data={"analysis": [result['analysis'] for result in results]}, meta=Meta(code=1, message="Resume Analysis Complete"))
            else:
                return ResponseModel(data=None, meta=Meta(code=0, message="Cannot Process more than 10 resumes at a time"))
        else:
            return ResponseModel(data=None, meta=Meta(code=0, message="Only PDF and Docx are supported"))
    else:
        return ResponseModel(data=None, meta=Meta(code=0, message="Job Description Not Found"))