#!/usr/bin/env python3
"""Framework for executing Infrastructure tests"""

import argparse
import ast
import configparser
import random
import sys
import ansible_runner
import os
import re
import time
import yaml

from report import Report

ansible_tests_list = []
ansible_run_list = []
tests_list = []
debug = False

ANSI_COLORS = {'cyan': '\033[36m',
               'green': '\033[32m',
               'magenta': '\033[35m',
               'red': '\033[31m',
               'yellow': '\033[33m',
               'reset': '\033[0m'}


def parse_command_line():
    """Parses command line and returns a dict with commandline optinons"""
    parser = argparse.ArgumentParser(
        description='Run ansible playbooks concurrently and with loops',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-c', '--config', dest='config_file',
                        required=True, action='store',
                        help='Config file in ini format')
    parser.add_argument('-p', '--plan', dest='test_plan',
                        required=False, action='store',
                        help='Test Plan to use.\nDo note that this option will override any Enabled Tests in the config file')

    return parser.parse_args()

def parse_config_file(config_file):
    """Parses config file, returning a ConfigParser object"""

    my_config = configparser.ConfigParser(allow_no_value=True)
    my_config.read(config_file)

    mandatory_options = ['test_directory']
    for option in mandatory_options:
        if not my_config.has_option('General', option):
            sys.exit('Option %s missing in configuration file' % option)

    return my_config


def get_tests_from_config():
    """Read test list from config file """

    tests = {}
    tests['functional'] = []
    tests['ha'] = []

    if config.has_section('Enabled Functional Tests'):
        enabled_tests = config.items('Enabled Functional Tests')
        for test in enabled_tests:
            tests['functional'].append(test[0])

    if config.has_section('Enabled HA Tests'):
        enabled_tests = config.items('Enabled HA Tests')
        for test in enabled_tests:
            tests['ha'].append(test[0])

    return tests


def get_tests_from_directory():
    """Return all tests in the functional_tests directory"""

    functional_path = os.path.join(config.get('General', 'test_directory'),
                                   'functional_tests')
    ha_path = os.path.join(config.get('General', 'test_directory'), 'ha_tests')

    functional_tests = []
    ha_tests = []

    if os.path.exists(functional_path):
        functional_tests = os.listdir(functional_path)

    if os.path.exists(ha_path):
        ha_tests = os.listdir(ha_path)

    return {'functional': functional_tests,
            'ha': ha_tests
            }


def get_tests_from_plan(plans):
    """Read the specified plan, returning list of tests to run. """

    plans_dir = config.get('General', 'plans_directory',
                           fallback=None)

    # fallback
    if not plans_dir:
        plans_dir = os.path.join(config.get('General',
                                            'test_directory'),
                                 'plans')

    tests = {}
    tests['functional'] = []
    tests['ha'] = []
    for plan in plans.split(sep=','):
        file_path = get_filename(plans_dir, plan)

        with open(file_path, 'r') as f:
            plan = yaml.safe_load(f)

        tests['functional'].extend(plan.get('functional_tests', []))
        tests['ha'].extend(plan.get('ha_tests', []))

    return tests


def get_filename(directory='.', base_name=None):
    """ Checks for a file with both .yaml and .yml extension and returns the
    one that exists."""

    for ext in ['.yaml', '.yml']:
        f = os.path.join(directory, base_name + ext)
        if os.path.exists(f):
            return f

    raise FileNotFoundError(F'Could not find neither {base_name}.yaml nor ' +
                            F'{base_name}.yml in {directory}')


