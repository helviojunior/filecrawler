# Knows More

[![Build](https://github.com/helviojunior/filecrawler/actions/workflows/build_and_publish.yml/badge.svg)](https://github.com/helviojunior/filecrawler/actions/workflows/build_and_publish.yml)
[![Build](https://github.com/helviojunior/filecrawler/actions/workflows/build_and_test.yml/badge.svg)](https://github.com/helviojunior/filecrawler/actions/workflows/build_and_test.yml)
[![Downloads](https://pepy.tech/badge/filecrawler/month)](https://pepy.tech/project/filecrawler)
[![Supported Versions](https://img.shields.io/pypi/pyversions/filecrawler.svg)](https://pypi.org/project/filecrawler)
[![Contributors](https://img.shields.io/github/contributors/helviojunior/filecrawler.svg)](https://github.com/helviojunior/filecrawler/graphs/contributors)
[![PyPI version](https://img.shields.io/pypi/v/filecrawler.svg)](https://pypi.org/project/filecrawler/)
[![License: GPL-3.0](https://img.shields.io/pypi/l/filecrawler.svg)](https://github.com/helviojunior/filecrawler/blob/main/LICENSE)

FileCrawler officially supports Python 3.7+.

## Main features

* [x] List all file contents
* [x] Index file contents at Elasticsearch
* [x] Do OCR at several file types (with tika lib)
* [x] Look for hard-coded credentials
* [x] Much more...

### Parsers:
* [x] PDF files
* [X] Microsoft Office files (Word, Excel etc)
* [X] X509 Certificate files
* [X] Image files (Jpg, Png, Gif etc)
* [X] Java packages (Jar and war)
* [X] Disassembly APK Files with APKTool
* [X] Compressed files (zip, tar, gzip etc)
* [X] SQLite3 database

### Extractors:
* [X] AWS credentials
* [X] Github and gitlab credentials

## Installing

### Dependencies

```bash
apt install default-jre default-jdk libmagic-dev git
```

### Installing FileCrawler

Installing from last release

```bash
pip install -U filecrawler
```

Installing development package

```bash
pip install -i https://test.pypi.org/simple/ FileCrawler
```

## Running

### Config file

Create a sample config file with default parameters

```bash
filecrawler --create-config -v
```

Edit the configuration file **config.yml** with your desired parameters

**Note:** You must adjust the Elasticsearch URL parameter before continue

### Run

```bash
# Integrate with ELK
filecrawler --index-name filecrawler --path /mnt/client_files -T 30 -v --elastic

# Just save leaks locally
filecrawler --index-name filecrawler --path /mnt/client_files -T 30 -v --local -o /home/out_test
```

## Help

```bash
$ filecrawler -h

File Crawler v0.1.3 by Helvio Junior
File Crawler index files and search hard-coded credentials.
https://github.com/helviojunior/filecrawler
    
usage: 
    filecrawler module [flags]

Available Integration Modules:
  --elastic                  Integrate to elasticsearch
  --local                    Save leaks locally

Global Flags:
  --index-name [index name]  Crawler name
  --path [folder path]       Folder path to be indexed
  --config [config file]     Configuration file. (default: ./fileindex.yml)
  --db [sqlite file]         Filename to save status of indexed files. (default: ~/.filecrawler/{index_name}/indexer.db)
  -T [tasks]                 number of connects in parallel (per host, default: 16)
  --create-config            Create config sample
  --clear-session            Clear old file status and reindex all files
  -h, --help                 show help message and exit
  -v                         Specify verbosity level (default: 0). Example: -v, -vv, -vvv

Use "filecrawler [module] --help" for more information about a command.

```

# How-to install ELK from scratch

[Installing Elasticsearch](https://github.com/helviojunior/filecrawler/blob/main/INSTALL_ELK.md)

# Credits

This project was inspired of:

1. [FSCrawler](https://fscrawler.readthedocs.io/)
2. [Gitleaks](https://gitleaks.io/)

**Note:** Some part of codes was ported from this 2 projects

# To do

[Check the TODO file](https://github.com/helviojunior/filecrawler/blob/main/TODO.md)