# ansible-runner-looper

Simple python wrapper around ansible-runner for performing tests in parallel and in sequence.

## Functional Testing

The run-functional.py script executes a number of functional tests in parallel.

**usage: run-functional.py -c CONFIGFILE [-p PLAN[,PLAN]...]**

**OPTIONS**
**-c --config**  
Configuration file, described below.

**-p PLAN**  
Comma-seperated list of test plans, described below. The testing framework will look for plans in the _plans_directory_ specified in the config file.   
It should be noted that specifying a test plan will override any enabled tests in the config file.

## HA Testing

The run-ha.py script sources a directory of ansible-runner jobs and invokes them in a random sequential order.  Any job failure terminates the run and exits.   

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
| test_directory  | Directory containing the tests. <br> This is the directory containing the _functional_tests_ subdirectory | - / required

**Ansible Runner Settings:**  
This section contain key-value pairs corresponding to the Ansible Runner library [Settings](https://ansible-runner.readthedocs.io/en/latest/intro.html#env-settings-settings-for-runner-itself).

**Enabled Functional Tests:**  
If this section exists, only the tests listed here will be executed.

## Plan files
The Plan files are in the YAML format with the following structure:

```YAML
---
functional_tests:
  - a_test
  - another_test
```
It should be noted that specifying a plan file on the command line has precedence over any tests specified in the config file.

## Example
```
./run-functional.py -c ../config.ini -p openstack
```
