from sqlalchemy.orm import Session
from dotenv import load_dotenv
from typing import List, Optional
from neondb.models import Company
from openai import OpenAI
from neondb.helper import engine
import json
import os
import logging
import time
from neondb.helper import get_prompt

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

deepinfra = OpenAI(
    api_key=os.environ['DEEPINFRA_TOKEN'],
    base_url="https://api.deepinfra.com/v1/openai",
)

mixtral_model = "mistralai/Mixtral-8x7B-Instruct-v0.1"
llama_model = "meta-llama/Meta-Llama-3-70B-Instruct"
llama_405 = "meta-llama/Meta-Llama-3.1-8B-Instruct"

def get_response(model: str, user_prompt: str, system_prompt: str = "Be a Helpful Assistant", response_type: dict = {'type': 'text'}, max_tokens: int = None):
    
    start_time = time.time()
    
    logging.info("Sending request to DeepInfra API")

    chat_completion = deepinfra.chat.completions.create(
        model=model,

        messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
        max_tokens=max_tokens,
        response_format=response_type,
        temperature=0.4
    )

    end_time = time.time()
    logging.info(f"Received response in {end_time - start_time:.2f} seconds")
    print("|||||||||||||||")
    print(chat_completion.choices[0].message.content)
    return chat_completion.choices[0].message.content


def is_software_req(custom_req: str) -> bool:
    """
        Checks if the given custom requirement is software requirement or not:
        Parameters:
            custom_req: custom requirement for the job

        Returns:
            Bool: True if requirement is for software role else False
    """
    with Session(engine) as session:
        sys_prompt, usr_prompt = get_prompt(db=session, prompt_name="CUSTOM_ROLE_CHECK")
    usr_prompt = usr_prompt.replace('CUSTOM_ROLE', custom_req)
        
    response = get_response(model=mixtral_model, system_prompt=sys_prompt, user_prompt=usr_prompt, max_tokens=1)

    if response.strip().lower() == 'yes':
        return True
    return False

def get_predefined_choices(job_title: str) -> list[dict]:

    with Session(engine) as session:
        sys_prompt, usr_prompt = get_prompt(db=session, prompt_name="PREDEFINED_OPTIONS")
    usr_prompt = usr_prompt.replace('JOB_TITLE', job_title)

    response = json.loads(get_response(model=mixtral_model, system_prompt=sys_prompt, user_prompt=usr_prompt, response_type={'type': 'json_object'}))
    response['options'].append({'question5': {"contract": ["Full-time", "Contractual"], }, 'question6': {"working_mode": ["Remote", "On-Site", "Hybrid", "Part-Time"]}})
    return response

def get_salary_range(role:str, iscontract: str, company: Company, location: Optional[dict] = None):

    if location:

        loc_city = location['city']
        loc_state = location['state']
        loc_country = location['country']

    else:
        loc_city = company.city
        loc_state = company.province
        loc_country = company.country

    with Session(engine) as session:
        sys_prompt, usr_prompt = get_prompt(db=session, prompt_name="GET_SALARY_RANGE")
    usr_prompt = usr_prompt.replace('JOB_ROLE', role)
    usr_prompt = usr_prompt.replace('CITY', loc_city)
    usr_prompt = usr_prompt.replace('STATE', loc_state)
    usr_prompt = usr_prompt.replace('COUNTRY', loc_country)

        
    if iscontract:
        usr_prompt = usr_prompt.replace('HOURLY_YEARLY', 'hourly')
    else:
        usr_prompt = usr_prompt.replace('HOURLY_YEARLY', 'yearly')
    response_str=get_response(model=mixtral_model, system_prompt=sys_prompt, user_prompt=usr_prompt, response_type={'type': 'json_object'})
    response_str = response_str.replace("\\", "")
    response = json.loads(response_str)
    
    return response


def generate_jd(role: str, responsibilities: List[str], qualifications: List[str], technologies: List[str], experience: List[str], iscontract: bool, salary_range: str, currency: str, remote: str, company_name: str, company_bio: str, city: Optional[str] = None, state: Optional[str] = None, country: Optional[str] = None, qa_pair: Optional[dict] = None) -> str:
    
    with Session(engine) as session:
        sys_prompt, usr_prompt = get_prompt(db=session, prompt_name="GENERATE_JOB_DESCRIPTION")
    
    usr_prompt = usr_prompt.replace('JOB_ROLE', role)
    usr_prompt = usr_prompt.replace('RESPONSIBILITIES', ", ".join(responsibilities))
    usr_prompt = usr_prompt.replace('WORKING_MODEL', remote)
    usr_prompt = usr_prompt.replace('QUALIFICATIONS', ", ".join(qualifications))
    usr_prompt = usr_prompt.replace('CONTRACT_FULLTIME', 'contract' if iscontract else 'fulltime')
    usr_prompt = usr_prompt.replace('HOURLY_YEARLY', 'hourly' if iscontract else 'yearly')
    usr_prompt = usr_prompt.replace('TECHNOLOGIES', ", ".join(technologies))
    usr_prompt = usr_prompt.replace('EXPERIENCE', ", ".join(experience))
    
    usr_prompt = usr_prompt.replace('CURRENCY', currency)
    usr_prompt = usr_prompt.replace('SALARY_RANGE', salary_range)

    usr_prompt = usr_prompt.replace('CITY', city)
    usr_prompt = usr_prompt.replace('STATE', state)
    usr_prompt = usr_prompt.replace('COUNTRY', country)

    usr_prompt = usr_prompt.replace('COMPANY_NAME', company_name)
    usr_prompt = usr_prompt.replace('COMPANY_BIO', company_bio)

    if qa_pair:
        usr_prompt = usr_prompt.replace('QA_PAIR', qa_pair)

    else:
        usr_prompt = usr_prompt.replace('QA_PAIR', 'None')

    response = get_response(model=llama_405, system_prompt=sys_prompt, user_prompt=usr_prompt)
    return response

def generate_custom_option(question: str, role: str):
    with Session(engine) as session:
        sys_prompt, usr_prompt = get_prompt(db=session, prompt_name='GET_CUSTOM_OPTIONS')
    
    usr_prompt = usr_prompt.replace('CUSTOM_QUESTION', question)
    usr_prompt = usr_prompt.replace('JOB_ROLE', role)

    response = json.loads(get_response(model=mixtral_model, system_prompt=sys_prompt, user_prompt=usr_prompt))
    return response

def analyze_resume(job_description: str, resume: str, usr_prompt: str, sys_prompt: str):
    try:
        usr_prompt = usr_prompt.replace('DESCRIPTON_JOB', job_description)
        usr_prompt = usr_prompt.replace('CANDIDATE_RESUME', resume)

        print("GOT PROMPT")
        response = get_response(model=llama_405, system_prompt=sys_prompt, user_prompt=usr_prompt)
        print("RESPONSE: ", response)
        return json.loads(response)
    except json.decoder.JSONDecodeError:
        return None