#!/bin/sh

# Default to empty object if vars are missing
echo "window.__ENV = {" > ./public/__env.js

# Append env vars
# We primarily care about NEXT_PUBLIC_API_URL
if [ -n "$NEXT_PUBLIC_API_URL" ]; then
  echo "  NEXT_PUBLIC_API_URL: \"$NEXT_PUBLIC_API_URL\"," >> ./public/__env.js
else 
  echo "  NEXT_PUBLIC_API_URL: \"\"," >> ./public/__env.js
fi

echo "};" >> ./public/__env.js

# Execute the main container command
exec "$@"
