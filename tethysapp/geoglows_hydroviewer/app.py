from tethys_sdk.app_settings import CustomSetting
from tethys_sdk.base import TethysAppBase, url_map_maker


class GeoglowsHydroviewer(TethysAppBase):
    """
    Tethys app class for the GEOGloWS ECMWF Streamflow Hydroviewer
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
            UrlMap(name='hydroshare_view',
                   url=f'{self.root_url}/hydroshare',
                   controller=f'{self.package}.controllers.hydroshare_view'),

            # handles the requests to get the various plots in the app modals
            UrlMap(name='get_streamflow',
                   url=f'{self.root_url}/hydroviewer/getStreamflow',
                   controller=f'{self.package}.controllers.get_streamflow'),
            UrlMap(name='upload_new_observations',
                   url=f'{self.root_url}/hydroviewer/upload_new_observations',
                   controller=f'{self.package}.manage_uploaded_observations.upload_new_observations'),
            UrlMap(name='correct_bias',
                   url=f'{self.root_url}/hydroviewer/correctBias',
                   controller=f'{self.package}.controllers.correct_bias'),

            # some other utilities
            UrlMap(name='find_reach_id',
                   url=f'{self.root_url}/findReachID',
                   controller=f'{self.package}.controllers.find_reach_id'),

            # Gauge Networks
            UrlMap(name='get_gauge_geojson',
                   url=f'{self.root_url}/getGaugeGeoJSON',
                   controller=f'{self.package}.controllers.get_gauge_geojson'),

            # geoglows hydroviewer creator main pages
            UrlMap(name='geoglows_hydroviewer_creator',
                   url=f'{self.root_url}/creator',
                   controller=f'{self.package}.controllers_creator.home'),
            UrlMap(name='project_overview',
                   url=f'{self.root_url}/creator/project',
                   controller=f'{self.package}.controllers_creator.project_overview'),
            UrlMap(name='render_hydroviewer',
                   url=f'{self.root_url}/creator/render',
                   controller=f'{self.package}.controllers_creator.render_hydroviewer'),

            # creator pages and urls for adding/deleting projects
            UrlMap(name='add_new_project',
                   url=f'{self.root_url}/creator/add-new-project',
                   controller=f'{self.package}.controllers_creator.add_new_project'),
            UrlMap(name='delete_existing_project',
                   url=f'{self.root_url}/creator/delete_existing_project',
                   controller=f'{self.package}.controllers_creator.delete_existing_project'),

            # geoprocessing shapefiles urls
            UrlMap(name='geoprocess_idregion',
                   url=f'{self.root_url}/creator/project/geoprocessing/geoprocess_idregion',
                   controller=f'{self.package}.controllers_creator.geoprocess_hydroviewer_idregion'),
            UrlMap(name='geoprocess_clip',
                   url=f'{self.root_url}/creator/project/geoprocessing/geoprocess_clip',
                   controller=f'{self.package}.controllers_creator.geoprocess_hydroviewer_clip'),

            # project editing urls and pages
            UrlMap(name='draw_boundaries',
                   url=f'{self.root_url}/creator/project/edit/draw_boundaries',
                   controller=f'{self.package}.controllers_creator.draw_hydroviewer_boundaries'),
            UrlMap(name='choose_boundaries',
                   url=f'{self.root_url}/creator/project/edit/choose_boundaries',
                   controller=f'{self.package}.controllers_creator.choose_hydroviewer_boundaries'),
            UrlMap(name='upload_boundaries',
                   url=f'{self.root_url}/creator/project/edit/upload_boundaries',
                   controller=f'{self.package}.controllers_creator.upload_boundary'),
            UrlMap(name='save_boundaries',
                   url=f'{self.root_url}/creator/project/edit/save_boundaries',
                   controller=f'{self.package}.controllers_creator.save_boundaries'),
            UrlMap(name='retrieve_boundaries',
                   url=f'{self.root_url}/creator/project/edit/retrieve_boundaries',
                   controller=f'{self.package}.controllers_creator.retrieve_hydroviewer_boundaries'),

            # project and shapefile exporting options
            UrlMap(name='export_zipfile',
                   url=f'{self.root_url}/creator/project/export/zipfile',
                   controller=f'{self.package}.controllers_creator_export.export_zipfile'),
            UrlMap(name='export_geoserver',
                   url=f'{self.root_url}/creator/project/export/geoserver',
                   controller=f'{self.package}.controllers_creator_export.export_geoserver'),
            UrlMap(name='export_hydroshare',
                   url=f'{self.root_url}/creator/project/export/hydroshare',
                   controller=f'{self.package}.controllers_creator_export.export_hydroshare'),
            UrlMap(name='export_html',
                   url=f'{self.root_url}/creator/project/export/html',
                   controller=f'{self.package}.controllers_creator_export.export_html'),
        )

    def custom_settings(self):
        return (
            CustomSetting(
                name='global_delineation_shapefiles_directory',
                type=CustomSetting.TYPE_STRING,
                description="Absolute file path to a directory containing geoglows shapefiles (see app documentation)",
                required=False,
                default=self.get_app_workspace().path,
            ),
        )
