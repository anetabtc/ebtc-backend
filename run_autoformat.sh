#!/bin/bash
yapf -i -r --style .style.yapf server
yapf -i -r --style .style.yapf tests
yapf -i -r --style .style.yapf .
docformatter -i -r .
isort .