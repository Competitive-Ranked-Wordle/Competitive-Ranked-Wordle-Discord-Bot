FROM python:3.12.3-alpine
WORKDIR /wordlebot
COPY ./requirements.txt /wordlebot/requirements.txt
RUN pip3 install --no-cache-dir --upgrade -r requirements.txt
COPY ./app.py /wordle/app.py
COPY ./bin/ /wordle/bin
CMD ["python3", "app.py", "app.py"]