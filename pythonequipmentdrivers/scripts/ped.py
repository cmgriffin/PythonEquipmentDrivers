r"""
This is a callable script that will start an interactive shell (ipython if installed else vanilla python)
where the globals() == EnviromentSetup(). The intent is to allow creation of a generic CLI for working with
the bench equiptment

ped - starts the CLI
ped setup - performs the setup necessary for the CLI namely selection of the .json file to use for the enviroment setup
The config file (ped.json) is located in the user home folder. Windows: c:users\USERNAME\.ped\ped.json
"""

from pathlib import Path
import tkinter
import shutil
from tkinter.filedialog import askopenfilename
import json
import argparse
import pythonequipmentdrivers as ped

CONFIG_PATH = Path('.ped/bench_config.json')
config_path = Path.home() / CONFIG_PATH


def check_if_setup():
    parser = argparse.ArgumentParser(
        description='Run the pythonequiptmentdrivers CLI')
    parser.add_argument('--setup', action='store_true')
    args = parser.parse_args()
    return args.setup


def run_cli():
    if not config_path.is_file():
        raise FileNotFoundError(
            f'{config_path} file not found \n run "ped --setup" to configure')
    temp = ped.EnvironmentSetup(config_path)
    vars().update(vars(temp))  # transfer
    banner = '\n\nPythonEquiptmentDrivers CLI\n'
    try:
        import IPython
        IPython.embed(colors="neutral", banner1=banner)
    except ImportError:
        import code
        variables = globals().copy()
        variables.update(locals())
        shell = code.InteractiveConsole(variables)
        shell.interact(banner=banner)


def run_setup():
    json_path = askopenfilename(
        title='Select the bench configuration json file...', filetypes=[("json", '.json')])
    if json_path == '':
        raise ValueError('No valid file was selected')
    json_path = Path(json_path)
    config_folder = config_path.parent
    try:
        config_folder.mkdir()
    except FileExistsError:
        # directory already exists
        pass
    shutil.copyfile(json_path, config_path)


def main():
    if check_if_setup():
        # run the setup routine
        run_setup()
    else:
        # just run the CLI
        run_cli()


if __name__ == '__main__':
    main()
