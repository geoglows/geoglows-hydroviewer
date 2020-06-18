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
    description = ''
    tags = ''
    enable_feedback = False
    feedback_emails = []

    def url_maps(self):
        """
        Add controllers
        """
        UrlMap = url_map_maker(self.root_url)

        return (
            # the home page
            UrlMap(
                name='home',
                url=f'{self.root_url}',
                controller=f'{self.package}.controllers.home'
            ),

            # handles the requests to get the various plots in the app modals
            UrlMap(
                name='get_streamflow',
                url=f'{self.root_url}/getStreamflow',
                controller=f'{self.package}.controllers.get_streamflow'
            ),
            UrlMap(
                name='upload_new_observations',
                url=f'{self.root_url}/upload_new_observations',
                controller=f'{self.package}.manage_uploaded_observations.upload_new_observations'
            ),
            UrlMap(
                name='correct_bias',
                url=f'{self.root_url}/correctBias',
                controller=f'{self.package}.controllers.correct_bias'
            ),

            # some other utilities
            UrlMap(
                name='find_reach_id',
                url=f'{self.root_url}/findReachID',
                controller=f'{self.package}.controllers.find_reach_id'
            ),

            # Gauge Networks
            UrlMap(
                name='get_gauge_geojson',
                url=f'{self.root_url}/getGaugeGeoJSON',
                controller=f'{self.package}.controllers.get_gauge_geojson'
            )
        )
