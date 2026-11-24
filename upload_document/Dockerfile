FROM python:3.13-slim

WORKDIR /upload_document

COPY ./upload_document/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ./upload_document/. .

EXPOSE 7002
ENTRYPOINT ["python", "main.py"]
