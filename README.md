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
| fact_caching    | The [fact caching](https://docs.ansible.com/ansible/latest/reference_appendices/config.html#cache-plugin) to use. | memory
|inventory        | Comma-separated list of Ansible inventories | %(test_directory)s/inventory/hosts
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

# run-tests-podman

This section covers building a framework container and some specifics related to running tests using containerized framework. This approach is useful when there is a need to run all the tests from within a locked-down network. It implies that container is built from a RHEL8 machine which has all the containerization prerequisites installed. Later, container file can be exported and imported to any machine within a locked-down network capable of running containers.

## Building a container image

```
podman build .
```

Build process installs all the required packages and copies the entire framework folder to the container image /testing folder.

## Exporting the image

```
podman save <image_id> > image_filename.tar
```
This will export previously built image to a file so it can be tranported and used on any other machine.

## Importing the image

```
podman load < image_filename.tar
```
This will import the image on the any machine where tests are going to be run.

## Running the tests

```
podman run -v </path/to/folder/containing/needed/files>:/testing/external:z -e openstackrc=<openstackrc_file> -e plan=<plan>  <image_id>
```
The command will mount local foder containing ansible test repository and all other needed files, to container folder /testing/external. It will take openstackrc file reference and plan reference defined in telco-tests plans folder.

Mandatory files and folders:
- <test_repository>
- <config_file>
- <extravars_file>
- <openstackrc_file>

Keep in mind when adjusting config.ini that container is not aware of any files outside /testing/external.

Here is an example snippet of config.ini references having in mind container folder /testing/external:
```
[General]
test_directory = /testing/external/telco-tests
plans_directory = /testing/external/telco-tests/plans
inventory = /testing/external/telco-tests/inventory/hosts
report    = /testing/external/report.csv
extra_vars = /testing/external/extravars
iterations = 1
max_failures = 3
output_directory = /testing/external/output
```

If you are going to test image upload, put an image file into the mounted folder and correspondingly adjust img_filename reference within extravars.

## Example
```
podman run -v /opt/ansible-testing-framework/mount_to_docker:/testing/external:z -e openstackrc=my_adminrc -e plan=openstack  765ef8246ca8
```
