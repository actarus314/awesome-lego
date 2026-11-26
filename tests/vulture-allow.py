# Names that vulture (scripts/hygiene.py) cannot see used: methods and attributes that the standard library
# calls on the classes of the scripts. A name enters here only with the library that calls it.
_ = object
_.handle_data  # html.parser.HTMLParser
_.handle_endtag  # html.parser.HTMLParser
_.handle_startendtag  # html.parser.HTMLParser
_.log_message  # http.server.BaseHTTPRequestHandler
_.request_queue_size  # socketserver.TCPServer
_.redirect_request  # urllib.request.HTTPRedirectHandler
