FROM python:3.13-slim

WORKDIR /api_gateway

COPY ./api_gateway/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ./api_gateway/. .
COPY ./db ./db

EXPOSE 7000
ENTRYPOINT ["python", "main.py"]
