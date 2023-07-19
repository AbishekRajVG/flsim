#!/bin/bash

log_file=$1

watch -n 1 "printf \"Current Round: `grep 'Round [0-9]\+\/[0-9]\+' $1 | tail -1` \n\n\" && printf \"Live logs: (ctrl + c to exit)\n\n\" && tail -40 $1"
