# This file is a part of Arjuna
# Copyright 2015-2020 Rahul Verma

# Website: www.RahulVerma.net

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#   http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import abc
import os
import re
import argparse
import tempfile
import shutil
import logging
import traceback
import json
import sys
import abc

from arjuna.tpi.constant import *
from arjuna.core.constant import *
from arjuna.core.utils import sys_utils
from arjuna.core.utils import file_utils
from arjuna.core.reader.hocon import HoconFileReader, HoconConfigDictReader
from arjuna.configure.cli import CliArgsConfig
from .validation import *


class Command(metaclass=abc.ABCMeta):
    PENTRY = '''
    project.name = {}
    workspace.dir = "{}"
    '''

    def __init__(self):
        self.parser = None

    def print_help(self):
        self.parser.print_help()

    def _set_parser(self, parser):
        self.parser = parser

    def get_parser(self):
        return self.parser

    @abc.abstractmethod
    def execute(self, integrator, arg_dict):
        pass


class MainCommand(Command):

    def __init__(self):
        super().__init__()
        parser = argparse.ArgumentParser(prog='python -m arjuna', conflict_handler='resolve',
                                description="This is the CLI of Arjuna. Use the appropriate command and sub-commands as needed.")
        self._set_parser(parser)

    def create_subparsers(self):
        return self.parser.add_subparsers(title="Valid Commands", description="What do you want Arjuna to do?", dest='command')

    def convert_to_dict(self, args):
        def format_value(k, v):
            # if k in {"ao", "uo", "irules", "erules", 'ip', 'ep', }:
            #     return v
            if k == "report.formats" and v is None:
                v = ['XML', 'HTML']
            # if type(v) is list:
            #     return ",".join([str(i) for i in v])
            # else:
            return v
        try:
            args = self.parser.parse_args(args[1:])
            return {k:format_value(k,v) for k,v in vars(args).items()}
        except Exception as e:
            print("!!!Fatal Error!!!")
            print(e)
            import traceback
            traceback.print_exc()
            sys_utils.fexit()
        import sys
        sys.exit(1)

    def execute(self, arg_dict):
        pass


class FileObjectType(Enum):
    DIR = auto()
    FILE = auto()


