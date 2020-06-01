import os
from errno import ENOENT


class ConfigFileNotFoundError(FileNotFoundError):
    def __init__(self, path: str):
        super(ConfigFileNotFoundError, self).__init__(ENOENT, os.strerror(ENOENT), path)


class InvalidModuleNameError(ValueError):
    def __init__(self, module_name: str):
        super(InvalidModuleNameError, self).__init__(
            "The module name {} could not be resolved".format(module_name)
        )


class YamlExtraRequiredError(Exception):
    def __init__(self):
        super(YamlExtraRequiredError, self).__init__(
            'In order to parse YAML files, appcfg has to be installed with the ["yaml"] extra.'
        )
