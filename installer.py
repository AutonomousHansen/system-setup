# Created by Patrick Kao
import argparse
import pyjson5
import os
from collections import OrderedDict
import subprocess
from subprocess import Popen
from pathlib import Path
import distutils.dir_util
import sys
import pprint
from pprint import pprint as print
import traceback as tb


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
        stdout, stderr = command.communicate()
        result = command.returncode
        if result != 0:
            print(stderr)
            raise SystemError

def jump(raw_expr, cur_index, pack):
        # Processes a jump command of the form:
        # `jump: cond -? int1 -: int2`
        # where int1 defaults to the the current line 
        condition, indices = raw_expr.split('-?')
        indices = indices.split('-:')
        if indices[0].strip() == '':
            indices[0] = cur_index + 1
        if "END" in indices[1]:
            indices[1] = len(pack) - 1
        print(indices)
        ternary_expr = "if [" + condition + "]; then echo \'" + str(indices[0]) + "';  else echo \'" + str(indices[1]) + "\'; fi"
        command = Popen(ternary_expr, executable='bash', shell=True, stdin=sys.stdin, stdout=subprocess.PIPE, universal_newlines=True)
        jump_ind, stderr = command.communicate()
        print(jump_ind)
        print(command.returncode)
        if command.returncode != 0:
            print(command.returncode)
            raise SystemError
        else:
            return jump_ind


def install_pack(progress, name, script_loc, package):
    # Run line
    try:
        i = 0
        while i < len(package):
            line = package[i]
            print(">>{}".format(line))
            # Check for macros
            if 'break:' in line:
                # Displays message and exits with given code
                line = line.replace('break:', '')
                code, msg = line.split(':', 1)
                update_progress(progress, name, script_loc)
                msg = "echo " + msg
                process_command(msg)
                # Defaulting to return 0 if the format break:: was used
                if code.strip() == '':
                    code = 0
                code = int(code)
                if code != 0:
                    exit(code)
                else:
                    return
                
            elif 'info:' in line:
                # Displays message and continues
                line = line.replace('info:', '')
                line = "echo " + line
                process_command(line)
            elif 'jump:' in line:
                # Jumps to different line in package
                expr = line.replace('jump:', '')
                jump_line = jump(expr, i, package)
                i = int(jump_line) - 1
            else:
                # Bare bash
                process_command(line)
            i = i + 1
            update_progress(progress, name, script_loc)

    except SystemError:
        ("Package {} failed installing at line {}".format(name, line))
        exit

def install_packages():
    parser = argparse.ArgumentParser(description='A tutorial of argparse!')
    parser.add_argument("--workdir", default="/home/{}/temp".format(os.getenv('USER')), type=str,
                        help="Working directory")
    parser.add_argument("--ignore-progress", default=False, type=bool, help="Don't install the same package twice")
    parser.add_argument("--package", default=None, type=str, help="Install 1 specific package (adds to progress)")
    parser.add_argument("--file", default="./packages.json5", type=str,
                        help="Path to json file that contains packages to install")
    parser.add_argument("--resources", default="./resources", type=str, help="Path to resources")

    args = parser.parse_args()

    script_loc = os.getcwd()

    # load package dict
    with open(args.file, 'r') as file:
        try:
            packages = OrderedDict(pyjson5.decode_io(file))
        except pyjson5.Json5DecoderException as e:
            print('{}:\n{}'.format(type(e), e.message))
            print('Broke at point:\n {}'.format(e.result), compact=True)
            return


    # load progress list
    progress_file = "{}/progress.txt".format(script_loc)
    Path(progress_file).touch()
    progress = file_to_list(progress_file)

    # Make and switch to workng directory
    os.system("mkdir -p {}".format(args.workdir))
    # Copy resources into workdir
    distutils.dir_util.copy_tree("{}".format(args.resources), "{}".format(args.workdir))

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
