from tethys_sdk.base import TethysAppBase, url_map_maker


class HydroviewerTemplate(TethysAppBase):
    """
    Tethys app class for GEOGloWS Hydroviewer Template.
    """

    name = 'GEOGloWS ECMWF Streamflow Hydroviewer'
    index = 'hydroviewer_template:home'
    icon = 'hydroviewer_template/images/water.jpg'
    package = 'hydroviewer_template'
    root_url = 'hydroviewer-template'
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
                name='getStreamflow',
                url=f'{self.root_url}/getStreamflow',
                controller=f'{self.package}.controllers.get_streamflow'
            ),
            # todo
            # UrlMap(
            #     name='upload_new_observations',
            #     url=f'{self.root_url}/upload_new_observations',
            #     controller=f'{self.package}.manage_uploaded_observations.upload_new_observations'
            # ),
            UrlMap(
                name='correctBias',
                url=f'{self.root_url}/correctBias',
                controller=f'{self.package}.controllers.correct_bias'
            ),

            # some other utilities
            UrlMap(
                name='findReachID',
                url=f'{self.root_url}/findReachID',
                controller=f'{self.package}.controllers.find_reach_id'
            ),

            # Gauge Networks
            UrlMap(
                name='getGaugeGeoJSON',
                url=f'{self.root_url}/getGaugeGeoJSON',
                controller=f'{self.package}.controllers.get_gauge_geojson'
            )
        )