class CreateProject(Command):

    COMMON_DIRS_FILES = (
        (FileObjectType.DIR, "config"),
        (FileObjectType.FILE, "config/data.yaml"),
        (FileObjectType.FILE, "config/envs.yaml"),
        (FileObjectType.FILE, "config/groups.yaml"),
        (FileObjectType.FILE, "config/project.yaml"),
        (FileObjectType.FILE, "config/sessions.yaml"),
        (FileObjectType.FILE, "config/stages.yaml"),
        (FileObjectType.FILE, "config/withx.yaml"),
        (FileObjectType.DIR, "data"),
        (FileObjectType.DIR, "data/source"),
        (FileObjectType.DIR, "data/reference"),
        (FileObjectType.DIR, "data/reference/excel_column"),
        (FileObjectType.DIR, "data/reference/excel_row"),
        (FileObjectType.DIR, "l10n"),
        (FileObjectType.DIR, "l10n/excel"),
        (FileObjectType.DIR, "l10n/json"),
        (FileObjectType.DIR, "guiauto"),
        (FileObjectType.DIR, "guiauto/driver"),
        (FileObjectType.DIR, "guiauto/driver/linux"),
        (FileObjectType.DIR, "guiauto/driver/mac"),
        (FileObjectType.DIR, "guiauto/driver/windows"),
        (FileObjectType.DIR, "guiauto/namespace"),
        (FileObjectType.DIR, "hook"),
        (FileObjectType.FILE, "hook/arjuna_config.py"),
        (FileObjectType.DIR, "report"),
        (FileObjectType.DIR, "script"),
        (FileObjectType.DIR, "test"),
        (FileObjectType.FILE, "test/__init__.py"),
        (FileObjectType.DIR, "test/pkg"),
        (FileObjectType.FILE, "test/pkg/__init__.py"),
        (FileObjectType.DIR, "lib"),
        (FileObjectType.FILE, "lib/__init__.py"),
        (FileObjectType.DIR, "lib/fixture"),
        (FileObjectType.FILE, "lib/fixture/__init__.py"),
        (FileObjectType.FILE, "lib/fixture/group.py"),
        (FileObjectType.FILE, "lib/fixture/module.py"),
        (FileObjectType.FILE, "lib/fixture/test.py"),
    )

    def __init__(self, subparsers, parents):
        super().__init__()
        self.parents = parents
        parser = subparsers.add_parser('create-project', parents=[parent.get_parser() for parent in parents], help="Create a new project")
        self._set_parser(parser)

    def __create_file_or_dir(self, project_temp_dir, ftype, frpath):
        if ftype == FileObjectType.DIR:
            os.makedirs(os.path.join(project_temp_dir, frpath))
        else:
            f = open(os.path.join(project_temp_dir, frpath), "w")
            f.close()

    def execute(self, arg_dict):
        def get_src_file_path(src):
            return os.path.join(os.path.dirname(os.path.realpath(__file__)), src)

        def get_proj_target_path(dest):
            return os.path.join(project_temp_dir, dest)

        def copy_file(src, dest):
            shutil.copyfile(get_src_file_path(src), get_proj_target_path(dest))

        for parent in self.parents:
            parent.process(arg_dict)
        # from arjuna import ArjunaCore
        pdir = arg_dict['project.root.dir']
        if os.path.exists(os.path.join(pdir, "config/project.yaml")):
            print("Arjuna project already exists at the specified location.")
            sys.exit(1)
        parent_dir = os.path.abspath(os.path.join(pdir, ".."))
        project_name = os.path.basename(pdir)
        with tempfile.TemporaryDirectory() as tdir:
            project_temp_dir = os.path.join(tdir, project_name)
            os.makedirs(project_temp_dir)
            for ftype, frpath in CreateProject.COMMON_DIRS_FILES:
                self.__create_file_or_dir(project_temp_dir, ftype, frpath)
            copy_file("../../res/project.yaml", "config/project.yaml")
            copy_file("../../res/check_dummy.py", "test/pkg/check_dummy.py")
            copy_file("../../res/arjuna_launcher.py", "script/arjuna_launcher.py")
            f = open(get_src_file_path("../../res/conftest.txt"), "r")
            contents = f.read().format(project=project_name)
            f.close()
            f = open(get_proj_target_path("test/conftest.py"), "w")
            f.write(contents)
            f.close()
            for d in ["data/source", "l10n/excel", "l10n/json", "data/reference/excel_row", "data/reference/excel_column", "guiauto/namespace"]:
                copy_file("../../res/placeholder.txt", d + "/placeholder.txt")
            for os_name in ["mac", "windows", "linux"]:
                copy_file("../../res/placeholder.txt", "guiauto/driver/{}/placeholder.txt".format(os_name))
            for f in os.listdir(project_temp_dir):
                try:
                    shutil.move(os.path.join(project_temp_dir, f), pdir)
                except Exception as e:
                    print(e)
                    pass

        print("Project {} successfully created at {}.".format(project_name, parent_dir))


class __RunCommand(Command):
    def __init__(self, subparsers, sub_parser_name, parents, help):
        super().__init__()
        self.parents = parents
        parser = subparsers.add_parser(sub_parser_name, parents=[parent.get_parser() for parent in parents], help=help)
        self._set_parser(parser)
        self.enumerate_only = False

    def execute(self, arg_dict):
        for parent in self.parents:
            parent.process(arg_dict)

        from arjuna import Arjuna
        project_root_dir = arg_dict.pop("project.root.dir")
        runid = arg_dict.pop("run.id")
        static_rid = arg_dict.pop("static.rid")
        self.dry_run = arg_dict.pop("dry_run")
        if self.dry_run:
            self.dry_run = DryRunType[self.dry_run]
        
        if "ref_conf" in arg_dict:
            self.ref_conf_name = arg_dict.pop("ref_conf")

        self.pop_command_args(arg_dict)

        Arjuna.init(project_root_dir, CliArgsConfig(arg_dict), runid, static_rid=static_rid)

        import sys
        proj_dir = Arjuna.get_config().value(ArjunaOption.PROJECT_ROOT_DIR)
        sys.path.append(proj_dir + "/..")

        py_3rdparty_dir = Arjuna.get_config().value(ArjunaOption.ARJUNA_EXTERNAL_IMPORTS_DIR)
        sys.path.append(py_3rdparty_dir)

    def pop_command_args(self, arg_dict):
        pass


