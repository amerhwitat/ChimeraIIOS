# Chimera Web Runtime

The userland web stack supports PHP, HTML5, CSS and JavaScript as first-class application runtimes.

- HTML/CSS are served as static assets and can be rendered by Aurora-compatible browsers.
- JavaScript runs in a sandboxed engine service.
- PHP runs behind the Chimera web service using a FastCGI-compatible process boundary.
- HTTP/1.1, HTTP/2 and HTTP/3 are exposed through a capability-controlled web service.
- Apache httpd is an optional integration profile; it is not linked into Koronos.
- Applications may use the Chimera Data Architecture through SQL/REST/CDC APIs.

Security boundaries: web code is untrusted userland code; filesystem, network, process and database access require explicit capabilities.