def launch_ansible_test(test_to_launch, test_type, invocation, failure_count):
    """Launches the specified test,
    returning a reference to the running test"""

    test_directory = config.get('General', 'test_directory')

    inventory = config.get('General', 'inventory', fallback=None)
    if not inventory:
        inventory = os.path.join(test_directory, 'inventory/hosts')

    inventory_list = inventory.split(',')

    # Finally, if the fallback inventry
    if len(inventory_list) == 1 and not os.path.exists(inventory_list[0]):
        inventory_list = None

    extravars_file = config.get('General',
                                'extra_vars',
                                fallback='extra_vars.yaml')
    extravars = None
    if os.path.exists(extravars_file):
        with open(extravars_file, 'r') as f:
            extravars = yaml.safe_load(f)

    private_data_dir = test_directory + '/' + test_to_launch
    output_dir = config.get('General', 'output_directory', fallback=None)
    if output_dir:
        private_data_dir = output_dir + '/' + test_to_launch
        os.makedirs(private_data_dir, mode=0o700, exist_ok=True)

    if config and config.has_section('Ansible Runner Settings'):
        settings = dict(config.items('Ansible Runner Settings'))
    else:
        settings = None

     # ansible_runner.interface.run _SHOULD_ take a dict here. But it doesn't )-:
     # So instead we'll write a yaml file into the output dir, this seem to work...
    if settings and output_dir:

        # first convert from strings
        for v in settings:
            try:
                settings[v] = ast.literal_eval(settings[v])
            except ValueError:
                pass

        os.makedirs(private_data_dir + '/env', mode=0o700, exist_ok=True)
        if os.path.exists(private_data_dir + '/env/settings'):
            os.remove(private_data_dir + '/env/settings')
        with open(private_data_dir + '/env/settings', 'w') as f:
            yaml.safe_dump(settings, f)

    playbook = get_filename(os.path.join(test_directory,
                                         test_type + '_tests',
                                         test_to_launch),
                            'test')

    fact_caching = config.get('General', 'fact_caching', fallback=None)

    # Keep as many generations of artifacts as we have interations
    keepartifacts = config.getint('General', 'iterations', fallback=20)

    (t, r) = ansible_runner.interface.run_async(
        private_data_dir=private_data_dir,
        playbook=playbook,
        inventory=inventory_list,
        extravars=extravars,
        rotate_artifacts=keepartifacts,
        ident=test_type + '_' + str(invocation) + '_' + str(failure_count),
        fact_cache_type=fact_caching)
    return({
        'thread': t,
        'runner': r,
        'test': test_to_launch
    })


def launch_ansible_tests(lists_of_tests):
    """Launces tests and initialises list of running tests to monitor"""

    running_tests = []

    # Launch all functional tests at once
    for test in lists_of_tests['functional']:
        launched_test = launch_ansible_test(test,
                                            'functional',
                                            1,
                                            0)
        running_tests.append({
            'thread': launched_test['thread'],
            'runner': launched_test['runner'],
            'test_name': launched_test['test'],
            'test_type': 'functional',
            'iteration': 1,
            'failures': 0
        })
        print("{}Launching functional: {} - {} iteration {}{}".format(
            ANSI_COLORS['yellow'], test, launched_test['runner'].status,
            1, ANSI_COLORS['reset'])
        )

    # And now, also an HA one
    # We're picking a random one to launch,
    # the remainder will be added to the run_list unlaunched
    if lists_of_tests['ha']:
        test = random.choice(lists_of_tests['ha'])
        launched_test = launch_ansible_test(test,
                                            'ha',
                                            1,
                                            0)
        running_tests.append({
            'thread': launched_test['thread'],
            'runner': launched_test['runner'],
            'test_name': launched_test['test'],
            'test_type': 'ha',
            'iteration': 1,
            'failures': 0
        })
        print("{}Launching ha: {} - {} iteration {}{}".format(
            ANSI_COLORS['yellow'], test, launched_test['runner'].status,
            1, ANSI_COLORS['reset'])
        )

        # Add remaining tests to run_list unlaunced
        lists_of_tests['ha'].remove(test)
        for test in lists_of_tests['ha']:
            running_tests.append({
                'thread': None,
                'runner': None,
                'test_name': test,
                'test_type': 'ha',
                'iteration': 0,
                'failures': 0
            })

    return(running_tests)


