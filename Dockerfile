FROM python:3.7-slim
ENV PYTHONUNBUFFERED=1 \
    LANG="C.UTF-8" \
    LC_ALL="C.UTF-8"

# to update ubuntu to correctly run apt install
# install chrome driver and set PATH
RUN apt-get update -y && \
    apt install chromium-driver -y

# install releated python package
COPY requirements.txt /tmp/requirements.txt

# install python package
RUN pip install --no-cache-dir -r /tmp/requirements.txt

#COPY . /ddjob
#WORKDIR /ddjob
