FROM python:3.9-slim
WORKDIR /app
COPY ./requirements.txt /app
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
ENV FLASK_APP=app.py
ENV APP_SETTINGS=settings.cfg
CMD ["flask", "run", "--host", "0.0.0.0"]
