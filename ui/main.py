"""Entrypoint for Kivy app."""

from kivy.logger import Logger as log
from kivymd.app import MDApp

# from plyer import storagepath


class OsmFieldworkApp(MDApp):
    """The main Kivy app."""

    def __init__(self, *args, **kwargs):
        """When the Kivy app is initialised."""
        log.info(f"{self.__class__.__name__}: app __init___")
        super(OsmFieldworkApp, self).__init__(*args, **kwargs)

    def on_build(self):
        """Run when a build is initiated."""
        log.info(f"{self.__class__.__name__}: on_build called")

        self.title = "OSM-Fieldwork"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Red"

    def on_kv_post(self):
        """Called once the .kv file is loaded.

        .kv code is the app_name.kv file.
        """
        log.info(f"{self.__class__.__name__}: kv file processed.")

    def on_start(self):
        """On app start."""
        log.info(f"{self.__class__.__name__}: on_start called")

    def on_pause(self):
        """On app pause."""
        log.info(f"{self.__class__.__name__}: on_pause called")
        # Return true to prevent app closing on pause
        # default is to close app
        return True

    def on_resume(self):
        """On app resume."""
        log.info(f"{self.__class__.__name__}: on_resume called")

    def on_stop(self):
        """On app stop / shutdown."""
        log.info(f"{self.__class__.__name__}: on_stop called")

    @property
    def storage(self):
        """Conveience property to get app private storage."""
        # Update storage dir as needed
        return self.user_data_dir

    def download_basemap(
        self,
        boundary: str = "6.119728,45.905957,6.126509,45.909869",
        zooms: str = "13-14",
        source: str = "esri",
        output_name: str = "basemap.mbtiles",
    ):
        """Wrapper to download basemaps."""
        download_dir = OsmFieldworkApp.get_running_app().storage
        output_file = f"{download_dir}/{output_name}"
        log.info(f"Downloading tiles to to {download_dir}")
        log.info(f"Generating basemap {output_file}")

        # Plyer doesn't work?
        # log.warning(storagepath.get_documents_dir())
        # Use androidstorage4kivy
        # https://github.com/Android-for-Python/Android-for-Python-Users#sharing-a-file-between-apps
        # https://github.com/Android-for-Python/share_send_example/blob/main/main.py

        # create_basemap_file(
        #     boundary=boundary,
        #     outfile=output_file,
        #     zooms=zooms,
        #     source=source,
        #     outdir=download_dir,
        # )


if __name__ == "__main__":
    """Main func for calling main.py directly (to start app)."""
    OsmFieldworkApp().run()
