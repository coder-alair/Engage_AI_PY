from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select
from uuid import uuid4
from datetime import datetime, timedelta
from neondb.models import User, Jobs, Locations, Prompts, UserSubscription, Softwareroles, Company
from engage_api import settings
from typing import List


connection_string = str(settings.DATABASE_URL).replace(
    "postgresql", "postgresql+psycopg"
)

engine = create_engine(connection_string,
                        pool_size=10,
                        max_overflow=20,
                        pool_timeout=30,
                        pool_recycle=300)

def get_prompt(db: Session, prompt_name):
    stmt = select(Prompts.user_prompt, Prompts.system_prompt).filter(Prompts.prompt_name == prompt_name)
    result = db.execute(stmt)
    
    prompt = result.first()
    
    if prompt:
        print("PROMPT ", prompt)
        return prompt.system_prompt, prompt.user_prompt
    else:
        return None, None

def check_user(db: Session, user_id: str):
    stmt = select(User).filter(User.user_id == user_id)
    result = db.execute(stmt)
    
    user = result.scalars().first()
    
    if user:
        return user
    else:
        return None
    
def fetch_location(db: Session, location_id: str):
    stmt = select(Locations).filter(Locations.location_id == location_id)
    result = db.execute(stmt)
    
    location = result.scalars().first()
    
    if location:
        return location
    else:
        return None

def get_user_company(db: Session, user_id: str) -> Company:
    stmt = select(User).filter(User.user_id == user_id)
    result = db.execute(stmt)
    
    user = result.scalars().first()
    
    if user:
        return user.company
    else:
        return None
    
def save_jd(db: Session, user_id: str, job_name: str, job_description: str, technologies: List[str], experience: List[str], responsibilities: List[str], qualifications: List[str], isContract:str, salary_range:str, working_mode:str):
    new_job = Jobs(
        user_id=user_id,
        job_name=job_name,
        job_description=job_description,
        technologies=technologies,
        experience=experience,
        responsibilities=responsibilities,
        qualifications=qualifications,
        isContract=isContract,
        salary_range=salary_range,
        working_mode=working_mode
    )
    
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return new_job.job_id


def delete_old_jobs(db: Session):
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    old_jobs = db.query(Jobs).filter(Jobs.created_at < thirty_days_ago).all()
    
    for job in old_jobs:
        db.delete(job)
    
    db.commit()
    
    return len(old_jobs)

def empty_prompts(db: Session):
    db.query(Prompts).delete()
    db.commit()

def get_total_resumes(db: Session, user_id: str):

    stmt = select(UserSubscription).filter(UserSubscription.user_id == user_id)
    result = db.execute(stmt)

    return result.scalar().subscription.resumesAvailablity

def get_resumes_used(db: Session, user_id: str):
    stmt = select(UserSubscription).filter(UserSubscription.user_id == user_id)
    result = db.execute(stmt)

    return result.scalar().resumes_used


def get_user_sub(db: Session, user_id: str) -> UserSubscription:
    stmt = select(UserSubscription).filter(UserSubscription.user_id == user_id)
    result = db.execute(stmt)

    return result.scalar()

def add_roles():
    software_roles = [ "Java Developer", "Python Developer", "C++ Developer", "C# Developer", "JavaScript Developer", "TypeScript Developer", "Ruby Developer", "PHP Developer", ".NET Developer", "Scala Developer", "Go Developer", "Rust Developer", "Swift Developer", "Kotlin Developer", "Objective-C Developer", "R Developer", "MATLAB Developer", "Perl Developer", "Lua Developer", "Haskell Developer", "Erlang Developer", "Clojure Developer", "F# Developer", "Visual Basic Developer", "COBOL Developer", "Assembly Language Programmer", "Front-end Developer", "Back-end Developer", "Full Stack Developer", "Web Designer", "UX Designer", "UI Developer", "WordPress Developer", "Drupal Developer", "Magento Developer", "Shopify Developer", "E-commerce Developer", "iOS Developer", "Android Developer", "React Native Developer", "Flutter Developer", "Xamarin Developer", "Ionic Developer", "Mobile Game Developer", "Unity Developer", "Unreal Engine Developer", "Game Designer", "3D Modeler for Games", "Game AI Programmer", "Game Physics Programmer", "Data Scientist", "Data Analyst", "Data Engineer", "Big Data Engineer", "Database Administrator", "Database Developer", "ETL Developer", "Business Intelligence Developer", "Data Warehouse Engineer", "Machine Learning Engineer", "AI Engineer", "Natural Language Processing (NLP) Engineer", "Computer Vision Engineer", "Deep Learning Engineer", "Robotics Engineer", "Cloud Engineer", "AWS Developer", "Azure Developer", "Google Cloud Platform (GCP) Developer", "Cloud Architect", "DevOps Engineer", "Site Reliability Engineer (SRE)", "Systems Administrator", "Network Engineer", "Infrastructure Engineer", "Cybersecurity Analyst", "Information Security Engineer", "Penetration Tester", "Security Architect", "Cryptographer", "Forensic Analyst", "Blockchain Developer", "IoT Developer", "AR/VR Developer", "Quantum Computing Researcher", "5G Network Engineer", "QA Engineer", "Test Automation Engineer", "Performance Tester", "Security Tester", "Usability Tester", "Technical Project Manager", "Scrum Master", "Product Owner", "IT Director", "CTO (Chief Technology Officer)", "CIO (Chief Information Officer)", "Embedded Systems Developer", "Firmware Engineer", "FPGA Developer", "Audio Programmer", "Graphics Programmer", "High-Frequency Trading Systems Developer", "Bioinformatics Programmer", "Technical Support Engineer", "IT Support Specialist", "System Analyst", "Release Engineer", "Build Engineer", "UX Researcher", "Interaction Designer", "Information Architect", "Visual Designer", "Technical Writer", "API Documentation Specialist", "Knowledge Base Manager", "FinTech Developer", "HealthTech Developer", "EduTech Developer", "GreenTech Developer", "LegalTech Developer", "Edge Computing Specialist", "Quantum Algorithm Developer", "Autonomous Vehicle Programmer", "Smart Contract Developer", "Conversational AI Designer", "Ethical AI Consultant", "Digital Twin Developer", "Low-Code/No-Code Platform Specialist" ]
    db = Session(engine)
    
    for role in software_roles:
        new_role = Softwareroles(name=role)
        db.add(new_role)
        db.commit()
        db.flush()
    db.close()
