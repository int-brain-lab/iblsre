#!/bin/bash
set -e
# Create folder with current date (YYYY-MM-DD format)
folder_name=$HOME/monitor/$(date +"%Y-%m-%d")
mkdir -p "$folder_name"

# Create filename with current time (HH-MM-SS format)
file_name_top=apache_$(date +"%H%M").txt
file_name_apache=top_$(date +"%H%M").txt

# Monitor top command output
top -b -n 1 -o %MEM | head -40 > "$folder_name/$file_name_top"

# Monitor apache server
docker exec alyx_apache /bin/bash -c "apachectl status" > "$folder_name/$file_name_apache"
