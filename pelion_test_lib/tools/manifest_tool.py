"""
Copyright 2019-2020 ARM Limited
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Manifest tool helper
Prerequisites: manifest-tool has been cloned from github

"""

import logging
import subprocess
import os
import uuid

log = logging.getLogger(__name__)

BINARIES = 'bin'
MANIFEST_TOOL = 'manifest-tool'
UPDATE_DEFAULT_RESOURCES = 'update_default_resources.c'
SETTINGS_FILE = '.manifest_tool.json'


def init(working_path, vendor_domain=None, model_name=None):
    """
    Call 'manifest-tool init' to create a certificate, private key and default settings file.
    :param working_path: Path where to run the manifest-tool
    :param vendor_domain: "company domain name"
    :param model_name: "product model identifier"
    :return: Path to update_default_resources.c path if it was created. Else None
    """
    log.debug('manifest-tool init - START')
    if vendor_domain is None:
        vendor_domain = '{}.com'.format(uuid.uuid4().hex)
    if model_name is None:
        model_name = uuid.uuid4().hex
    command = [MANIFEST_TOOL, 'init', '-d', vendor_domain, '-m', model_name, '-q', '-f']
    log.debug(command)
    p = subprocess.Popen(command, cwd=working_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if stdout:
        log.debug(stdout)
    if stderr:
        log.warning(stderr)
    log.debug('manifest-tool init - DONE')
    f = os.path.join(os.sep, working_path, UPDATE_DEFAULT_RESOURCES)
    if os.path.isfile(f):
        log.debug('Path to update_default_resources.c: {}'.format(f))
        return os.path.abspath(f)
    log.error('Could not find update_default_resources.c')
    return None


def create_manifest(path, firmware_url, update_image_path, output='output.manifest', delta_manifest=None):
    """
    Create a manifest file
    :param path: Manifest-tool path
    :param firmware_url: URL to firmware image
    :param update_image_path: Path to local update image
    :param output: Manifest file name
    :param delta_manifest: File name of the json input file generated by delta-tool in case of delta update
    :returns: Path to a manifest file on success. Otherwise None.
    :raises: OSError if invalid or inaccessible file name or path.
             ValueError if Popen is called with invalid arguments.
    """
    log.info('Creating manifest for update campaign with manifest-tool...')
    log.debug('manifest-tool create - START')
    path = os.path.abspath(path)
    # remove file if it exists
    if os.path.isfile(output):
        os.remove(output)
    cmd = [MANIFEST_TOOL, 'create', '-u', firmware_url, '-o', output]
    if delta_manifest:
        log.debug('Specifying delta payload')
        cmd.append('-i')
        cmd.append(delta_manifest)
        cmd.append('--payload-format')
        cmd.append('bsdiff-stream')
    else:
        cmd.append('-p')
        cmd.append(update_image_path)
    log.debug(cmd)
    p = subprocess.Popen(cmd, cwd=path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if stdout:
        log.debug(stdout)
    if stderr:
        log.warning(stderr)
    log.debug('manifest-tool create - DONE')
    # return path to manifest file
    f = os.path.join(os.sep, path, output)
    if os.path.isfile(f):
        if os.path.getsize(f) <= 0:
            log.error('Manifest file size is 0')
            return None
        log.info('Manifest created!')
        return os.path.abspath(f)
    log.error('Could not find manifest file')
    return None