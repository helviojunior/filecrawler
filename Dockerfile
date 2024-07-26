FROM ubuntu:jammy
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
      jq \
  && apt clean all \
  && apt autoremove

RUN echo FileCrawler > /etc/hostname

WORKDIR /tmp
ENV GIT_SSL_NO_VERIFY="true"
RUN python3 -m pip install -U pip && \
    git clone https://github.com/helviojunior/filecrawler.git installer && \
    python3 -m pip install -U installer/ && \
    mkdir -p /u01/ && mkdir /u02/ && chmod -R 777 /u0{1,2}/ && \
    ln -s /u01/ /root/.filecrawler && \
    rm -rf /tmp/* && \
    filecrawler -h

WORKDIR /u02/

ENTRYPOINT ["filecrawler"]
