#!/bin/bash
# postinst script for Fina Ergen
# This script runs after the package is installed.

set -e

case "$1" in
    configure)
        echo "Configuring Fina Ergen..."
        
        # Ensure the setup script is executable
        chmod +x /usr/lib/fina-ergen/scripts/fina_setup.sh
        
        # We try to run the setup script for the current user if we can detect one,
        # otherwise we just exit and let the app handle it on first run.
        # Note: running GUI scripts from postinst can be tricky due to X11/Wayland context.
        # A better approach is to have the app check if it's configured on first run.
        
        # To run it manually after install:
        # /usr/lib/fina-ergen/scripts/fina_setup.sh
    ;;

    abort-upgrade|abort-remove|abort-deconfigure)
    ;;

    *)
        echo "postinst called with unknown argument \`$1'" >&2
        exit 1
    ;;
esac

exit 0