def relaunch_test(run_list, test):
    """ Relaunch a test.
    If it's a functional one, just relaunch it
    If it's an HA one, pick a random one from the list)
    """

    max_iterations = config.getint('General', 'iterations', fallback=20)
    max_failures = config.getint('General', 'max_failures', fallback=3)
    finished = False

    if test['iteration'] >= max_iterations or test['failures'] >= max_failures:
        run_list.remove(test)
        finished = True

        if test['failures'] >= max_failures:
            print(f"{ANSI_COLORS['red']}Error : {test['test_type']}" +
                  f" {test['test_name']} - {test['runner'].status};" +
                  f" iteration {test['iteration']} Max failures exceeded," +
                  f" removeing test{ANSI_COLORS['reset']}")

        # Success
        else:
            print("{}Complete {}: {} - {} iteration {}{}".format(
                ANSI_COLORS['green'],
                test['test_type'],
                test['test_name'],
                test['runner'].status,
                test['iteration'],
                ANSI_COLORS['reset'])
            )

    if test['test_type'] == 'functional' and not finished:
        launched_test = launch_ansible_test(test['test_name'],
                                            test['test_type'],
                                            test['iteration'],
                                            test['failures'])
        index = run_list.index(test)
        run_list[index]['thread'] = launched_test['thread']
        run_list[index]['runner'] = launched_test['runner']
        run_list[index]['iteration'] += 1
        print("{}Launching {}: {} - {} iteration {}{}".format(
                            ANSI_COLORS['yellow'],
                            test['test_type'],
                            test['test_name'],
                            test['runner'].status,
                            test['iteration'],
                            ANSI_COLORS['reset']))

    # For HA tests, we want to launch a new test,
    # even if the current one is finished
    elif test['test_type'] == 'ha':

        # Start by marking the current test as non-running
        if not finished:
            run_list[run_list.index(test)]['runner'] = None

        ha_tests = list(filter(lambda x: x['test_type'] == 'ha', run_list))

        if ha_tests:
            test_candidate = ha_tests[random.randrange(len(ha_tests))]
            launched_test = launch_ansible_test(test_candidate['test_name'],
                                                'ha',
                                                test_candidate['iteration'],
                                                test_candidate['failures'])

            index = run_list.index(test_candidate)
            run_list[index]['thread'] = launched_test['thread']
            run_list[index]['runner'] = launched_test['runner']
            run_list[index]['iteration'] += 1
            print("{}Launching {}: {} - {} iteration {}{}".format(
                                ANSI_COLORS['yellow'],
                                test_candidate['test_type'],
                                test_candidate['test_name'],
                                test_candidate['runner'].status,
                                test_candidate['iteration'],
                                ANSI_COLORS['reset']))


def check_ansible_loop(run_list):
    """Checks on running tests and re-launces them required number of times"""

    # Initialize report
    report_file = config.get('General', 'report', fallback='report.csv')
    report = Report(run_list, report_file)

    # Good thing to keep in mind:
    # iteration - Currently running iteration
    #  (as opposed to completed ones)
    # failures - Number of failed iterations.
    # Therefore marked after test completes

    while run_list:

        # filter out only tests which are running
        running_tests = filter(lambda x: x['runner'], run_list)

        for test in running_tests:
            if test['runner'].status == 'successful':
                report.add_result(test['test_name'], successful=True)
                relaunch_test(run_list, test)

            elif test['runner'].status == 'running' or test['runner'].status == 'starting':
                if debug:
                    print("{}Running : {} - {} :{}: iteration {}{}".format(
                        ANSI_COLORS['cyan'],
                        test['test_name'],
                        test['runner'].status,
                        test['test_type'],
                        test['iteration'],
                        ANSI_COLORS['reset'])
                    )
            else:
                report.add_result(test['test_name'], successful=False)
                run_list[run_list.index(test)]['failures'] += 1
                relaunch_test(run_list, test)
        time.sleep(2)


if __name__ == '__main__':
    args = parse_command_line()
    config = parse_config_file(args.config_file) if args.config_file else None

    # If plan is given on command line, read tests from there
    if args.test_plan:
        ansible_tests_list = get_tests_from_plan(args.test_plan)

    # Else take tests from config file
    elif (config.has_section('Enabled Functional Tests') or
            config.has_section('Enabled HA Tests')):
        ansible_tests_list = get_tests_from_config()

    # If none of the above, just run all tests in the
    # functional-tests directory
    else:
        ansible_tests_list = get_tests_from_directory()

    ansible_run_list = launch_ansible_tests(ansible_tests_list)
    check_ansible_loop(ansible_run_list)
