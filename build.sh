#!/bin/bash

key="audio-video-tools"
orgOpt=""
token=$SQ_TOKEN
if [ "$SQ_URL" == "https://sonarcloud.io" ]; then
  key="okorach_audio-video-tools"
  orgOpt="-Dsonar.organization=okorach-github"
  token=$SCLOUD_TOKEN_AV_TOOLS
fi

buildDir="build"
[ ! -d $buildDir ] && mkdir $buildDir
pylintReport="$buildDir/pylint-report.out"
banditReport="$buildDir/bandit-report.json"
flake8Report="$buildDir/flake8-report.out"

if [ "$1" != "-nolint" ]; then
  echo "Running pylint"
  rm -f $pylintReport
  pylint *.py */*.py -r n --msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}" | tee $pylintReport
  re=$?
  if [ "$re" == "32" ]; then
    >&2 echo "ERROR: pylint execution failed, errcode $re, aborting..."
    exit $re
  fi

  echo "Running flake8"
  rm -f $flake8Report
  flake8 . >$flake8Report

  echo "Running bandit"
  rm -f $banditReport
  bandit -f json -r . >$banditReport
else
  shift
fi

sonar-scanner \
  -Dsonar.projectKey=$key \
  -Dsonar.host.url=$SQ_URL \
  -Dsonar.login=$token \
  -Dsonar.python.flake8.reportPaths=$flake8Report \
  -Dsonar.python.pylint.reportPath=$pylintReport \
  -Dsonar.python.bandit.reportPaths=$banditReport \
  $orgOpt $*
