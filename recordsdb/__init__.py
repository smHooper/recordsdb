import os
import json
import docopt
import re

CONFIG_JSON = os.path.join(os.path.dirname(__file__), '../../config/config.json')

if not os.path.isfile(CONFIG_JSON):
    raise IOError(
        f'No config file found at {os.path.abspath(CONFIG_JSON)}. A directory named "config" with a config.json file'
         ' must exist at the same directory level as the package directory.'
    )

with open(CONFIG_JSON) as f:
    config = json.load(f)


def get_docopt_args(doc):
    """
    Get command line arguments as a dictionary
    :return: dictionary of arguments
    """
    # Any args that don't have a default value and weren't specified will be None
    cl_args = {k: v for k, v in docopt.docopt(doc).items() if v is not None}

    # get rid of extra characters from doc string and 'help' entry
    args = {re.sub('[<>-]*', '', k): v for k, v in cl_args.items() if k != '--help' and k != '-h'}

    # convert numeric values
    for k, v in args.items():
        if type(v) == bool or v == None:
            continue
        elif re.fullmatch('\d*', v):
            args[k] = int(v)
        elif re.fullmatch('\d*\.\d*', v):
            args[k] = float(v)

    return args