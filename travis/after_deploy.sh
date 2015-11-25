#!/bin/bash -e

travis/doindex.py > ~/index.html

git fetch origin gh-pages:gh-pages
git checkout gh-pages

cp ~/index.html index/c2cgeoportal/index.html
git add index/c2cgeoportal/index.html
git commit -m "Update index"
git push origin gh-pages
