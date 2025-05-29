#!/bin/bash

mkdir -p ~/.streamlit/

echo "\
[general]\n\
email = \"your-email@domain.com\"\n\
" > ~/.streamlit/credentials.toml

echo "\
[server]\n\
headless = true\n\
enableCORS=false\n\
port = \$PORT\n\
[theme]\n\
base = \"light\"\n\
primaryColor = \"#667eea\"\n\
backgroundColor = \"#ffffff\"\n\
secondaryBackgroundColor = \"#f8f9ff\"\n\
textColor = \"#262730\"\n\
[browser]\n\
gatherUsageStats = false\n\
" > ~/.streamlit/config.toml 