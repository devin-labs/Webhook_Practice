FROM python
WORKDIR /app
COPY wsgi.py .
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY gunicorn.conf.py .
COPY webhook_reciever.py .
CMD ["gunicorn", "-c", "gunicorn.conf.py", "wsgi:app"]