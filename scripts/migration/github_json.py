"""Decode gh --paginate JSON streams without depending on newer --slurp flags."""
import json


def json_pages(source):
    decoder = json.JSONDecoder()
    pages = []
    offset = 0
    while offset < len(source):
        while offset < len(source) and source[offset].isspace():
            offset += 1
        if offset == len(source):
            break
        value, offset = decoder.raw_decode(source, offset)
        if not isinstance(value, (list, dict)):
            raise ValueError("Expected JSON array/object from GitHub pagination")
        pages.append(value)
    return pages
