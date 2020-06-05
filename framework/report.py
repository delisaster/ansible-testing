""" CSV REPORT """

import csv


class Report:
    """Creates a CSV report for the testing framework.
    Report format will be
    Test name, Number of iterations run, Number of failed iterations
    """

    def __init__(self, test_list=None, file_name='report.csv'):
        """ Initilizes an report from a list of tests.
        A test_list of None is an indication that the report should be a dummy
        one, with all noop operations """

        # report_data format:
        # ---
        # 01_test_neutron:
        #    completed_iterations: 0
        #    failed_iterations: 0
        self.report_data = None
        if test_list:
            self.report_data = {}

            for test in test_list:
                self.report_data[test['test_name']] = {'completed_iterations': 0,
                                                       'failed_iterations': 0}

        self.file_name = file_name

    def add_result(self, test_name, successful):
        """ Adds a result to the report """

        if self.report_data:
            self.report_data[test_name]['completed_iterations'] += 1
            if not successful:
                self.report_data[test_name]['failed_iterations'] += 1

            self.print_report()

    def print_report(self):
        """ Print the CSV file"""

        if self.report_data:
            with open(self.file_name, 'w', newline='') as csvfile:
                fieldnames = ['Test', 'Completed Iterations', 'Failed Iterations']
                writer = csv.writer(csvfile)
                writer.writerow(fieldnames)
                for test in self.report_data:
                    writer.writerow([test,
                                     self.report_data[test]['completed_iterations'],
                                     self.report_data[test]['failed_iterations']])


if __name__ == '__main__':

    # unit testing
    EMPTY_REPORT = Report(None)
    TEST_REPORT = Report([{'thread': 'some_thred',
                           'runner': 'some_object',
                           'test_name': '01_test_neutron',
                           'test_directory': 'some_directory',
                           'test_type': 'setup',
                           'iteration': 1,
                           'failures': 0}],
                         '/tmp/report.csv')
    EMPTY_REPORT.add_result('foo', True)
    TEST_REPORT.add_result('01_test_neutron', True)
