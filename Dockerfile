FROM continuumio/miniconda3:24.3.0-0

RUN apt update \
    && apt install -y build-essential libsox-dev portaudio19-dev python3-pyaudio \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/notebooks/ser-wavelet

# Set user
# ENV USER ron
# RUN useradd -m $USER
# RUN chown -R $USER: /opt/conda /opt/notebooks
# USER $USER

RUN conda create -y --name ser python=3.8.10

SHELL ["conda", "run", "--no-capture-output", "-n", "ser", "/bin/bash", "-c"]

RUN conda install jupyter -y

COPY ./requirements ./requirements
RUN pip install -r ./requirements/pip.txt

COPY ./config ./config
COPY ./data ./data
COPY ./examples ./examples
COPY ./notebooks ./notebooks
COPY ./src ./src
COPY ./checkpoints2 ./checkpoints2

CMD jupyter notebook \
    --notebook-dir=/opt/notebooks --ip='*' --port=8888 \
    --no-browser --allow-root --NotebookApp.token=''
