FROM python:latest
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY processing_functions.py .
COPY gunicorn.conf.py .
COPY app.py .
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:app"]