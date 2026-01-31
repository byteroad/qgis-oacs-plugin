import dataclasses


@dataclasses.dataclass(frozen=True)
class IconPath:
    search = ":/plugins/qgis_oacs/search.svg"
    system = ":/plugins/qgis_oacs/manufacturing.svg"
    sampling_feature = ":/plugins/qgis_oacs/lab_panel.svg"
    system_type_sensor = ":/plugins/qgis_oacs/sensors_krx.svg"
    system_type_actuator = ":/plugins/qgis_oacs/stadia_controller.svg"
    system_type_platform = ":/plugins/qgis_oacs/tools_ladder.svg"
    system_type_sampler = ":/plugins/qgis_oacs/labs.svg"
    system_type_system = ":/plugins/qgis_oacs/manufacturing.svg"
    system_asset_type_equipment = ":/plugins/qgis_oacs/manufacturing.svg"
    system_asset_type_human = ":/plugins/qgis_oacs/manufacturing.svg"
    system_asset_type_living_thing = ":/plugins/qgis_oacs/manufacturing.svg"
    system_asset_type_simulation = ":/plugins/qgis_oacs/manufacturing.svg"
    system_asset_type_process = ":/plugins/qgis_oacs/manufacturing.svg"
    system_asset_type_group = ":/plugins/qgis_oacs/manufacturing.svg"
    system_asset_type_other = ":/plugins/qgis_oacs/manufacturing.svg"


# we look for both `rel=<name>` and `rel=ogc-rel:<name>` because of:
#
# https://github.com/opengeospatial/ogcapi-connected-systems/issues/173
#
@dataclasses.dataclass(frozen=True)
class LinkRelation:
    control_streams = "controlstreams"
    data_streams = "datastreams"
    deployments = "deployments"
    parent_system = "parentSystem"
    procedures = "procedures"
    sampled_feature = "sampledFeature"
    sample_of = "sampleOf"
    sampling_features = "samplingFeatures"
    sub_systems = "subsystems"


@dataclasses.dataclass(frozen=True)
class OgcLinkRelation:
    control_streams = "ogc-rel:controlstreams"
    data_streams = "ogc-rel:datastreams"
    deployments = "ogc-rel:deployments"
    parent_system = "ogc-rel:parentSystem"
    procedures = "ogc-rel:procedures"
    sampled_feature = "ogc-rel:sampledFeature"
    sample_of = "ogc-rel:sampleOf"
    sampling_features = "ogc-rel:samplingFeatures"
    sub_systems = "ogc-rel:subsystems"

