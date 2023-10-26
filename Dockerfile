FROM python:3.10.12

WORKDIR /usr/src/app

COPY ./aiohttp_server .

RUN pip install -r requirements.txt

CMD python3 app.py