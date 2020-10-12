from setuptools import setup, find_namespace_packages
from tethys_apps.app_installation import find_resource_files

# -- Apps Definition -- #
app_package = 'geoglows_hydroviewer'
release_package = 'tethysapp-' + app_package

# -- Python Dependencies -- #
dependencies = []

# -- Get Resource File -- #
resource_files = find_resource_files('tethysapp/' + app_package + '/templates', 'tethysapp/' + app_package)
resource_files += find_resource_files('tethysapp/' + app_package + '/public', 'tethysapp/' + app_package)
resource_files += find_resource_files('tethysapp/' + app_package + '/workspaces', 'tethysapp/' + app_package)


setup(
    name=release_package,
    version='1.4.0',
    description='Interfaces with the GEOGloWS ECMWF Streamflow model developed by the BYU Hydroinformatics lab.',
    long_description='Contains an interactive map interface for retrieving data using the ESRI Dynamic Mapping Service '
                     'retrieved from the Living Atlas. Includes tools for extracting a subset of the delineated '
                     ' shapefiles and creating a customized hydroviewer interface.',
    keywords='geoglows, ',
    author='Riley Hales, Kyler Ashby',
    author_email='',
    url='',
    license='BSD 3-Clause Clear',
    packages=find_namespace_packages(),
    package_data={'': resource_files},
    include_package_data=True,
    zip_safe=False,
    install_requires=dependencies,
)
