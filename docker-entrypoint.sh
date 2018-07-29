#!/bin/bash

# Check if Subtle user exists, execute 'first run' commands if not
if ! grep -q subtle /etc/passwd; then
	# Check environment variables
	if [ -z ${OS_PASSWORD+x} ]; then OS_PASSWORD=""; fi
	if [ -z ${OS_HASH+x} ]; then OS_HASH=""; fi

	# Add Subtle user
	adduser -D -u $PUID -g $PGID subtle && chown $PUID:$PGID -R /opt/subtle

	# Add OS credentials to config file
	cd /opt/subtle
	sed -i "s/your OpenSubtitles username/$OS_USER/" config.json && \
			sed -i "s/your OpenSubtitles password (will be hashed on first run)/$OS_PASSWORD/" config.json && \
	        sed -i 's@"hash": ""@"hash": "'$OS_HASH'"@' config.json
fi

# Start Subtle
sudo -u subtle gunicorn -b 0.0.0.0:8979 Subtle:app