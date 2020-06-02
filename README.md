# run-tests

Python script for performing infrastructure testing.  

The script will run a number of user-defined functional tests in parallel.  
To make a test round more interesting, this script also have the capability of executing a number of user-defined High-Availability tests which introduce failures, such as crashing a control node, into the system.

The idea is that an high-availability test only should be check that the system recovers after the failure. The functional tests which run simultaneously should detect if the high availability test introduced any outage in the system.

All tests are written in Ansible and available in a separate repository.

## Testing

The run_tests.py script executes the tests.

**usage: run_tests.py -c CONFIGFILE [-p PLAN[,PLAN]...]**

**OPTIONS**
**-c --config**  
Configuration file, described below.

**-p PLAN**  
Comma-seperated list of test plans, described below. The testing framework will look for plans in the _plans_directory_ specified in the config file.   
It should be noted that specifying a test plan will override any enabled tests in the config file.

## Configuration file
The scripts take as input a configuration file in [ini](https://en.wikipedia.org/wiki/INI_file) format.

The following sections are defined:

**General:**

| Key             | Description| Default
|-----            |----------  | ---
| extra_vars      | Path to YAML file containing Ansible extra-vars | extra_vars.yaml
| fact_caching    | The [fact caching](https://docs.ansible.com/ansible/latest/reference_appendices/config.html#cache-plugin) to use. <br> Set to _memory_ to revert to Ansible default ephemeral cache. | jsonfile
|inventory        | Path to Ansible inventory | %(test_directory)s/inventory/hosts
| iterations      | Number of iterations to run | 20
| max_failures    | Number of failed iterations after which a test is disabled| 3
| output_directory| Directory to store all output of the test runs | %(test_directory)s
| plans_directory | Directory containing test plans | %(test_directory)s/plans
| report          | File-name where report will be written | report.csv
| test_directory  | Directory containing the tests. <br> This is the directory containing the _functional_tests_ and _ha_tests_ subdirectory | - / required

**Ansible Runner Settings:**  
This section contain key-value pairs corresponding to the Ansible Runner library [Settings](https://ansible-runner.readthedocs.io/en/latest/intro.html#env-settings-settings-for-runner-itself).

**Enabled Functional Tests / Enabled HA Tests:**  
If any of these sections exists, only the tests listed here will be executed.

## Plan files
The Plan files are in the YAML format with the following structure:

```YAML
---
functional_tests:
  - a_test
  - another_test
ha_tests:
  - an_ha_test
  - yet_another_ha_test
```
It should be noted that specifying a plan file on the command line has precedence over any tests specified in the config file.

## Example
```
./run_tests.py -c ../config.ini -p openstack
```
