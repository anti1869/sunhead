VERSION_NUMBER = "5.0.1a3"
PACKAGE_NAME = "SunHead"
VERSION_CODENAME = "Early Dawn"


def get_version(full=False):
    if full:
        return "%s %s %s" % (PACKAGE_NAME, VERSION_NUMBER, VERSION_CODENAME)
    else:
        return VERSION_NUMBER


__version__ = get_version()
