import configparser
import datetime as dt
import json
import logging
import os
import shlex
import shutil
import subprocess
import sys
import tomllib
import typing
import zipfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import httpx
import typer
from rich import (
    print,
)

logger = logging.getLogger(__name__)
LOCAL_ROOT_DIR = Path(__file__).parents[2].resolve()
SRC_NAME = "qgis_oacs"
RESOURCE_DIR_NAME = "qt-resources"
app = typer.Typer()


@dataclass
class GithubRelease:
    pre_release: bool
    tag_name: str
    url: str
    published_at: dt.datetime


@app.callback()
def main(ctx: typer.Context, verbose: bool = False, qgis_profile: str = "default"):
    """Perform various development-oriented tasks for this plugin"""
    logging.basicConfig(level=logging.INFO if verbose else logging.WARNING)
    ctx_obj = ctx.ensure_object(dict)
    ctx_obj.update({
        "qgis_profile": qgis_profile,
    })


@app.command()
def install(ctx: typer.Context):
    """Deploy plugin to QGIS' plugins dir"""
    uninstall(ctx)
    print("Building...")
    built_dir = build(ctx, clean=True)
    base_target_dir = _get_qgis_root_dir(ctx) / "python/plugins" / SRC_NAME
    print(f"Copying built plugin to {base_target_dir}...")
    shutil.copytree(built_dir, base_target_dir)
    print(f"Installed {str(built_dir)!r} into {str(base_target_dir)!r}")


@app.command()
def uninstall(context: typer.Context):
    """Remove plugin from QGIS' plugins directory"""
    print("Uninstalling...")
    base_target_dir = _get_qgis_root_dir(context) / "python/plugins" / SRC_NAME
    shutil.rmtree(str(base_target_dir), ignore_errors=True)
    print(f"Removed {str(base_target_dir)!r}")


@app.command()
def generate_zip(
    context: typer.Context, output_dir: typing.Optional[Path] = LOCAL_ROOT_DIR / "dist"
):
    build_dir = build(context)
    metadata = _get_metadata()
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / f'{SRC_NAME}.{metadata["version"]}.zip'
    with zipfile.ZipFile(zip_path, "w") as fh:
        _add_to_zip(build_dir, fh, arc_path_base=build_dir.parent)
    typer.echo(f"zip generated at {str(zip_path)!r}")
    return zip_path


@app.command()
def build(
    context: typer.Context,
    output_dir: typing.Optional[Path] = LOCAL_ROOT_DIR / "build" / SRC_NAME,
    clean: bool = True,
) -> Path:
    if clean:
        shutil.rmtree(str(output_dir), ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    copy_source_files(output_dir)
    icon_path = copy_icon(context, output_dir)
    if icon_path is None:
        logger.warning("Could not copy icon")
    compile_resources(output_dir)
    generate_metadata(context, output_dir)
    copy_license(output_dir)
    return output_dir


@app.command()
def copy_icon(
    context: typer.Context,
    output_dir: typing.Optional[Path] = LOCAL_ROOT_DIR / "build/temp",
) -> Path | None:
    metadata = _get_metadata()
    icon_path = LOCAL_ROOT_DIR / RESOURCE_DIR_NAME / metadata["icon"]
    logger.info(f"{icon_path=}")
    if icon_path.is_file():
        target_path = output_dir / icon_path.name
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(icon_path, target_path)
        result = target_path
    else:
        result = None
    return result


@app.command()
def copy_source_files(
    output_dir: typing.Optional[Path] = LOCAL_ROOT_DIR / "build/temp",
):
    output_dir.mkdir(parents=True, exist_ok=True)
    for child in (LOCAL_ROOT_DIR / "src" / SRC_NAME).iterdir():
        if child.name != "__pycache__":
            target_path = output_dir / child.name
            handler = shutil.copytree if child.is_dir() else shutil.copy
            handler(str(child.resolve()), str(target_path))


def copy_license(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    license_file_name = "LICENSE"
    license_path = LOCAL_ROOT_DIR / license_file_name
    target_path = output_dir / license_file_name
    shutil.copy(license_path, target_path)


@app.command()
def compile_resources(
    output_dir: typing.Optional[Path] = LOCAL_ROOT_DIR / "build/temp",
):
    resources_path = LOCAL_ROOT_DIR / RESOURCE_DIR_NAME / "resources.qrc"
    target_path = output_dir / "resources.py"
    target_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"compile_resources target_path: {target_path}")
    subprocess.run(shlex.split(f"pyrcc5 -o {target_path} {resources_path}"))


@app.command()
def generate_metadata(
    context: typer.Context,
    output_dir: typing.Optional[Path] = LOCAL_ROOT_DIR / "build/temp",
):
    metadata = _get_metadata()
    logger.info(f"metadata: {json.dumps(metadata, indent=2)}")
    target_path = output_dir / "metadata.txt"
    target_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"generate_metadata target_path: {target_path}")
    config = configparser.ConfigParser()
    # do not modify case of parameters, as per
    # https://docs.python.org/3/library/configparser.html#customizing-parser-behaviour
    config.optionxform = lambda option: option
    config["general"] = metadata
    with target_path.open(mode="w") as fh:
        config.write(fh)


