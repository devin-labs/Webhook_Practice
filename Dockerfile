FROM python
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY webhook_reciever.py .
CMD ["python", "webhook_reciever.py"]