import sys

from tango import DevFailed, Util
from .device import CATS, CATSClass, ISARA2, ISARA2Class

SERVER_NAME = 'PyCATS'
_DEVICE_REF = None
_UTIL = None


def core_loop():
    global _DEVICE_REF

    if _DEVICE_REF is not None:
        if isinstance(_DEVICE_REF, CATS):
            CATS.check_reconnection(_DEVICE_REF)
            CATS.update_status(_DEVICE_REF)
        elif isinstance(_DEVICE_REF, ISARA2):
            ISARA2.check_reconnection(_DEVICE_REF)
            ISARA2.update_status(_DEVICE_REF)
    else:
        dev_list = _UTIL.get_device_list("*")
        for dev in dev_list:
            if isinstance(dev, CATS):
                _DEVICE_REF = dev
                break
            elif isinstance(dev, ISARA2):
                _DEVICE_REF = dev
                break

def run(args=None):
    try:
        global _UTIL

        if not args:
            args = sys.argv[1:]
            args = [SERVER_NAME] + list(args)

        util = Util(args)
        util.add_class(CATSClass, CATS, 'CATS')
        util.add_class(ISARA2Class, ISARA2, 'ISARA2')

        u = Util.instance()
        _UTIL = u
        u.server_set_event_loop(core_loop)
        u.server_init()
        u.server_run()

    except DevFailed as e:
        print('-------> Received a DevFailed exception:', e)
    except Exception as e:
        print('-------> An unforeseen exception occured....', e)


if __name__ == "__main__":
    run()
