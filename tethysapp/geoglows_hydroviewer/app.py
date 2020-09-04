import os

from tethys_sdk.app_settings import CustomSetting
from tethys_sdk.base import TethysAppBase, url_map_maker


class HydroviewerTemplate(TethysAppBase):
    """
    Tethys app class for GEOGloWS Hydroviewer Template.
    """

    name = 'GEOGloWS ECMWF Streamflow Hydroviewer'
    index = 'geoglows_hydroviewer:home'
    icon = 'geoglows_hydroviewer/images/water.jpeg'
    package = 'geoglows_hydroviewer'
    root_url = 'geoglows-hydroviewer'
    color = '#2980b9'
    description = 'A tool for viewing the GEOGloWS ECMWF Streamflow Model and creating subset shapefiles.',
    tags = 'geoglows, streamflow, animations, timeseries, hydrograph, geoprocessing, esri'
    enable_feedback = False
    feedback_emails = []

    def url_maps(self):
        UrlMap = url_map_maker(self.root_url)

        return (
            # the geoglows hydroviewer page (home page)
            UrlMap(name='home',
                   url=f'{self.root_url}',
                   controller=f'{self.package}.controllers.home'),

            # handles the requests to get the various plots in the app modals
            UrlMap(name='get_streamflow',
                   url=f'{self.root_url}/getStreamflow',
                   controller=f'{self.package}.controllers.get_streamflow'),
            UrlMap(name='upload_new_observations',
                   url=f'{self.root_url}/upload_new_observations',
                   controller=f'{self.package}.manage_uploaded_observations.upload_new_observations'),
            UrlMap(name='correct_bias',
                   url=f'{self.root_url}/correctBias',
                   controller=f'{self.package}.controllers.correct_bias'),

            # some other utilities
            UrlMap(name='find_reach_id',
                   url=f'{self.root_url}/findReachID',
                   controller=f'{self.package}.controllers.find_reach_id'),

            # Gauge Networks
            UrlMap(name='get_gauge_geojson',
                   url=f'{self.root_url}/getGaugeGeoJSON',
                   controller=f'{self.package}.controllers.get_gauge_geojson'),

            # geoglows hydroviewer creator main page
            UrlMap(name='geoglows_hydroviewer_creator',
                   url=f'{self.root_url}/creator',
                   controller=f'{self.package}.controllers_creator.home'),
            # creator pages and urls for forms
            UrlMap(name='add_new_project',
                   url=f'{self.root_url}/creator/add-new-project',
                   controller=f'{self.package}.controllers_creator.add_new_project'),
            UrlMap(name='delete_existing_project',
                   url=f'{self.root_url}/creator/delete_existing_project',
                   controller=f'{self.package}.controllers_creator.delete_existing_project'),

            UrlMap(name='geoprocess_idregion',
                   url=f'{self.root_url}/creator/geoprocessing/geoprocess_idregion',
                   controller=f'{self.package}.controllers_creator.geoprocess_hydroviewer_idregion'),
            UrlMap(name='geoprocess_clip',
                   url=f'{self.root_url}/creator/geoprocessing/geoprocess_clip',
                   controller=f'{self.package}.controllers_creator.geoprocess_hydroviewer_clip'),

            UrlMap(name='project_overview',
                   url=f'{self.root_url}/creator/project_overview',
                   controller=f'{self.package}.controllers_creator.project_overview'),

            UrlMap(name='draw_boundaries',
                   url=f'{self.root_url}/creator/edit-hydroviewer/draw_boundaries',
                   controller=f'{self.package}.controllers_creator.draw_hydroviewer_boundaries'),
            UrlMap(name='choose_boundaries',
                   url=f'{self.root_url}/creator/edit-hydroviewer/choose_boundaries',
                   controller=f'{self.package}.controllers_creator.choose_hydroviewer_boundaries'),
            UrlMap(name='upload_boundaries',
                   url=f'{self.root_url}/creator/edit-hydroviewer/upload_boundaries',
                   controller=f'{self.package}.controllers_creator.upload_boundary_shapefile'),
            UrlMap(name='save_boundaries',
                   url=f'{self.root_url}/creator/edit-hydroviewer/save_boundaries',
                   controller=f'{self.package}.controllers_creator.save_drawn_boundaries'),
            UrlMap(name='retrieve_boundaries',
                   url=f'{self.root_url}/creator/edit-hydroviewer/retrieve_boundaries',
                   controller=f'{self.package}.controllers_creator.retrieve_hydroviewer_boundaries'),

            UrlMap(name='shapefile_export_zipfile',
                   url=f'{self.root_url}/creator/project_overview/shapefile_export_zipfile',
                   controller=f'{self.package}.controllers_creator.shapefile_export_zipfile'),
            UrlMap(name='shapefile_export_geoserver',
                   url=f'{self.root_url}/creator/edit-hydroviewer/shapefile_export_geoserver',
                   controller=f'{self.package}.controllers_creator.shapefile_export_geoserver'),
            UrlMap(name='project_export_html',
                   url=f'{self.root_url}/creator/project_export_html',
                   controller=f'{self.package}.controllers_creator.project_export_html'),
        )

    def custom_settings(self):
        return (
            CustomSetting(
                name='global_delineation_shapefiles_directory',
                type=CustomSetting.TYPE_STRING,
                description="Absolute file path to a directory containing shapefiles (see app documentation)",
                required=False,
                default=f"{os.path.join(self.get_app_workspace().path, 'shapefiles')}",
            ),
        )
