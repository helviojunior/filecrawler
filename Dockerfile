FROM sebp/elk:latest as compile
MAINTAINER Helvio Junior <helvio_junior@hotmail.com>

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
  && apt clean all \
  && apt autoremove

# Install ELK
#RUN curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | gpg --dearmor -o /usr/share/keyrings/elastic.gpg
#RUN echo "deb [signed-by=/usr/share/keyrings/elastic.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | tee -a /etc/apt/sources.list.d/elastic-8.x.list
#RUN apt update \
#  && apt -yqq install elasticsearch kibana \
#  && apt clean all \
#  && apt autoremove

RUN mkdir -p /u01/filecrawler
RUN mkdir -p /u01/es_data/elasticsearch
WORKDIR /u01/filecrawler
RUN python3 -m pip install -U pip
#RUN python3 -m pip install -U filecrawler
RUN git clone https://github.com/helviojunior/filecrawler.git installer
RUN python3 -m pip install -U installer/
WORKDIR /u01/filecrawler
RUN python3 ./installer/scripts/config_elk.py
#RUN systemctl enable elasticsearch \
#    && systemctl start elasticsearch \
#    && systemctl enable kibana \
#    && systemctl start kibana
RUN filecrawler --create-config -v
ENV ES_HOME /opt/elasticsearch


#FROM ubuntu:jammy
EXPOSE 9200 80 443
WORKDIR /u01/filecrawler
#COPY --from=compile /opt/venv /opt/venv
#ENV PATH="/opt/venv/bin:$PATH"
ENTRYPOINT ["/bin/bash"]

#https://phoenixnap.com/kb/elk-stack-docker