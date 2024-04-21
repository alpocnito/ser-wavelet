FROM python:3.8.10

RUN apt update && apt install -y    \
    build-essential                 \
    libsox-dev                      \
    portaudio19-dev                 \
    python3-pyaudio


WORKDIR /ser-wavelet

COPY ./requirements ./requirements
COPY ./data ./data
COPY ./src ./src
COPY ./checkpoints2 ./checkpoints2


# ser-wavelet stuff
RUN pip install --upgrade pip
RUN pip install -r requirements/pip.txt

# reader stuff
RUN pip install influxdb_client
COPY ./analyze.py ./analyze.py
COPY ./read.py ./read.py

CMD ["python3", "read.py"]
