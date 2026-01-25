# Development

## Quickstart

!!! WARNING
    
    This plugin is being developed on an ubuntu 24.04 machine. These instructions are not guaranteed to work
    on a different system. Moreover, they will very likely fail on a Windows system.

1. Install [QGIS](https://qgis.org/). Be sure to get at the minimum version 3.44;

1. Create a custom QGIS profile for development - This is not strictly necessary but helps with keeping your main
   QGIS workspace clean. Use the QGIS GUI for this (Settings -> User Profiles -> New Profile...). For the sake of
   these instructions, let's pretend you named your profile `my-profile`.

1.  Install the pyqt5 dev tools, in order to gain access to the `pyrcc5` utility:

    ```shell
    sudo apt install pyqt5-dev-tools
    ```

1. Install [uv](https://docs.astral.sh/uv/);

1. **Fork** and clone this repo (assuming your github name is `myself`):

    ```shell
    git clone https://github.com/myself/qgis-oacs-plugin.git
    ```

1. Use the provided `plugin-admin` CLI utility to create a virtualenv and get the QGIS Python bindings in it:

    ```shell
    uv plugin-admin --qgis-profile my-profile install-qgis-into-venv
    ```

1. Now you can work on the plugin code

1. Test things out locally by installing the plugin with:

    ```shell
    uv plugin-admin --qgis-profile my-profile install
    ```

1. When ready, submit a PR for your code to be reviewed and merged


## plugin-admin CLI tool

This plugin comes with a `plugin-admin` CLI command which provides commands useful for development.
It is used to perform all operations related to the plugin:

- Install the plugin to your local QGIS user profile
- Ensure your virtual env has access to the QGIS Python bindings
- Build a zip of the plugin
- etc.

It must be invoked like this:

```shell
# get an overview of existing commands
uv run plugin-admin --help
```


## Installing the plugin into your local QGIS python plugins directory

When developing, in order to try out the plugin locally you need to
call `uv run plugin-admin install` command. This command will copy all files into your
local QGIS python plugins directory. Upon making changes to the code you
will need to call this installation command again (and potentially also restart QGIS).

!!! TIP
    Perhaps a more robust set of instructions would be to:
    - Create a custom QGIS user profile for development (here named `oacs-dev`)
    - Create a sample QGIS project to aid in development (here named `oacs-plugin-sample-project.qgz`)
    execute the following:
    
    ```shell
    uv run plugin-admin --qgis-profile oacs-dev install \
        && qgis \
            --profiles-path ${HOME}/.local/share/QGIS/QGIS3 \
            --profile oacs-dev \
            --project oacs-plugin-sample-project.qgz
    ```


## Releasing new versions

This plugin uses an automated release process that is based upon
[github actions](https://docs.github.com/en/actions/quickstart).
New versions shall be released under the [semantic versioning](https://semver.org/)
contract.

In order to have a new version of the plugin released:

-  Be sure to have updated the `CHANGELOG.md`

-  Be sure to have updated the version on the `pyproject.toml` file. 

-  Create a new git annotated tag and push it to the repository. **The tag name must
   follow the `v{major}.{minor}.{patch}` convention**, for example:

    ```shell
    git tag -a -m 'version 0.3.2' v0.3.2
    git push origin v0.3.2
    ```

-  Github actions will take it from there. The new release shall appear in the custom
   QGIS plugin repo shortly