@app.command()
def install_qgis_into_venv(
    context: typer.Context,
    pyqt5_dir: Path = os.getenv(
        "PYQT5_DIR_PATH", "/usr/lib/python3/dist-packages/PyQt5"
    ),
    # sip_dir: Path = os.getenv("SIP_DIR_PATH", "/usr/lib/python3/dist-packages"),
    qgis_dir: Path = os.getenv(
        "QGIS_PYTHON_DIR_PATH", "/usr/lib/python3/dist-packages/qgis"
    ),
    processing_plugin_dir: Path = os.getenv(
        "QGIS_PROCESSING_PLUGIN_DIR_PATH", "/usr/share/qgis/python/plugins/processing")
):
    venv_dir = _get_virtualenv_site_packages_dir()
    logger.info(f"venv_dir: {venv_dir}")
    logger.info(f"pyqt5_dir: {pyqt5_dir}")
    # print(f"sip_dir: {sip_dir}")
    logger.info(f"qgis_dir: {qgis_dir}")
    logger.info(f"processing_plugin_dir: {processing_plugin_dir}")
    suitable, relevant_paths = _check_suitable_system(
        pyqt5_dir,
        # sip_dir,
        qgis_dir,
        processing_plugin_dir
    )
    if suitable:
        target_pyqt5_dir_path = venv_dir / "PyQt5"
        print(f"Symlinking {relevant_paths['pyqt5']} to {target_pyqt5_dir_path}...")
        try:
            target_pyqt5_dir_path.symlink_to(
                relevant_paths["pyqt5"], target_is_directory=True
            )
        except FileExistsError as err:
            print(err)

        # for sip_file in relevant_paths["sip"]:
        #     target = venv_dir / sip_file.name
        #     print(f"Symlinking {sip_file} to {target}...")
        #     try:
        #         target.symlink_to(sip_file)
        #     except FileExistsError as err:
        #         print(err)
        target_qgis_dir_path = venv_dir / "qgis"
        print(f"Symlinking {relevant_paths['qgis']} to {target_qgis_dir_path}...")
        try:
            target_qgis_dir_path.symlink_to(
                relevant_paths["qgis"], target_is_directory=True
            )
        except FileExistsError as err:
            print(err)
        target_processing_plugin_dir_path = venv_dir / "processing"
        print(
            f"Symlinking {relevant_paths['processing_plugin']} to "
            f"{target_processing_plugin_dir_path}..."
        )
        try:
            target_processing_plugin_dir_path.symlink_to(
                relevant_paths["processing_plugin"], target_is_directory=True
            )
        except FileExistsError as err:
            print(err)
        final_message = "Done!"
    else:
        final_message = f"Could not find all relevant paths: {relevant_paths}"
    print(final_message)


