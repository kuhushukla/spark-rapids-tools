# Copyright (c) 2023, NVIDIA CORPORATION.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utility and helper methods"""

import os
import pathlib
import re
import sys
from functools import reduce
from operator import getitem
from typing import Any, Optional

import fire
from pydantic import ValidationError, AnyHttpUrl, TypeAdapter

import spark_rapids_pytools
from spark_rapids_tools.exceptions import CspPathAttributeError
from spark_rapids_pytools.common.utilities import Utils
from spark_rapids_pytools.common.sys_storage import FSUtil


def get_elem_from_dict(data, keys):
    try:
        return reduce(getitem, keys, data)
    except LookupError:
        print(f'ERROR: Could not find elements [{keys}]')
        return None


def get_elem_non_safe(data, keys):
    try:
        return reduce(getitem, keys, data)
    except LookupError:
        return None


def stringify_path(fpath) -> str:
    if isinstance(fpath, str):
        actual_val = fpath
    elif hasattr(fpath, '__fspath__'):
        actual_val = os.fspath(fpath)
    else:
        raise CspPathAttributeError('Not a valid path')
    expanded_path = os.path.expanduser(actual_val)
    # make sure we return absolute path
    return os.path.abspath(expanded_path)


def is_http_file(value: Any) -> bool:
    try:
        TypeAdapter(AnyHttpUrl).validate_python(value)
        return True
    except ValidationError:
        # ignore
        return False


def get_path_as_uri(fpath: str) -> str:
    if re.match(r'\w+://', fpath):
        # that's already a valid url
        return fpath
    # stringify the path to apply the common methods which is expanding the file.
    local_path = stringify_path(fpath)
    return pathlib.PurePath(local_path).as_uri()


def to_camel_case(word: str) -> str:
    return word.split('_')[0] + ''.join(x.capitalize() or '_' for x in word.split('_')[1:])


def to_camel_capital_case(word: str) -> str:
    return ''.join(x.capitalize() for x in word.split('_'))


def to_snake_case(word: str) -> str:
    return ''.join(['_' + i.lower() if i.isupper() else i for i in word]).lstrip('_')


def dump_tool_usage(tool_name: Optional[str], raise_sys_exit: Optional[bool] = True):
    imported_module = __import__('spark_rapids_tools.cmdli', globals(), locals(), ['ToolsCLI'])
    wrapper_clzz = getattr(imported_module, 'ToolsCLI')
    help_name = 'ascli'
    usage_cmd = f'{tool_name} --help'
    try:
        fire.Fire(wrapper_clzz(), name=help_name, command=usage_cmd)
    except fire.core.FireExit:
        # ignore the sys.exit(0) thrown by the help usage.
        # ideally we want to exit with error
        pass
    if raise_sys_exit:
        sys.exit(1)


def gen_app_banner() -> str:
    """
    ASCII Art is generated by an online Test-to-ASCII Art generator tool https://patorjk.com/software/taag
    :return: a string representing the banner of the user tools including the version
    """

    c_ver = spark_rapids_pytools.__version__
    return rf"""

********************************************************************
*                                                                  *
*    _____                  __      ____              _     __     *
*   / ___/____  ____ ______/ /__   / __ \____ _____  (_)___/ /____ *
*   \__ \/ __ \/ __ `/ ___/ //_/  / /_/ / __ `/ __ \/ / __  / ___/ *
*  ___/ / /_/ / /_/ / /  / ,<    / _, _/ /_/ / /_/ / / /_/ (__  )  *
* /____/ .___/\__,_/_/  /_/|_|  /_/ |_|\__,_/ .___/_/\__,_/____/   *
*     /_/__  __                  ______    /_/     __              *
*       / / / /_______  _____   /_  __/___  ____  / /____          *
*      / / / / ___/ _ \/ ___/    / / / __ \/ __ \/ / ___/          *
*     / /_/ (__  )  __/ /       / / / /_/ / /_/ / (__  )           *
*     \____/____/\___/_/       /_/  \____/\____/_/____/            *
*                                                                  *
*                                      Version. {c_ver}            *
*                                                                  *
* NVIDIA Corporation                                               *
* spark-rapids-support@nvidia.com                                  *
********************************************************************

"""


def init_environment(short_name: str):
    """
    Initialize the Python Rapids tool environment.
    Note:
    - This function is not implemented as the `__init__()` method to avoid execution
      when `--help` argument is passed.
    """
    # Set the 'UUID' environment variable with a unique identifier.
    uuid = Utils.gen_uuid_with_ts(suffix_len=8)
    Utils.set_rapids_tools_env('UUID', uuid)

    # Set the 'tools_home_dir' to store logs and other configuration files.
    home_dir = Utils.get_sys_env_var('HOME', '/tmp')
    tools_home_dir = FSUtil.build_path(home_dir, '.spark_rapids_tools')
    Utils.set_rapids_tools_env('HOME', tools_home_dir)

    # Set the 'LOG_FILE' environment variable and create the log directory.
    log_dir = f'{tools_home_dir}/logs'
    log_file = f'{log_dir}/{short_name}_{uuid}.log'
    Utils.set_rapids_tools_env('LOG_FILE', log_file)
    FSUtil.make_dirs(log_dir)

    # Print the log file location
    print(Utils.gen_report_sec_header('Application Logs'))
    print(f'Location: {log_file}')
    print('In case of any errors, please share the log file with the Spark RAPIDS team.\n')
