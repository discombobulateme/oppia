# Copyright 2017 The Oppia Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Helper script used for creating a new release or hotfix branch on GitHub.

ONLY RELEASE COORDINATORS SHOULD USE THIS SCRIPT.

Usage: Run this script from your oppia root folder:

For release branch:

    python -m scripts.cut_release_or_hotfix_branch --version="x.y.z"

where x.y.z is the new version of Oppia, e.g. 2.5.3. The generated branch
name will be release-x.y.z, e.g. release-2.5.3.

For hotfix branch:

    python -m scripts.cut_release_or_hotfix_branch --version="x.y.z"
    --hotfix_number=d

where x.y.z is the new version of Oppia, e.g. 2.5.3,
d is number of the hotfix being created, e.g. 1. The generated branch
name will be release-x.y.z-hotfix-d, e.g. release-2.5.3-hotfix-1.
"""

from __future__ import absolute_import  # pylint: disable=import-only-modules
from __future__ import unicode_literals  # pylint: disable=import-only-modules

import argparse
import json
import re
import subprocess
import sys

import python_utils
import release_constants

from . import common


def new_version_type(arg, pattern=re.compile(r'\d\.\d\.\d')):
    """Checks that the new version name matches the expected pattern.

    Args:
        arg: str. The new version name.
        pattern: RegularExpression. The pattern that release version should
            match.

    Raises:
        argparse.ArgumentTypeError: The new version name does not match
            the pattern.

    Returns:
        str. The new version name with correct pattern.
    """
    if not pattern.match(arg):
        raise argparse.ArgumentTypeError(
            'The format of "new_version" should be: x.x.x')
    return arg


_PARSER = argparse.ArgumentParser()
_PARSER.add_argument(
    '--new_version', help='new version to be released', type=new_version_type)
_PARSER.add_argument('--hotfix_number', default=0)

PARSED_ARGS = _PARSER.parse_args()
if PARSED_ARGS.new_version:
    TARGET_VERSION = PARSED_ARGS.new_version
else:
    raise Exception('ERROR: A "new_version" arg must be specified.')

# Construct the new branch name.
HOTFIX_NUMBER = int(PARSED_ARGS.hotfix_number)
if not HOTFIX_NUMBER:
    NEW_BRANCH_NAME = '%s-%s' % (
        release_constants.RELEASE_BRANCH_TYPE, TARGET_VERSION)
    NEW_BRANCH_TYPE = release_constants.RELEASE_BRANCH_TYPE
else:
    NEW_BRANCH_NAME = '%s-%s-%s-%s' % (
        release_constants.RELEASE_BRANCH_TYPE, TARGET_VERSION,
        release_constants.HOTFIX_BRANCH_TYPE, HOTFIX_NUMBER)
    NEW_BRANCH_TYPE = release_constants.HOTFIX_BRANCH_TYPE


def _verify_target_branch_does_not_already_exist(remote_alias):
    """Checks that the new release branch doesn't already exist locally or
    remotely.

    Args:
        remote_alias: str. The alias that points to the remote oppia
            repository. Example: When calling git remote -v, you get:
            upstream    https://github.com/oppia/oppia.git (fetch),
            where 'upstream' is the alias that points to the remote oppia
            repository.

    Raises:
        Exception: The target branch name already exists locally.
        Exception: The target branch name already exists on the remote
            oppia repository.
    """

    git_branch_output = subprocess.check_output(['git', 'branch'])
    if NEW_BRANCH_NAME in git_branch_output:
        raise Exception(
            'ERROR: The target branch name already exists locally. '
            'Run "git branch -D %s" to delete it.' % NEW_BRANCH_NAME)
    git_ls_remote_output = subprocess.check_output(
        ['git', 'ls-remote', '--heads', remote_alias])
    remote_branch_ref = 'refs/heads/%s' % NEW_BRANCH_NAME
    if remote_branch_ref in git_ls_remote_output:
        raise Exception(
            'ERROR: The target branch name already exists on the remote repo.')


def _verify_target_version_is_consistent_with_latest_released_version():
    """Checks that the target version is consistent with the latest released
    version on GitHub.

    Raises:
        Exception: Failed to fetch latest release info from GitHub.
        Exception: Could not parse version number of latest GitHub release.
        AssertionError: The previous and the current major version are not the
            same.
        AssertionError: The current patch version is not equal to previous patch
            version plus one.
        AssertionError: The current patch version is greater or equal to 10.
        AssertionError: The current minor version is not equal to previous
            minor version plus one.
        AssertionError: The current patch version is different than 0.
    """
    response = python_utils.url_open(
        'https://api.github.com/repos/oppia/oppia/releases/latest')
    if response.getcode() != 200:
        raise Exception(
            'ERROR: Failed to fetch latest release info from GitHub')

    data = json.load(response)
    latest_release_tag_name = data['tag_name']

    match_result = re.match(r'v(\d)\.(\d)\.(\d)', latest_release_tag_name)
    if match_result is None:
        raise Exception(
            'ERROR: Could not parse version number of latest GitHub release.')
    prev_major, prev_minor, prev_patch = match_result.group(1, 2, 3)

    match_result = re.match(r'(\d)\.(\d)\.(\d)', TARGET_VERSION)
    curr_major, curr_minor, curr_patch = match_result.group(1, 2, 3)

    # This will need to be overridden if the major version changes.
    assert prev_major == curr_major, 'Unexpected major version change.'
    if prev_minor == curr_minor:
        assert int(curr_patch) == int(prev_patch) + 1
        assert int(curr_patch) < 10
    else:
        assert int(curr_minor) == int(prev_minor) + 1
        assert int(curr_patch) == 0


def _verify_hotfix_number_is_one_ahead_of_previous_hotfix_number(
        remote_alias):
    """Checks that the hotfix number is one ahead of previous hotfix
    number.

    Args:
        remote_alias: str. The alias that points to the remote oppia
            repository. Example: When calling git remote -v, you get:
            upstream    https://github.com/oppia/oppia.git (fetch),
            where 'upstream' is the alias that points to the remote oppia
            repository.

    Raises:
        Exception: The difference between two continuous hotfix numbers
             is not one.
    """
    all_branches = subprocess.check_output([
        'git', 'branch', '-a'])[:-1].split('\n')

    last_hotfix_number = 0
    hotfix_branch_name_regex = '^%s/%s-%s-%s-\\d*$' % (
        remote_alias, release_constants.RELEASE_BRANCH_TYPE, TARGET_VERSION,
        release_constants.HOTFIX_BRANCH_TYPE)
    for branch_name in all_branches:
        branch_name = branch_name.lstrip().rstrip()
        if re.match(hotfix_branch_name_regex, branch_name):
            hotfix_number = int(branch_name[branch_name.rfind('-') + 1:])
            if hotfix_number > last_hotfix_number:
                last_hotfix_number = hotfix_number

    assert HOTFIX_NUMBER == last_hotfix_number + 1


def _execute_branch_cut():
    """Pushes the new release branch to Github."""

    # Do prerequisite checks.
    common.require_cwd_to_be_oppia()
    common.verify_local_repo_is_clean()
    common.verify_current_branch_name('develop')

    # Update the local repo.
    remote_alias = common.get_remote_alias(release_constants.REMOTE_URL)
    subprocess.call(['git', 'pull', remote_alias])

    _verify_target_branch_does_not_already_exist(remote_alias)
    _verify_target_version_is_consistent_with_latest_released_version()

    # The release coordinator should verify that tests are passing on develop
    # before checking out the release branch.
    common.open_new_tab_in_browser_if_possible(
        'https://github.com/oppia/oppia#oppia---')
    while True:
        if not HOTFIX_NUMBER:
            branch_to_check = 'develop'
        elif HOTFIX_NUMBER == 1:
            branch_to_check = '%s-%s' % (
                release_constants.RELEASE_BRANCH_TYPE, TARGET_VERSION)
        else:
            branch_to_check = '%s-%s-%s-%s' % (
                release_constants.RELEASE_BRANCH_TYPE, TARGET_VERSION,
                release_constants.HOTFIX_BRANCH_TYPE, HOTFIX_NUMBER - 1)
        python_utils.PRINT(
            'Please confirm: are Travis checks passing on %s? (y/n) ' % (
                branch_to_check))
        answer = python_utils.INPUT().lower()
        if answer in release_constants.AFFIRMATIVE_CONFIRMATIONS:
            break
        elif answer:
            python_utils.PRINT(
                'Tests should pass on %s before this script is run. '
                'Exiting.' % branch_to_check)
            sys.exit()

    # Cut a new release or hotfix branch.
    if NEW_BRANCH_TYPE == release_constants.HOTFIX_BRANCH_TYPE:
        _verify_hotfix_number_is_one_ahead_of_previous_hotfix_number(
            remote_alias)
        if HOTFIX_NUMBER == 1:
            branch_to_cut_from = '%s-%s' % (
                release_constants.RELEASE_BRANCH_TYPE, TARGET_VERSION)
        else:
            branch_to_cut_from = '%s-%s-%s-%s' % (
                release_constants.RELEASE_BRANCH_TYPE, TARGET_VERSION,
                release_constants.HOTFIX_BRANCH_TYPE, HOTFIX_NUMBER - 1)
        python_utils.PRINT('Cutting a new hotfix branch: %s' % NEW_BRANCH_NAME)
        subprocess.call([
            'git', 'checkout', '-b', NEW_BRANCH_NAME, branch_to_cut_from])
    else:
        python_utils.PRINT('Cutting a new release branch: %s' % NEW_BRANCH_NAME)
        subprocess.call(['git', 'checkout', '-b', NEW_BRANCH_NAME])

    # Push the new release branch to GitHub.
    python_utils.PRINT('Pushing new %s branch to GitHub.' % NEW_BRANCH_TYPE)
    subprocess.call(['git', 'push', remote_alias, NEW_BRANCH_NAME])

    python_utils.PRINT('')
    python_utils.PRINT(
        'New %s branch successfully cut. You are now on branch %s' % (
            NEW_BRANCH_TYPE, NEW_BRANCH_NAME))
    python_utils.PRINT('Done!')


if __name__ == '__main__':
    _execute_branch_cut()
