ARG PYTHON_VERSION=3.12.0
FROM python:${PYTHON_VERSION}-slim as base

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m pip install -U channels["daphne"]
COPY . .

EXPOSE 8000

CMD ["sh", "-c", "python manage.py runserver 0.0.0.0:8000 & python manage.py rqworker"]