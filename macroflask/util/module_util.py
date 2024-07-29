import importlib
import os
import sys

"""
This module indicates how to import a python module
"""


def import_module(module_name):
    try:
        # print(sys.path)
        module = importlib.import_module(module_name)
        print(f"Module '{module_name}' has been imported.")
        return module
    except ImportError as e:
        print(str(e))
        print(f"Module '{module_name}' not found.")
        return None


def import_module_by_path_and_suffix_name(path: str, suffix_name: str):
    """
    Import all Python modules in a given directory that end with a specific suffix.

    This function will scan the directory specified by 'path', and import all Python
    modules that have file names ending with 'suffix_name'.
    The modules are imported using the 'import_module' function.

    :param path: The path to the directory to scan for modules. This should be a string
                 representing a valid directory path.

    :param suffix_name: The suffix to match against the file names in the directory. This
                        should be a string. Only files that have names ending with this
                        suffix will be imported.
    :return: None
    """
    target_file_path = os.path.realpath(path)
    target_dir_path = os.path.dirname(target_file_path)
    # print(f"Current file path: {target_file_path}")

    # Get all files in the target directory
    target_files = os.listdir(target_dir_path)

    # Get the latest directory name in the common path
    target_dir_name = target_dir_path.split(os.sep)[-1]
    current_file_path = os.path.realpath(__file__)
    common_path = os.path.commonpath([target_file_path, current_file_path])
    latest_dir_name_in_common_path = common_path.split(os.sep)[-1]

    for file in target_files:
        # Check if the file name ends with the provided suffix name
        if file.endswith(suffix_name + '.py'):
            module_name = '.'.join([latest_dir_name_in_common_path, target_dir_name, file[:-3]])  # remove '.py'
            # print(module_name)
            import_module(module_name)