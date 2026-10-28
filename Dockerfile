FROM astrocrpublic.azurecr.io/runtime:3.2-1

# Switch to root for setup
USER root

# INSTALACAO DA LIBAIO DO ORACLE PARA O DEBIAN-TRIXIE
RUN apt-get update && \
    apt-get install -y libaio-dev unzip && \
    ln -s /usr/lib/x86_64-linux-gnu/libaio.so.1t64 /usr/lib/x86_64-linux-gnu/libaio.so.1 || true && \
    ldconfig && \
    rm -rf /var/lib/apt/lists/*

# Baixa e instala Oracle Instant Client
RUN curl -o /tmp/instantclient.zip https://download.oracle.com/otn_software/linux/instantclient/2390000/instantclient-basic-linux.x64-23.9.0.25.07.zip \
    && unzip /tmp/instantclient.zip -d /opt/oracle \
    && rm /tmp/instantclient.zip

ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_23_9

USER astro

COPY requirements.txt .
RUN pip install -r requirements.txt

WORKDIR /usr/local/airflow

COPY dags/ dags/
COPY include/ include/
COPY plugins/ plugins/