@app.command()
def generate_plugin_repo_xml(
    context: typer.Context,
    target_dir: Path = LOCAL_ROOT_DIR / "site/repo",
):
    target_dir.mkdir(parents=True, exist_ok=True)
    metadata = _get_metadata()
    fragment_template = """
            <pyqgis_plugin name="{name}" version="{version}">
                <description><![CDATA[{description}]]></description>
                <about><![CDATA[{about}]]></about>
                <version>{version}</version>
                <qgis_minimum_version>{qgis_minimum_version}</qgis_minimum_version>
                <homepage><![CDATA[{homepage}]]></homepage>
                <file_name>{filename}</file_name>
                <icon>{icon}</icon>
                <author_name><![CDATA[{author}]]></author_name>
                <download_url>{download_url}</download_url>
                <update_date>{update_date}</update_date>
                <experimental>{experimental}</experimental>
                <deprecated>{deprecated}</deprecated>
                <tracker><![CDATA[{tracker}]]></tracker>
                <repository><![CDATA[{repository}]]></repository>
                <tags><![CDATA[{tags}]]></tags>
                <server>False</server>
            </pyqgis_plugin>
    """.strip()
    contents = "<?xml version = '1.0' encoding = 'UTF-8'?>\n<plugins>"
    repo_owner_name = metadata["repository"].partition("github.com/")[-1]
    repo_owner, repo_name = repo_owner_name.split("/")
    logger.info(f"{repo_owner=}, {repo_name=}")
    all_releases = _get_existing_releases(
        repository_name=repo_owner,
        repository_owner=repo_name,
        context=context
    )
    logger.info(f"{all_releases=}")
    if len(all_releases) > 0:
        for release in [r for r in _get_latest_releases(all_releases) if r is not None]:
            tag_name = release.tag_name
            logger.info(f"Processing release {tag_name}...")
            fragment = fragment_template.format(
                name=metadata.get("name"),
                version=tag_name.replace("v", ""),
                description=metadata.get("description"),
                about=metadata.get("about"),
                qgis_minimum_version=metadata.get("qgisMinimumVersion"),
                homepage=metadata.get("homepage"),
                filename=release.url.rpartition("/")[-1],
                icon=metadata.get("icon", ""),
                author=metadata.get("author"),
                download_url=release.url,
                update_date=release.published_at,
                experimental=release.pre_release,
                deprecated=metadata.get("deprecated"),
                tracker=metadata.get("tracker"),
                repository=metadata.get("repository"),
                tags=metadata.get("tags"),
            )
            contents = "\n".join((contents, fragment))
        contents = "\n".join((contents, "</plugins>"))
        repo_index = target_dir / "plugins.xml"
        repo_index.write_text(contents, encoding="utf-8")
        print(f"Plugin repo XML file saved at {repo_index}")
    else:
        print(f"No releases found for {repo_owner}/{repo_name} - plugin repo XML not written")


def _check_suitable_system(
        pyqt5_dir: Path,
        # sip_dir: Path,
        qgis_dir: Path,
        processing_plugin_dir: Path,
) -> typing.Tuple[bool, typing.Dict]:
    pyqt5_found = pyqt5_dir.is_dir()
    # try:
    #     sip_files = _find_sip_files(sip_dir)
    # except IndexError:
    #     sip_files = []
    # sip_found = len(sip_files) > 0
    qgis_found = qgis_dir.is_dir()
    processing_plugin_found = processing_plugin_dir.is_dir()
    suitable = all(
        (
            pyqt5_found,
            # sip_found,
            qgis_found,
            processing_plugin_found,
        )
    )
    return (
        suitable,
        {
            "pyqt5": pyqt5_dir,
            # "sip": sip_files,
            "qgis": qgis_dir,
            "processing_plugin": processing_plugin_dir,
        },
    )


# def _find_sip_files(sip_dir) -> typing.List[Path]:
#     sip_so_file = list(sip_dir.glob("sip.*.so"))[0]
#     sipconfig_files = list(sip_dir.glob("sipconfig*.py"))
#     return sipconfig_files + [sip_so_file]
#
#
def _get_virtualenv_site_packages_dir() -> Path:
    venv_lib_root = Path(sys.executable).parents[1] / "lib"
    for item in [i for i in venv_lib_root.iterdir() if i.is_dir()]:
        if item.name.startswith("python"):
            python_lib_path = item
            break
    else:
        raise RuntimeError("Could not find site_packages_dir")
    site_packages_dir = python_lib_path / "site-packages"
    if site_packages_dir.is_dir():
        result = site_packages_dir
    else:
        raise RuntimeError(f"{site_packages_dir} does not exist")
    return result


