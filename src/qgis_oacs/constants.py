import dataclasses

from qgis.PyQt import QtGui

SPATIAL_COLOR = QtGui.QColor("#2a9d8f")


# ---------------------------------------------------------------------------
# CSAPI layer custom property keys
# ---------------------------------------------------------------------------

OACS_SCHEMA_VERSION_KEY = "oacs/schema_version"
OACS_SCHEMA_VERSION = 1
OACS_CONNECTION_ID_KEY = "oacs/connection_id"
OACS_CONNECTION_BASE_URL_KEY = "oacs/connection_base_url"
OACS_RESOURCE_TYPE_KEY = "oacs/resource_type"
OACS_SELF_LINK_KEY = "oacs/self_link"
OACS_LINKS_JSON_KEY = "oacs/links_json"


@dataclasses.dataclass(frozen=True)
class IconPath:
    datastream = ":/plugins/qgis_oacs/stream.svg"
    datastream_type_status = ":/plugins/qgis_oacs/circle.svg"
    datastream_type_observation = ":/plugins/qgis_oacs/eye_tracking.svg"
    deployment = ":/plugins/qgis_oacs/deployed_code.svg"
    feature_does_not_have_geospatial_location = ":/plugins/qgis_oacs/table.svg"
    feature_has_geospatial_location = ":/plugins/qgis_oacs/location_on.svg"
    main_logo = ":/plugins/qgis_oacs/graph_3.svg"
    procedure_type_procedure = ":/plugins/qgis_oacs/article.svg"
    sampling_feature = ":/plugins/qgis_oacs/lab_panel.svg"
    search = ":/plugins/qgis_oacs/search.svg"
    system = ":/plugins/qgis_oacs/manufacturing.svg"
    system_asset_type_equipment = ":/plugins/qgis_oacs/manufacturing.svg"
    system_asset_type_group = ":/plugins/qgis_oacs/manufacturing.svg"
    system_asset_type_human = ":/plugins/qgis_oacs/manufacturing.svg"
    system_asset_type_living_thing = ":/plugins/qgis_oacs/manufacturing.svg"
    system_asset_type_other = ":/plugins/qgis_oacs/manufacturing.svg"
    system_asset_type_process = ":/plugins/qgis_oacs/manufacturing.svg"
    system_asset_type_simulation = ":/plugins/qgis_oacs/manufacturing.svg"
    system_type_actuator = ":/plugins/qgis_oacs/stadia_controller.svg"
    system_type_platform = ":/plugins/qgis_oacs/tools_ladder.svg"
    system_type_sampler = ":/plugins/qgis_oacs/labs.svg"
    system_type_sensor = ":/plugins/qgis_oacs/sensors_krx.svg"
    system_type_system = ":/plugins/qgis_oacs/manufacturing.svg"


# we look for both `rel=<name>` and `rel=ogc-rel:<name>` because of:
#
# https://github.com/opengeospatial/ogcapi-connected-systems/issues/173
#
@dataclasses.dataclass(frozen=True)
class LinkRelation:
    # singular resource links (used in @link inline properties)
    deployment = "deployment"
    feature_of_interest = "featureOfInterest"
    procedure = "procedure"
    sampling_feature = "samplingFeature"
    system = "system"
    # collection / association links (used in the links[] array)
    control_streams = "controlStreams"
    data_streams = "datastreams"
    deployed_systems = "deployedSystems"
    deployments = "deployments"
    features_of_interest = "featuresOfInterest"
    implementing_systems = "implementingSystems"
    observations = "observations"
    parent_deployment = "parentDeployment"
    parent_system = "parentSystem"
    platform = "platform"
    procedures = "procedures"
    sampled_feature = "sampledFeature"
    sample_of = "sampleOf"
    sampling_features = "samplingFeatures"
    sub_deployments = "subdeployments"
    sub_systems = "subsystems"


@dataclasses.dataclass(frozen=True)
class OgcLinkRelation:
    # singular resource links (used in @link inline properties)
    deployment = "ogc-rel:deployment"
    feature_of_interest = "ogc-rel:featureOfInterest"
    procedure = "ogc-rel:procedure"
    sampling_feature = "ogc-rel:samplingFeature"
    system = "ogc-rel:system"
    # collection / association links (used in the links[] array)
    control_streams = "ogc-rel:controlStreams"
    data_streams = "ogc-rel:datastreams"
    deployed_systems = "ogc-rel:deployedSystems"
    deployments = "ogc-rel:deployments"
    features_of_interest = "ogc-rel:featuresOfInterest"
    implementing_systems = "ogc-rel:implementingSystems"
    observations = "ogc-rel:observations"
    parent_deployment = "ogc-rel:parentDeployment"
    parent_system = "ogc-rel:parentSystem"
    platform = "ogc-rel:platform"
    procedures = "ogc-rel:procedures"
    sampled_feature = "ogc-rel:sampledFeature"
    sample_of = "ogc-rel:sampleOf"
    sampling_features = "ogc-rel:samplingFeatures"
    sub_deployments = "ogc-rel:subdeployments"
    sub_systems = "ogc-rel:subsystems"


# ---------------------------------------------------------------------------
# Link relation → icon path mapping (used by tree widgets and the panel)
# ---------------------------------------------------------------------------

def _build_link_rel_to_icon() -> dict[str, str]:
    lr = LinkRelation
    ogc = OgcLinkRelation
    ip = IconPath
    return {
        lr.system: ip.system_type_system,
        ogc.system: ip.system_type_system,
        lr.procedure: ip.procedure_type_procedure,
        ogc.procedure: ip.procedure_type_procedure,
        lr.deployment: ip.deployment,
        ogc.deployment: ip.deployment,
        lr.sampling_feature: ip.sampling_feature,
        ogc.sampling_feature: ip.sampling_feature,
        lr.implementing_systems: ip.system_type_system,
        ogc.implementing_systems: ip.system_type_system,
        lr.data_streams: ip.datastream,
        ogc.data_streams: ip.datastream,
        lr.control_streams: ip.datastream,
        ogc.control_streams: ip.datastream,
        lr.observations: ip.datastream_type_observation,
        ogc.observations: ip.datastream_type_observation,
        lr.sampling_features: ip.sampling_feature,
        ogc.sampling_features: ip.sampling_feature,
        lr.deployments: ip.deployment,
        ogc.deployments: ip.deployment,
        lr.sub_deployments: ip.deployment,
        ogc.sub_deployments: ip.deployment,
        lr.parent_deployment: ip.deployment,
        ogc.parent_deployment: ip.deployment,
        lr.deployed_systems: ip.system_type_system,
        ogc.deployed_systems: ip.system_type_system,
        lr.procedures: ip.procedure_type_procedure,
        ogc.procedures: ip.procedure_type_procedure,
        lr.sub_systems: ip.system_type_system,
        ogc.sub_systems: ip.system_type_system,
        lr.parent_system: ip.system_type_system,
        ogc.parent_system: ip.system_type_system,
        lr.sampled_feature: ip.sampling_feature,
        ogc.sampled_feature: ip.sampling_feature,
        lr.sample_of: ip.sampling_feature,
        ogc.sample_of: ip.sampling_feature,
        lr.platform: ip.system_type_platform,
        ogc.platform: ip.system_type_platform,
    }


LINK_REL_TO_ICON: dict[str, str] = _build_link_rel_to_icon()

