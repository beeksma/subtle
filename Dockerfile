FROM alpine
LABEL maintainer "Victor Beek <beeksma@pm.me>"

# Set environment variables
ENV ROOT='/video'

# Set volumes and exposed ports
VOLUME $ROOT
EXPOSE 8979

# Install dependencies and Subtle
RUN apk add --no-cache bash sudo git python3 python3-dev gcc g++ libffi-dev && \
        python3 -m ensurepip && \
        rm -r /usr/lib/python*/ensurepip && \
        pip3 install --upgrade pip setuptools && \
        if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
        if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
        rm -r /root/.cache && \
        git clone https://github.com/beeksma/subtle.git /opt/subtle && \
        pip3 install -r /opt/subtle/requirements.txt

# Configure Subtle
WORKDIR /opt/subtle
RUN cp config.json.sample config.json && \
        sed -i 's@"root": ""@"root": "'$ROOT'"@' config.json && \
        cp ./docker-entrypoint.sh / && chmod +x /docker-entrypoint.sh

# Set entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"]