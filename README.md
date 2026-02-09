# QGIS OACS Plugin


## Development, installation and usage

Check out the docs at:

https://byteroad.github.io/qgis-oacs-plugin/


### Issues and feature requests

Please use the GitHub issue tracker at

https://github.com/byteroad/qgis-oacs-plugin/issues


### Demo servers

The following are known OACS servers:

- http://45.55.99.236:8080/sensorhub/api - seems to have been freshly set up - let's use this one - it is protected by
  auth (credentials supplied offline)
- https://csa.demo.52north.org/ - as of now, this server's TLS certificate is not valid, so one needs to skip TLS 
  verification in order to use it.
- https://api.georobotix.io/ogc/demo1/api/systems - the [opensensorhub docs] claim this is a good demo server 
  for OACS - seems to be down though (responds with HTTP 502)

[opensensorhub docs]: https://docs.opensensorhub.org/docs/osh-connect/connected-systems#hands-on-guide-and-examples



## Icons

This plugin uses some icons from the google material symbols library. These are distributed using 
the [Apache License Version 2.0](https://www.apache.org/licenses/LICENSE-2.0), as per the notice at:

https://developers.google.com/fonts/docs/material_symbols#licensing

List of Google material icons used:

- [Circle](https://fonts.google.com/icons?selected=Material+Symbols+Outlined:circle:FILL@0;wght@400;GRAD@0;opsz@24&icon.query=circle&icon.size=24&icon.color=%231f1f1f)
- [Deployed Code](https://fonts.google.com/icons?selected=Material+Symbols+Outlined:deployed_code:FILL@0;wght@400;GRAD@0;opsz@24&icon.query=deploy&icon.size=24&icon.color=%231f1f1f)
- [Eye Tracking](https://fonts.google.com/icons?selected=Material+Symbols+Outlined:eye_tracking:FILL@0;wght@400;GRAD@0;opsz@24&icon.query=measurement&icon.size=24&icon.color=%231f1f1f)
- [Graph 3](https://fonts.google.com/icons?selected=Material+Symbols+Outlined:graph_3:FILL@0;wght@400;GRAD@0;opsz@24&icon.query=node&icon.size=24&icon.color=%231f1f1f)
- [Labs](https://fonts.google.com/icons?selected=Material+Symbols+Outlined:labs:FILL@0;wght@400;GRAD@0;opsz@24&icon.query=sampl&icon.size=24&icon.color=%231f1f1f)
- [Lab Panel](https://fonts.google.com/icons?selected=Material+Symbols+Outlined:lab_panel:FILL@0;wght@400;GRAD@0;opsz@24&icon.query=sample&icon.size=24&icon.color=%231f1f1f)
- [Location On](https://fonts.google.com/icons?selected=Material+Symbols+Outlined:location_on:FILL@0;wght@400;GRAD@0;opsz@24&icon.query=location&icon.size=24&icon.color=%231f1f1f)
- [Manufacturing](https://fonts.google.com/icons?selected=Material+Symbols+Outlined:manufacturing:FILL@0;wght@400;GRAD@0;opsz@24&icon.query=machine&icon.size=24&icon.color=%231f1f1f)
- [Search](https://fonts.google.com/icons?selected=Material+Symbols+Outlined:search:FILL@0;wght@400;GRAD@0;opsz@24&icon.query=search&icon.size=24&icon.color=%231f1f1f)
- [Sensors Krx](https://fonts.google.com/icons?selected=Material+Symbols+Outlined:sensors_krx:FILL@0;wght@400;GRAD@0;opsz@24&icon.query=machine&icon.size=24&icon.color=%231f1f1f)
- [Stream](https://fonts.google.com/icons?selected=Material+Symbols+Outlined:stream:FILL@0;wght@400;GRAD@0;opsz@24&icon.query=data+stream&icon.size=24&icon.color=%231f1f1f)
- [Stadia Controller](https://fonts.google.com/icons?selected=Material+Symbols+Outlined:stadia_controller:FILL@0;wght@400;GRAD@0;opsz@24&icon.query=control&icon.size=24&icon.color=%231f1f1f)
- [Table](https://fonts.google.com/icons?selected=Material+Symbols+Outlined:table:FILL@0;wght@400;GRAD@0;opsz@24&icon.query=table&icon.size=24&icon.color=%231f1f1f)
- [Tools Ladder](https://fonts.google.com/icons?selected=Material+Symbols+Outlined:tools_ladder:FILL@0;wght@400;GRAD@0;opsz@24&icon.query=construct&icon.size=24&icon.color=%231f1f1f)


## Parsing of datetimes

The code that parses raw date-times has been lightly adapted from 
the [pyRFC3339](https://github.com/kurtraschke/pyRFC3339) project. This is done in order to keep the plugin from
having to rely on third-party Python packages being installed, which can sometimes pose a problem for end users.
