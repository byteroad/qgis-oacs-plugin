QGIS OACS Plugin


## Development

> ![warning]
> 
> This plugin is being developed on an ubuntu 24.04 machine. These instructions are not guaranteed to work 
> on a different system. Moreover, they will very likely fail on a Windows system

1. Install [QGIS](https://qgis.org/). Be sure to get at the minimum version 3.44;

1. Create a custom QGIS profile for development - This is not strictly necessary but helps with keeping your main 
   QGIS workspace clean. Use the QGIS GUI for this (Settings -> User Profiles -> New Profile...). For the sake of 
   these instructions, let's pretend you named your profile `my-profile`.

1. Install the pyqt5 dev tools, in order to gain access to the `pyrcc5` utility:

   ```shell
   sudo apt install pyqt5-dev-tools
   ```

1. Install [uv](https://docs.astral.sh/uv/);

1. Clone this repo;

1. Use the provided `plugin-admin` CLI utility to create a virtualenv and get the QGIS Python bindings in it:

   ```shell
   uv plugin-admin --qgis-profile my-profile install-qgis-into-venv
   ```

1. Now you can work on the plugin code

1. Install the plugin with:

   ```shell
   uv plugin-admin --qgis-profile my-profile install
   ```
   

### Demo servers

The following are known OACS servers:

- https://csa.demo.52north.org/ - as of now, this server's TLS certificate is not valid, so one needs to skip TLS 
  verification in order to use it (not sure how to do this in QGIS yet). The server also seems to not respond to its
  own advertised links (for example https://csa.demo.52north.org/collections/all_systems declares the existence of 
  a `/systems` sub-path, but requests to it return HTTP 404), so perhaps it is not in a good shape at the moment
- https://api.georobotix.io/ogc/demo1/api/systems - the [opensensorhub docs] claim this is a good demo server 
  for OACS - seems to be down though (responds with HTTP 502)

[opensensorhub docs]: https://docs.opensensorhub.org/docs/osh-connect/connected-systems#hands-on-guide-and-examples



## Icons

This plugin uses some icons from the google material symbols library. These are distributed using 
the [Apache License Version 2.0](https://www.apache.org/licenses/LICENSE-2.0), as per the notice at:

https://developers.google.com/fonts/docs/material_symbols#licensing

List of Google material icons used:

- [Graph 3](https://fonts.google.com/icons?selected=Material+Symbols+Outlined:graph_3:FILL@0;wght@400;GRAD@0;opsz@24&icon.query=node&icon.size=24&icon.color=%231f1f1f)