class RunProject(__RunCommand):
    def __init__(self, subparsers, parents):
        super().__init__(subparsers, 'run-project', parents, "Run all tests in an Arjuna Test Project in a single thread.")
        self.ref_conf_name = None

    def execute(self, arg_dict):
        super().execute(arg_dict)
        from arjuna import Arjuna
        session = Arjuna.get_test_session()
        session.load_tests(dry_run=self.dry_run, ref_conf_name=self.ref_conf_name)
        session.run()


class RunSession(__RunCommand):
    def __init__(self, subparsers, parents):
        super().__init__(subparsers, 'run-session', parents, "Run tests as per the named test session definition in sessions.yaml.")

    def execute(self, arg_dict):
        super().execute(arg_dict)
        from arjuna import Arjuna
        session = Arjuna.get_test_session()
        session.load_tests(dry_run=self.dry_run, ref_conf_name=self.ref_conf_name)
        session.run()

class RunStage(__RunCommand):
    def __init__(self, subparsers, parents):
        super().__init__(subparsers, 'run-stage', parents, "Run tests as per the named test stage definition in stages.yaml.")
        self.__stage_name = None

    def execute(self, arg_dict):
        super().execute(arg_dict)
        from arjuna import Arjuna
        session = Arjuna.get_test_session()
        session.load_tests_for_stage(stage_name=self.__stage_name, dry_run=self.dry_run, ref_conf_name=self.ref_conf_name)
        session.run()

    def pop_command_args(self, arg_dict):
        self.__stage_name = arg_dict.pop("stage_name")

class RunGroup(__RunCommand):
    def __init__(self, subparsers, parents):
        super().__init__(subparsers, 'run-group', parents, "Run tests as per the named test group definition in groups.yaml.")
        self.__group_name = None

    def execute(self, arg_dict):
        super().execute(arg_dict)
        from arjuna import Arjuna
        session = Arjuna.get_test_session()
        session.load_tests_for_group(group_name=self.__group_name, dry_run=self.dry_run, ref_conf_name=self.ref_conf_name)
        session.run()

    def pop_command_args(self, arg_dict):
        self.__group_name = arg_dict.pop("group_name")


class RunSelected(__RunCommand):

    def __init__(self, subparsers, parents):
        super().__init__(subparsers, 'run-selected', parents, "Run tests selected based on selectors specified in a single thread.")
        self.ref_conf_name = None
        self.__pickers_dict = dict()
        self.__rules = {'ir': [], 'er': []}

    def execute(self, arg_dict):
        super().execute(arg_dict)

        from arjuna import Arjuna
        session = Arjuna.get_test_session()
        session.load_tests(rules=self.__rules, dry_run=self.dry_run, ref_conf_name=self.ref_conf_name)
        session.run()

    def pop_command_args(self, arg_dict):
        from arjuna.engine.session.group import TestGroup
        i_e_rules = TestGroup.create_rule_strs(arg_dict)
        self.__rules['ir'].extend(i_e_rules['ir'])
        self.__rules['er'].extend(i_e_rules['er'])
        irule_strs = arg_dict.pop('ir')
        if irule_strs:
            self.__rules['ir'].extend(irule_strs)
        erule_strs = arg_dict.pop('er')
        if erule_strs:
            self.__rules['er'].extend(erule_strs)

