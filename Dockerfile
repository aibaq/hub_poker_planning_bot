FROM python:3.10

WORKDIR /code

COPY ./requirements.txt /code
RUN pip install --upgrade pip
RUN pip install -r requirements.txt


# Copy source code
COPY . /code

CMD python main.py
