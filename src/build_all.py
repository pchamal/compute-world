#!/usr/bin/env python3
# Phase 1 rebuild: homepage, country pages, OG images, thesis, license, data, sitemap.
# Run from repo root:  python3 src/build_all.py
# Writes generated HTML/OG/txt into the repo so Cloudflare Pages can serve them statically.
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
os.chdir(HERE)  # gdc_data / cnw_computed resolve relative to src/

from cnw_lib import assemble_countries
import build_home
import build_countries


def main():
    countries, as_of, wire, _ = assemble_countries()
    build_home.build(root=ROOT, countries=countries, as_of=as_of, wire=wire)
    os.chdir(HERE)
    build_countries.build(root=ROOT)
    print("phase 1 rebuild complete")


if __name__ == "__main__":
    main()
