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
      wget \
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
ENV GIT_SSL_NO_VERIFY="true"
RUN cp /etc/init.d/elasticsearch init.sh && \
    cat init.sh | sed 's|^DATA_DIR.*|DATA_DIR=/u01/es_data|' > /etc/init.d/elasticsearch && \
    python3 -m pip install -U pip && \
    git clone https://github.com/helviojunior/filecrawler.git installer && \
    VER=$(curl -s "https://raw.githubusercontent.com/chrismattmann/tika-python/master/tika/tika.py" | grep 'TIKA_VERSION' | grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' || echo '2.6.0') && \
    SERVER_HASH=$(curl -s "http://search.maven.org/remotecontent?filepath=org/apache/tika/tika-server-standard/$VER/tika-server-standard-$VER.jar.sha1") && \
    wget -nv -O "./installer/filecrawler/libs/bin/tika-server.jar" "http://search.maven.org/remotecontent?filepath=org/apache/tika/tika-server-standard/$VER/tika-server-standard-$VER.jar" && \
    echo "${SERVER_HASH} ./installer/filecrawler/libs/bin/tika-server.jar" | sha1sum -c - && \
    python3 -m pip install -U installer/ && \
    python3 ./installer/scripts/config_elk.py && \
    cp ./installer/scripts/config_elk.py /root/ && \
    mkdir -p /u01/ && mkdir /u02/ && chmod -R 777 /u0{1,2}/

WORKDIR /u02/

RUN printf "#!/bin/bash \n \
# Starter \n \
mkdir -p /u01/es_data/ 2>/dev/null \n \
python3 /root/config_elk.py \n \
chown -R elasticsearch:elasticsearch /u01/ \n \
ln -s /u01/ /root/.filecrawler  \n \
/etc/init.d/elasticsearch start \n \
/etc/init.d/kibana start \n \
/bin/bash \n \
/etc/init.d/elasticsearch stop \n \
/etc/init.d/kibana stop\n" > /root/start.sh

RUN chmod +x /root/start.sh

#RUN filecrawler --create-config -v

#FROM ubuntu:jammy
EXPOSE 80/tcp
EXPOSE 443/tcp
EXPOSE 9200/tcp
#COPY --from=compile /opt/venv /opt/venv
#ENV PATH="/opt/venv/bin:$PATH"
ENV ES_HEAP_SIZE="6g"
ENV LS_HEAP_SIZE="125m"
ENV KBN_PATH_CONF=/opt/kibana/config/
ENV LOGSTASH_START=0
ENV MAX_MAP_COUNT=262144
ENTRYPOINT ["/root/start.sh"]

#https://phoenixnap.com/kb/elk-stack-docker