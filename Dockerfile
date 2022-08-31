FROM rust:slim-bullseye as builder

LABEL maintainer="Antony <dentad@users.noreply.github.com>"
ENV DEBIAN_FRONTEND="noninteractive"

RUN apt-get update; \
apt-get -y install --no-install-recommends python-is-python3 python3-minimal python3-venv python3-distutils python3-pip python3-wheel; \
apt-get -y install --no-install-recommends libxml2 libxslt1.1 zlib1g; \
apt-get -y install --no-install-recommends python-dev-is-python3 python3-dev python-pip-whl binutils binfmt-support make gcc g++ libxml2-dev libxslt1-dev zlib1g-dev patch

RUN pip install --user maturin
ENV PATH="/root/.local/bin:$PATH"

RUN mkdir -p /working
COPY ./ /working/
WORKDIR /working
RUN maturin build --bindings pyo3 --compatibility linux --release --jobs 4

RUN mkdir -p /homesme
RUN useradd --home-dir /homesme sme
RUN chown -R sme: /homesme
USER sme

RUN mkdir -p /homesme/venvsme
RUN python3 -m venv /homesme/venvsme
ENV PATH="/homesme/venvsme/bin:$PATH"
ENV VIRTUAL_ENV="/homesme/venvsme"
RUN pip install --requirement /working/requirements.txt
RUN pip install /working/target/wheels/statisticalme-*.whl
RUN rm -rf "/homesme/venvsme/share/python-wheels"

FROM debian:bullseye-slim

LABEL maintainer="Antony <dentad@users.noreply.github.com>"
ENV DEBIAN_FRONTEND="noninteractive"

RUN apt-get update; \
apt-get -y full-upgrade --no-install-recommends; \
apt-get -y install --no-install-recommends python-is-python3 python3-minimal python3-venv python3-distutils; \
apt-get -y autoremove; \
apt-get clean; \
find /var/lib/apt/lists -type f -not -empty -delete

RUN mkdir -p /homesme
RUN useradd --home-dir /homesme sme
RUN chown -R sme: /homesme
USER sme
WORKDIR /homesme

RUN mkdir -p /homesme/venvsme
COPY --from=builder /homesme/venvsme /homesme/venvsme
ENV PATH="/homesme/venvsme/bin:$PATH"
ENV VIRTUAL_ENV="/homesme/venvsme"

RUN mkdir -p /homesme/var

ENTRYPOINT ["python3", "-m", "statisticalme"]
