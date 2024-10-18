#Base image
FROM python:3.10

#Set the working directory
WORKDIR /app

#Copy required files
COPY pyproject.toml poetry.lock* ./

#Install poetry
RUN pip install poetry &&  poetry install

#Copy the rest of the application code
COPY . /app/

#Expose port 8000
EXPOSE 8000

#Start the application when container is started
CMD ["poetry", "run", "uvicorn", "engage_api.main:app", "--host", "0.0.0.0", "--port", "8010"]