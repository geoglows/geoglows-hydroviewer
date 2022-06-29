from tethys_sdk.app_settings import CustomSetting
from tethys_sdk.base import TethysAppBase, url_map_maker
from tethys_apps.base.workspace import _get_app_workspace


class GeoglowsHydroviewer(TethysAppBase):
    """
    Tethys app class for the GEOGloWS ECMWF Streamflow Hydroviewer
    """
    name = 'GEOGloWS Hydroviewer'
    package = 'geoglows_hydroviewer'
    root_url = 'geoglows-hydroviewer'
    index = 'home'
    icon = 'geoglows_hydroviewer/images/water.jpeg'
    color = '#2980b9'
    description = 'A tool for viewing the GEOGloWS ECMWF Hydrologic Model and creating subset shapefiles.',
    tags = 'geoglows, streamflow, discharge, time series, hydrograph, geoprocessing, esri'
    enable_feedback = False
    feedback_emails = []
    
    controller_modules = [
        'controllers_creator_export', 'controllers_creator_geoprocess', 'controllers_creator',
        'hydroviewer_creator_tools', 'manage_gauge_networks', 'manage_uploaded_observations'
    ]

    def custom_settings(self):
        return (
            CustomSetting(
                name='global_delineation_shapefiles_directory',
                type=CustomSetting.TYPE_STRING,
                description="Absolute file path to a directory containing geoglows shapefiles (see app documentation)",
                required=False,
                default=_get_app_workspace(GeoglowsHydroviewer)
            ),
        )
