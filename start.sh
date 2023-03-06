#!/bin/sh

kill $(rq info | grep worker | awk '{print $2}')

concurrently "rq worker" "rq-dashboard"
