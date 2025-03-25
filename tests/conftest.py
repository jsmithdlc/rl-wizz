import logging


def pytest_sessionstart(session):
    # Libraries to shush should be specified here
    libraries_to_shush = [""]
    for library in libraries_to_shush:
        logging.getLogger(library).setLevel(logging.WARNING)