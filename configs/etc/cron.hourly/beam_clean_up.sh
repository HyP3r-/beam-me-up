#!/usr/bin/env bash

upload_dir=/usr/local/lib/beam/beam_web/static/upload

find "$upload_dir" -mtime +5 -exec rm {} \; || exit 1

exit 0