from tethys_sdk.base import TethysAppBase, url_map_maker


class HydroviewerTemplate(TethysAppBase):
    """
    Tethys app class for GEOGloWS Hydroviewer Template.
    """

    name = 'GEOGloWS Hydroviewer'
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
                name='get_streamflow',
                url=f'{self.root_url}/get_streamflow',
                controller=f'{self.package}.controllers.get_streamflow'
            ),
            UrlMap(
                name='upload_new_observations',
                url=f'{self.root_url}/upload_new_observations',
                controller=f'{self.package}.manage_uploaded_observations.upload_new_observations'
            ),
            UrlMap(
                name='correct_bias',
                url=f'{self.root_url}/correct_bias',
                controller=f'{self.package}.controllers.correct_bias'
            ),

            # some other utilities
            UrlMap(
                name='find_reach_id',
                url=f'{self.root_url}/findReachID',
                controller=f'{self.package}.controllers.find_reach_id'
            )
        )
