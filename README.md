# README

## TL;DR

Yuque-exporter is a simple tools to export Yuque repo to GitHub.

## Table of Contents

- [Background](#background)
- [Install](#install)
- [Usage](#usage)
- [Related Efforts](#related-efforts)
- [Maintainers](#maintainers)
- [License](#license)

## Background

A tiny and tailored Python3 exporter downloads Yuque repo documents in format of markdown through Yuque OpenAPI V2.0,
and archive them to GitHub repo. It was inspired by [M1r0ku/YuqueExport](https://github.com/M1r0ku/YuqueExport).

Now it run as a Kubernetes Cronjob, synchronizing every 8 hours, instead of Linux crontab in early weeks.

## Install

### Prerequisites

It is written in Python 3.11, and it is available to compile as a binary executable.

- Python 3.11+
- Pipenv
- Git
- PyCharm (Recommended)

```bash
git clone https://github.com/leryn1122/yuque-exporter.git

make install build
```

## Usage

Apply for Yuque token and write your username with token in the config file `~/.yuque/config`.

```bash
pipenv run python3 src/main.py --log-level=INFO --yuque --git-push

dist/yuque-export --log-level=INFO --yuque --git-push
```

It's recommended to run as a Kubernetes Cronjob. Fill in `deploy/raw/secret.yaml` with the content of `~/.yuque/config`. 

```bash
kubectl create ns cron

kubectl apply -f deploy/raw/secret.yaml  -n cron
kubectl apply -f deploy/raw/cronjob.yaml -n cron
```

## Related Efforts

Those repos are referenced on:

- [M1r0ku/YuqueExport](https://github.com/M1r0ku/YuqueExport)

## Maintainers

[@Leryn](https://github.com/leryn1122).

## License

[MIT](LICENSE-MIT) © Leryn


