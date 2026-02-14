import dataclasses


@dataclasses.dataclass(frozen=True)
class IconPath:
    search = ":/plugins/qgis_oacs/search.svg"
    system = ":/plugins/qgis_oacs/manufacturing.svg"
    sampling_feature = ":/plugins/qgis_oacs/lab_panel.svg"
    datastream = ":/plugins/qgis_oacs/stream.svg"
    datastream_type_status = ":/plugins/qgis_oacs/circle.svg"
    datastream_type_observation = ":/plugins/qgis_oacs/eye_tracking.svg"
    deployment = ":/plugins/qgis_oacs/deployed_code.svg"
    feature_has_geospatial_location = ":/plugins/qgis_oacs/location_on.svg"
    feature_does_not_have_geospatial_location = ":/plugins/qgis_oacs/table.svg"
    procedure_type_procedure = ":/plugins/qgis_oacs/procedure.svg"
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
    deployed_systems = "deployedSystems"
    features_of_interest = "featuresOfInterest"
    procedures = "procedures"
    parent_system = "parentSystem"
    platform = "platform"
    sampled_feature = "sampledFeature"
    sample_of = "sampleOf"
    sampling_features = "samplingFeatures"
    sub_deployments = "subDeployments"
    sub_systems = "subsystems"


@dataclasses.dataclass(frozen=True)
class OgcLinkRelation:
    control_streams = "ogc-rel:controlstreams"
    data_streams = "ogc-rel:datastreams"
    deployments = "ogc-rel:deployments"
    deployed_systems = "deployedSystems"
    features_of_interest = "featuresOfInterest"
    procedures = "ogc-rel:procedures"
    parent_system = "ogc-rel:parentSystem"
    platform = "ogc-rel:platform"
    sampled_feature = "ogc-rel:sampledFeature"
    sample_of = "ogc-rel:sampleOf"
    sampling_features = "ogc-rel:samplingFeatures"
    sub_deployments = "ogc-rel:subDeployments"
    sub_systems = "ogc-rel:subsystems"

