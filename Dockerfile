FROM registry.access.redhat.com/ubi8:latest
USER root
RUN yum install -y --enablerepo=ansible-2-for-rhel-8-x86_64-rpms ansible && \
    yum install -y --enablerepo=rhceph-4-tools-for-rhel-8-x86_64-rpms ansible-runner && \
    yum install -y --enablerepo=openstack-16-tools-for-rhel-8-x86_64-rpms python3-openstackclient &&\
    yum install -y  jq python3 python3-ansible-runner python3-pyyaml

USER 1001

WORKDIR testing 
COPY framework  framework

CMD ["/bin/bash","-c","source external/${openstackrc} && python3 framework/run_tests.py -c external/config.ini -p ${plan}"]