@lru_cache()
def _get_metadata() -> typing.Dict:
    pyproject_path = LOCAL_ROOT_DIR / "pyproject.toml"
    with pyproject_path.open("rb") as fh:
        conf = tomllib.load(fh)
    try:
        maintainer = conf["project"].get("maintainers", conf["project"]["authors"])[0]
        author_name = maintainer["name"]
        author_email = maintainer["email"]
    except (KeyError, IndexError):
        raise RuntimeError("Author list not found or invalid - check your pyproject.toml file")
    metadata = conf["tool"]["qgis-plugin"]["metadata"].copy()
    metadata.update(
        {
            "author": author_name,
            "email": author_email,
            "description": conf["project"]["description"],
            "version": conf["project"]["version"],
            "tags": ", ".join(metadata.get("tags", [])),
            "changelog": _parse_changelog(),
        }
    )
    return metadata


def _parse_changelog() -> str:
    if not (changelog_path := Path(LOCAL_ROOT_DIR) / "CHANGELOG.md").exists():
        raise RuntimeError(f"Changelog file not found at {changelog_path}")

    contents = changelog_path.read_text()
    usable_fragment = contents.rpartition(f"## [Unreleased]")[-1].partition(
        "[unreleased]"
    )[0]
    release_parts = usable_fragment.split("\n## ")
    result = []
    current_change_type = "unreleased"
    for release_fragment in release_parts:
        lines: typing.List[str] = [li for li in release_fragment.splitlines()]
        for line in lines:
            if line.startswith("["):
                release, release_date = line.partition(" - ")[::2]
                release = release.strip("[]")
                result.append(f"\n{release} ({release_date})")
            elif line.startswith("### "):
                current_change_type = line.strip("### ").strip().lower()
            elif line.startswith("-"):
                message = line.strip("- ")
                result.append(f"- ({current_change_type}) {message}")
            else:
                pass
    return "\n".join(result)


def _add_to_zip(directory: Path, zip_handler: zipfile.ZipFile, arc_path_base: Path):
    for item in directory.iterdir():
        if item.is_file():
            zip_handler.write(item, arcname=str(item.relative_to(arc_path_base)))
        else:
            _add_to_zip(item, zip_handler, arc_path_base)


def _get_qgis_root_dir(context: typing.Optional[typer.Context] = None) -> Path:
    return (
        Path.home() / f".local/share/QGIS/QGIS3/profiles/{context.obj['qgis_profile']}"
    )


def _get_existing_releases(
    repository_name: str,
    repository_owner: str,
    context: typing.Optional = None,
) -> typing.List[GithubRelease]:
    """Query the github API and retrieve existing releases"""
    # TODO: add support for pagination
    base_url = f"https://api.github.com/repos/{repository_owner}/{repository_name}/releases"
    response = httpx.get(base_url)
    result = []
    if response.status_code == 200:
        payload = response.json()
        for release in payload:
            for asset in release["assets"]:
                if asset.get("content_type") == "application/zip":
                    zip_download_url = asset.get("browser_download_url")
                    break
            else:
                zip_download_url = None
            logger.info(f"zip_download_url: {zip_download_url}")
            if zip_download_url is not None:
                result.append(
                    GithubRelease(
                        pre_release=release.get("prerelease", True),
                        tag_name=release.get("tag_name"),
                        url=zip_download_url,
                        published_at=dt.datetime.strptime(
                            release["published_at"], "%Y-%m-%dT%H:%M:%SZ"
                        ),
                    )
                )
    return result


def _get_latest_releases(
    current_releases: typing.List[GithubRelease],
) -> typing.Tuple[typing.Optional[GithubRelease], typing.Optional[GithubRelease]]:
    latest_experimental = None
    latest_stable = None
    for release in current_releases:
        if release.pre_release:
            if latest_experimental is not None:
                if release.published_at > latest_experimental.published_at:
                    latest_experimental = release
            else:
                latest_experimental = release
        else:
            if latest_stable is not None:
                if release.published_at > latest_stable.published_at:
                    latest_stable = release
            else:
                latest_stable = release
    return latest_stable, latest_experimental


if __name__ == "__main__":
    app()
