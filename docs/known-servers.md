# Known OGC API - Connected Systems Servers

The following is a list of servers which are known to implement the OGC API - Connected Systems standard. Feel free to
[open an issue](https://github.com/kurtraschke/pyRFC3339/blob/main/LICENSE.txt) if you want to add more servers to the list

1. <http://45.55.99.236:8080/sensorhub/api> - public instance of sensor hub; it contains Systems, Deployments, Procedures and Datastreams; the Systems are geo located.
2. <https://129-80-248-53.sslip.io/sensorhub/api/> - in addition to other entities, it contains Sampling Features that can be added to a map.
3. <https://129-80-248-53.sslip.io/csapi-go-head/> - in addition to other entities, it contains Sampling Features that can be added to a map.
4. <https://129-80-248-53.sslip.io/csapi-go-v2/> - this deployment only contains Sampling Features.
5. <https://os4csapi-osh.duckdns.org/sensorhub/api> - it contains tons of data for systems, deployments and other resources - it is protected by
  auth (credentials supplied offline).
6. <https://csa.demo.52north.org/> - as of now, this server's TLS certificate is not valid, so one needs to skip TLS
  verification in order to use it.
7. <https://api.georobotix.io/ogc/demo1/api/systems> - the [opensensorhub docs] claim this is a good demo server
  for CSAPI - seems to be down though (responds with HTTP 502)
8. <https://os4csapi-osh.duckdns.org/sensorhub/api> - it contains tons of data for systems, deployments and other resources - it is protected by
  auth (credentials supplied offline)

!!! NOTE

    To work with servers 1, 2 and 5 you will need to enable the `f` parameter for content negotiation (Connection Configuration -> Advanced Settings).

[opensensorhub docs]: https://docs.opensensorhub.org/docs/osh-connect/connected-systems#hands-on-guide-and-examples
