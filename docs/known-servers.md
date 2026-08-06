# Known OGC API - Connected Systems Servers

The following is a list of servers which are known to implement the OGC API - Connected Systems standard. Feel free to
[open an issue](https://github.com/kurtraschke/pyRFC3339/blob/main/LICENSE.txt) if you want to add more servers to the list

- http://45.55.99.236:8080/sensorhub/api - seems to have been freshly set up - let's use this one - it is protected by
  auth (credentials supplied offline)
- https://csa.demo.52north.org/ - as of now, this server's TLS certificate is not valid, so one needs to skip TLS
  verification in order to use it.
- https://api.georobotix.io/ogc/demo1/api/systems - the [opensensorhub docs] claim this is a good demo server
  for CSAPI - seems to be down though (responds with HTTP 502)
- https://os4csapi-osh.duckdns.org/sensorhub/api - it contains tons of data for systems, deployments and other resources - it is protected by
  auth (credentials supplied offline)
- 
  [opensensorhub docs]: https://docs.opensensorhub.org/docs/osh-connect/connected-systems#hands-on-guide-and-examples
