import configparser
import contextlib
import logging
from deadman import Deadman

config = configparser.ConfigParser()
config.read("/etc/paranoidnas.conf")


def get_deadman(name: str) -> contextlib.AbstractContextManager:
    try:
        guid = config["deadman"][f"{name}_id"]
        return Deadman(guid)
    except:
        logging.warn("Oops! No id.")
        return contextlib.nullcontext()
