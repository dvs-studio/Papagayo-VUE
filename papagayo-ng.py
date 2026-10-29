#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backward-compatibility wrapper forwarding execution to papagayo-vue.py.
Papagayo-VUE: Redeveloped by Victory Ukpong (2026).
"""

import os
import sys
import runpy

if __name__ == "__main__":
    target = os.path.join(os.path.dirname(os.path.abspath(__file__)), "papagayo-vue.py")
    runpy.run_path(target, run_name="__main__")
