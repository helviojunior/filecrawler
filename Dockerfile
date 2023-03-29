FROM sebp/elk:8.6.2 as compile
MAINTAINER Helvio Junior <helvio_junior@hotmail.com>

USER root

SHELL ["/bin/bash", "-xo", "pipefail", "-c"]

# Generate locale C.UTF-8
ENV LANG C.UTF-8
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Update and install dependencies
RUN apt update \
  && apt upgrade -y \
  && apt install -yqq --no-install-recommends \
      git \
      gcc \
      python3 \
      python3-pip \
      python3-dev \
      build-essential \
      libssl-dev \
      libffi-dev\
      python3-setuptools \
      unzip \
      default-jre \
      default-jdk \
      libmagic-dev \
      curl \
      gpg \
      vim \
  && apt clean all \
  && apt autoremove

# Install ELK
#RUN curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | gpg --dearmor -o /usr/share/keyrings/elastic.gpg
#RUN echo "deb [signed-by=/usr/share/keyrings/elastic.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | tee -a /etc/apt/sources.list.d/elastic-8.x.list
#RUN apt update \
#  && apt -yqq install elasticsearch kibana \
#  && apt clean all \
#  && apt autoremove

ENV ES_HOME /opt/elasticsearch

WORKDIR /tmp
RUN python3 -m pip install -U pip
#RUN python3 -m pip install -U filecrawler
RUN git clone https://github.com/helviojunior/filecrawler.git installer
RUN python3 -m pip install -U installer/
RUN python3 ./installer/scripts/config_elk.py

VOLUME ~/ /u01/
RUN mkdir -p /u01/.filecrawler/docker_es

VOLUME ~/.filecrawler/docker_es /var/lib/elasticsearch
VOLUME ~/.filecrawler/ /root/.filecrawler/
WORKDIR /root/

RUN filecrawler --create-config -v

#FROM ubuntu:jammy
EXPOSE 9200 80 443
WORKDIR /u01/filecrawler
#COPY --from=compile /opt/venv /opt/venv
#ENV PATH="/opt/venv/bin:$PATH"
ENV ES_HEAP_SIZE="2g"
ENV LS_HEAP_SIZE="1g"
VOLUME /var/lib/elasticsearch
ENTRYPOINT ["/usr/local/bin/start.sh"]
CMD ["filecrawler"]

#https://phoenixnap.com/kb/elk-stack-docker