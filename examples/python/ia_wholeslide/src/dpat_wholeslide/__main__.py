#!/usr/bin/env python

if __name__ == "__main__":
    from dpat_wholeslide.webserver import app, BIND_PORT

    app.run(host="0.0.0.0", port=BIND_PORT, debug=False)
