import os

from nonocaptcha import package_dir


class JSLibs:
    def __init__(self):
        self.CACHED_LIBS = {}

    def compose_resource_path(self, resource, lib_path='data'):
        if '.js' not in resource:
            resource = resource + '.js'

        if resource in self.CACHED_LIBS.keys() and not force_load:
            return self.CACHED_LIBS[resource]

        return os.path.join(package_dir, lib_path, resource)

    def load_lib(self, resource, lib_path='data', force_load=False):
        resource_path = self.compose_resource_path(resource, lib_path)
        try:
            with open(resource_path, 'r') as reader:
                self.CACHED_LIBS[resource] = reader.read()

            return self.CACHED_LIBS[resource]
        except FileNotFoundError as ex:
            error_message = "{}{}{}".format(
                'Loading pip package resource failure. We expected',
                f' [{os.path.join("<pip_lib_path>", lib_path, resource)}]',
                ' yet what we got was [{}]'.format(resource_path))
            raise FileNotFoundError(error_message)
        except Exception:
            raise

    def deface(self, target_site_recaptcha_anchor):
        return self.load_lib('deface').replace(
            '<target_site_recaptcha_anchor>',
            target_site_recaptcha_anchor)

    @property
    def check_detection(self):
        return self.load_lib('check_detection')

    @property
    def iframe_wait_load(self):
        return self.load_lib('iframe_wait_load')

    @property
    def jquery(self):
        return self.load_lib('jquery')

    @property
    def override(self):
        return self.load_lib('override')

JS_LIBS = JSLibs()