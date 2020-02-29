# Created by Patrick Kao
import argparse
import json5
import os
from collections import OrderedDict
import subprocess
from subprocess import Popen
from pathlib import Path
import distutils.dir_util
import sys


def list_to_file(filename, list_to_write):
    with open(filename, 'w') as filehandle:
        for listitem in list_to_write:
            filehandle.write('{}\n'.format(listitem))


def file_to_list(filename):
    to_ret = []
    with open(filename, 'r+') as filehandle:  # a+ makes file if not exist
        for line in filehandle:
            # remove linebreak which is the last character of the string
            currentPlace = line[:-1]

            # add item to the list
            to_ret.append(currentPlace)
    return to_ret


def update_progress(progress, name, script_loc):
    # Update progress file
    progress.append(name)
    list_to_file("{}/progress.txt".format(script_loc), progress)

def process_command(cmd):
        # Sys.stdin and sys.stdout instead of PIPE redirect output
        command = Popen(cmd, executable='bash', shell=True, stdin=sys.stdin, stdout=sys.stdout,
                        universal_newlines=True)
        command.communicate()
        result = command.returncode
        if result != 0:
            raise SystemError

def ternary(line):
        args = line.split("*?")
        cond  = args[0]
        opts  = args[1].split("*:")
        ternary_expr = "if [" + cond + "]; then " + opts[0] + ";  else " + opts[1] + " ; fi"
        return ternary_expr


def install_pack(progress, name, script_loc, package):
    # Run line
    try:
        for index, line in enumerate(package[:]):
            print(">>{}".format(line))
            # Check for macros
            if 'break:' in line:
                # Displays message and exits
                print(line.replace('break:', ''))
                update_progress(progress, name, script_loc)
                return
            elif 'info:' in line:
                # Displays message and continues
                print(line.replace('info:', ''))
            elif 'ternary:' in line:
                # Denotes a bash ternary conditional of the form:
                # expr *? opt1 *: opt2
                line = line.replace('ternary:', '')
                ternary_expr = ternary(line)
                process_command(ternary_expr)
            else:
                # Bare bash
                process_command(line)

    except SystemError:
        ("Package {} failed installing at line {}".format(name, line))

    update_progress(progress, name, script_loc)


def install_packages():
    parser = argparse.ArgumentParser(description='A tutorial of argparse!')
    parser.add_argument("--workdir", default="/home/{}/temp".format(os.getenv('USER')), type=str,
                        help="Working directory")
    parser.add_argument("--ignore-progress", default=False, type=bool, help="Don't install the same package twice")
    parser.add_argument("--package", default=None, type=str, help="Install 1 specific package (adds to progress)")
    parser.add_argument("--file", default="./packages.json5", type=str,
                        help="Path to json file that contains packages to install")

    args = parser.parse_args()

    script_loc = os.getcwd()
    # load package dict
    with open(args.file, 'r') as file:
        packages = json5.load(file, object_pairs_hook=OrderedDict)

    # load progress list
    progress_file = "{}/progress.txt".format(script_loc)
    Path(progress_file).touch()
    progress = file_to_list(progress_file)

    # Make and switch to workng directory
    os.system("mkdir -p {}".format(args.workdir))
    # Copy resources into workdir
    distutils.dir_util.copy_tree("{}/resources".format(os.getcwd()), "{}".format(args.workdir))

    os.chdir(args.workdir)

    if args.package is not None:
        if args.package in packages:
            install_pack(progress, args.package, script_loc, packages[args.package])
        else:
            print("Could not find package {} in list".format(args.package))
    else:
        # Iterate through packages
        for name, package in packages.items():
            # check progress
            if (name in progress) and (not args.ignore_progress):
                print("Already installed package {}. Skipping".format(name))
                continue

            install_pack(progress, name, script_loc, package)


if __name__ == "__main__":
    install_packages()
