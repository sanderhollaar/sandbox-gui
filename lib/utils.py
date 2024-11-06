#!/usr/bin/env python
import random


def randid():
    allowed_chars = 'abcdefghijklmnoprstuvwxyz1234567890'
    length = 16
    return ''.join([random.choice(allowed_chars) for n in range(length)])
