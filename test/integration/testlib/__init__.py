#!/usr/bin/env python3

import sys

# List main 'exports' here to encourage the user not to depend on our exact structure.
from .proc import Tinc
from .script import Script
from .log import log

assert sys.version_info >= (3, 6)
