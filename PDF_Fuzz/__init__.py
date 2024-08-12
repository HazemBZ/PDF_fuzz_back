from fuzz.search import Search

if Search.es is None:
    Search.connect()