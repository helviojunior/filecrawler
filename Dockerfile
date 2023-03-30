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
RUN echo FileCrawler > /etc/hostname

WORKDIR /tmp
RUN cp /etc/init.d/elasticsearch init.sh
RUN cat init.sh | sed 's|^DATA_DIR.*|DATA_DIR=/u01/.filecrawler/es_data|' > /etc/init.d/elasticsearch
RUN python3 -m pip install -U pip
#RUN python3 -m pip install -U filecrawler
RUN git clone https://github.com/helviojunior/filecrawler.git installer
RUN python3 -m pip install -U installer/
RUN python3 ./installer/scripts/config_elk.py
RUN cp ./installer/scripts/config_elk.py /root/

RUN mkdir /u01/
RUN mkdir /u02/

WORKDIR /u02/

RUN printf "#!/bin/bash \n \
# Starter \n \
mkdir -p /u01/.filecrawler/es_data/ 2>/dev/null \n \
python3 /root/config_elk.py \n \
chown -R elasticsearch:elasticsearch /u01/ \n \
/etc/init.d/elasticsearch start \n \
/etc/init.d/kibana start \n \
/bin/bash \n \
/etc/init.d/elasticsearch stop \n \
/etc/init.d/kibana stop\n" > /root/start.sh

RUN chmod +x /root/start.sh

#RUN filecrawler --create-config -v

#FROM ubuntu:jammy
EXPOSE 9200 80 443
#COPY --from=compile /opt/venv /opt/venv
#ENV PATH="/opt/venv/bin:$PATH"
ENV ES_HEAP_SIZE="2g"
ENV LS_HEAP_SIZE="1g"
ENV KBN_PATH_CONF=/opt/kibana/config/
ENV LOGSTASH_START=0
ENTRYPOINT ["/root/start.sh"]

#https://phoenixnap.com/kb/elk-stack-docker