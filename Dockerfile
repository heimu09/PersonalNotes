FROM python:3.10-slim

WORKDIR /app

COPY Pipfile Pipfile.lock ./

RUN pip install pipenv && pipenv install --system --deploy

COPY . .

EXPOSE 8000

CMD ["uvicorn", "PersonalNotes.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
