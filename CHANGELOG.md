# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]


## [0.2.0] - 2026-05-18

### Added
- Added missing icon for procedures
- Added user guide to docs
- Added action for opening data source selector from the plugin menu
- Support http://www.w3.org/ns/ssn/System as a valid type identifier for Systems

### Fixed
- Broken rendering of Deployment properties
- Don't fail parsing the full list of resources if the feature type of one of them
  is invalid


## Changed
- Resources with a spatial representation have their icon colorized in order to be easily
  distinguishable


### Removed
- Context menu for panel resources that allowed loading the resource to QGIS - there is
  already a button for this


## [0.1.0] - 2026-05-15

### Added
- Add support for Procedure items
- Add resource description to renderable properties
- Add panel for browsing a resource's relationships after loading
- Add panel for simple visualization of observations

### Fixed
- Fix 'q' search parameter being sent when empty
- Add support to GeoJSON geometries with more than two coordinates per point
- Scroll bar resizes correctly when number of list items changes


## [0.0.4] - 2026-02-09

### Fixed
-  CI workflow to publish to private QGIS repo


## [0.0.3] - 2026-02-09

### Added
-  CI workflow to publish to private QGIS repo


## [0.0.2] - 2026-02-09

### Fixed
-  Fixed wrong version in pyproject.toml


## [0.0.1] - 2026-02-09

### Added
-  Initial release for early feedback



[unreleased]: https://github.com/byteroad/qgis-oacs-plugin
[0.2.0]: https://github.com/byteroad/qgis-oacs-plugin/compare/v0.2.0...main
[0.1.0]: https://github.com/byteroad/qgis-oacs-plugin/compare/v0.1.0...main
[0.0.4]: https://github.com/byteroad/qgis-oacs-plugin/compare/v0.0.4...main
[0.0.3]: https://github.com/byteroad/qgis-oacs-plugin/compare/v0.0.3...main
[0.0.2]: https://github.com/byteroad/qgis-oacs-plugin/compare/v0.0.2...main
[0.0.1]: https://github.com/byteroad/qgis-oacs-plugin/compare/v0.0.1...main
