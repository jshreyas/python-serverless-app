import json
import base64
import time
import math
import datetime
import urllib.request
import urllib.error
import pytz


def get_timestamp():
    """ Returns timestamp in desired format """

    return datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')


class Testrail(object):

    def __init__(self, user, password, base_url="https://velocloud.testrail.com"):
        """ Testrail initializer

        Args:
            user (str): Username to authorize with
            password (str): Password
            base_url (str): Testrail URL
        """

        self.user = user
        self.password = password
        self.__run_id = None
        self.result_map = {
            "passed": 1,
            "failed": 5
        }

        self.cases_in_run = {}
        if not base_url.endswith('/'):
            base_url += '/'
        self.__url = base_url + 'index.php?/api/v2/'

        self.__project = None
        self.__project_id = None
        self.__suite = None
        self.__suite_id = None

        self.project = "Velocloud"
        self.suite = "Master"

    @property
    def project(self):
        return self.__project

    @project.setter
    def project(self, project_name):
        self.__project = project_name
        if project_name is not None:
            self.__project_id = self.__get_project_by_name(project_name)["id"]
        else:
            self.__project_id = None

    @property
    def project_id(self):
        if self.__project_id:
            return self.__project_id
        raise EnvironmentError(
            "Define the project name as an object attribute like so\n"
            "client.project = 'Velocloud'")

    @property
    def suite(self):
        return self.__suite

    @suite.setter
    def suite(self, suite_name):
        self.__suite = suite_name
        if suite_name is not None:
            self.__suite_id = self.__get_suite_by_name(suite_name)["id"]
        else:
            self.__suite_id = None

    @property
    def suite_id(self):
        if self.__suite_id:
            return self.__suite_id
        raise EnvironmentError(
            "Define the suite name as an object attribute like so\n"
            "client.suite = 'Master'")

    @property
    def run_id(self):
        return self.__run_id

    @run_id.setter
    def run_id(self, run_id):

        self.__run_id = run_id
        self.cases_in_run = {
            run_id: self.get_cases_in_run(run_id=run_id)
        }

    def get_cases_in_run(self, run_id):
        """ Returns the test cases associated to a test run

        Args:
            run_id (str): id of the run

        Returns:
            list: response of the API call of the test cases associated to a run
        """
        return self.send_get("get_tests/{run_id}".format(run_id=run_id))

    def get_all_cases(self):
        """ Returns all test cases from testrail

        Returns:
            list: list of all test cases
        """

        return self.send_get(f"get_cases/{self.project_id}")

    def get_milestone_id(self, name):
        """ Returns milestone id based on given name

        Returns:
            integer: Milestone ID
        """

        milestone_list = self.send_get(f"get_milestones/{self.project_id}")
        if milestone_list:
            for elem in milestone_list:
                if name in elem['name']:
                    return elem['id']

    def get_cases_based_on_milestone(self, milestone_id):
        """ Returns testcase ID list based on milestone

        Returns:
            list: Testcase list
        """

        total_cases = self.send_get(f"get_cases/{self.project_id}&milestone_id={milestone_id}")
        case_list = []
        for elem in total_cases:
            case_list.append(elem['id'])
        return case_list

    def get_sections(self):
        """ Gets all sections

        Returns:
            list: list of all sections
        """

        return self.send_get(f"get_sections/{self.project_id}")

    def send_get(self, uri):
        """ Send Get

        Issues a GET request (read) against the API and returns the result
        (as Python dict).

        Args:
            uri (str): The API method to call including parameters
                (e.g. get_case/1)

        """
        return self.__send_request('GET', uri, None)

    def send_post(self, uri, data):
        """ Send POST

        Issues a POST request (write) against the API and returns the result
        (as Python dict).

        Args:
            uri (str): The API method to call including parameters
                (e.g. add_case/1)
            data (dict): The data to submit as part of the request (as
                Python dict, strings must be UTF-8 encoded)
        """
        return self.__send_request('POST', uri, data)

    def __send_request(self, method, uri, data):

        url = self.__url + uri
        request = urllib.request.Request(url)
        if method == 'POST':
            request.data = bytes(json.dumps(data), 'utf-8')
        auth = str(
            base64.b64encode(
                bytes('%s:%s' % (self.user, self.password), 'utf-8')
            ),
            'ascii'
        ).strip()
        request.add_header('Authorization', 'Basic %s' % auth)
        request.add_header('Content-Type', 'application/json')

        e = None
        try:
            response = urllib.request.urlopen(request).read()
        except urllib.error.HTTPError as ex:
            response = ex.read()
            e = ex

        if response:
            result = json.loads(response.decode())
        else:
            result = {}

        if e is not None:
            if result and 'error' in result:
                error = '"' + result['error'] + '"'
            else:
                error = 'No additional error message received'
            raise APIError('TestRail API returned HTTP %s (%s)' %
                           (e.code, error))

        return result

    def __get_projects(self):
        """ Returns a list of projects """

        url = f"get_projects"
        return self.send_get(url)

    def __get_project_by_name(self, project_name):
        """ Searches for an exact match of the project name

        Args:
            project_name (string): name of the project

        Returns:
            dict: project
            None: if there is no match
        """

        projects = self.__get_projects()
        for project in projects:
            if project_name == project["name"]:
                return project
        return None

    def __get_suites(self, project_id=None):
        """ Returns a list of suites for a project

        Args:
            project_id (str): project id

        Returns:
            list: list of suites in a project
        """

        if not project_id:
            project_id = self.project_id
        url = f"get_suites/{project_id}"
        return self.send_get(url)

    def __get_suite_by_name(self, suite_name, project_id=None):
        """ Searches for an exact match of the suite name for a given project

        Args:
            suite_name (string): name of the suite
            project_id (string): project id

        Returns:
            dict: suite
            None: if there is no match
        """

        if not project_id:
            project_id = self.project_id
        suites = self.__get_suites(project_id)
        for suite in suites:
            if suite_name == suite["name"]:
                return suite
        return None

    def get_users(self):
        """ Returns users information

        Returns:
            list: list of users
        """

        url = "get_users"
        return self.send_get(url)

    def get_case(self, case_id):
        """ Returns test case information

        Args:
            case_id (string): test case id

        Returns:
            dict: case
        """

        url = f"get_case/{case_id}"
        return self.send_get(url)

    def update_case(self, case_id, data):
        """ Updates test case information

        Args:
            case_id (string): test case id
            data (dict)L dictionary of the testcase attributes
        """

        return self.send_post(
            uri=f'update_case/{case_id}',
            data=data)

    def _get_plan_by_name(self, plan_name, project_id=None):
        """ Searches for an exact match of the test plan name for a given project

        Args:
            plan_name (string): name of the test plan
            project_id (string): project id

        Returns:
            dict: plan
            None: if there is no match
        """

        if not project_id:
            project_id = self.project_id
        plans = self._get_plans(project_id)
        for plan in plans:
            if plan_name == plan["name"]:
                return plan
        return None

    def _get_plans(self, project_id=None):
        """ Returns a list of test plans for a project

        Args:
            project_id (string): project id

        Returns:
            list: list of test plans
        """

        if not project_id:
            project_id = self.project_id
        url = f"get_plans/{project_id}"
        return self.send_get(url)

    def _get_plan(self, plan_id):
        """ Returns an existing test plan along with all its runs

        Args:
            plan_id (int): plan id

        Returns:
            dict: test plan entry
        """

        url = f"get_plan/{plan_id}"
        return self.send_get(url)

    def _add_plan_entry(self, plan_id, data):
        """ Add test run/entry to a test plan

        Args:
            plan_id (string): test plan id
            data (dict): post body data

        Returns:
            dict: test plan entry
        """

        url = f"add_plan_entry/{plan_id}"
        return self.send_post(url, data)

    def format_testrun(self, test_run):
        """ Formats test run with time stamp """

        # return test_run
        date_format = '%Y-%m-%d %H:%M'
        date = datetime.datetime.now(tz=pytz.utc)
        date = date.astimezone(pytz.timezone('US/Pacific'))
        date_format = date.strftime(date_format)
        return f"{date_format} - {test_run}"

    def add_default_test_run_entry_to_plan(self, test_run_name, plan_name, case_ids=None):
        """ Creates a test run entry with some standard defaults to a test plan

        Defaults:
        test_run_entry = {
            "suite_id": suite_id,
            "name": "{test_run_name} - {timestamp}".format(
                test_run_name=test_run_name,
                timestamp=get_timestamp()),
            "assignedto_id": None,
            "include_all": True,
            "config_ids": [],
            "runs": [
                {
                    "include_all": True,
                    "case_ids": [],
                    "config_ids": []
                }
            ]
        }

        Args:
            test_run_name (string): name of the test plan entry to be created
            plan_name (string): name of the test plan
            case_ids (list): Specifug testCase Id's with which new test run will be created.

        Returns:
            dict: test plan entry
        """

        if case_ids:
            include_all = False
        else:
            include_all = True
        # This condition mandates testcase list not to be empty if include_all is False
        if not include_all and not case_ids:
            return False
        plan = self._get_plan_by_name(plan_name=plan_name)
        if plan is None:
            raise APIError("testrail plan '%s' not found" % plan_name)
        plan_id = plan["id"]

        # Format the testrun name with Time stamp.
        test_run_name = self.format_testrun(test_run_name)
        suite_id = self.suite_id

        test_run_entry = {
            "suite_id": suite_id,
            "name": "{test_run_name}".format(
                test_run_name=test_run_name,
                timestamp=get_timestamp()),
            "assignedto_id": None,
            "include_all": include_all,
            "config_ids": [],
            "case_ids": case_ids,
            "runs": [
                {
                    "include_all": False,
                    "case_ids": case_ids,
                    "config_ids": []
                }
            ]
        }

        return self._add_plan_entry(plan_id, test_run_entry)

    def update_test_run(self, test_run_name, plan_name, case_ids=None):
        """ Updates the existing test run with new set of testcases

        Args:
            test_run (str): test run name
            plan_name (str): test plan name

        """

        # Look for tescase entru already present in the test-run if so skip those

        test_run_id = self.get_run_id(plan_name, test_run_name)

        plan = self._get_plan_by_name(plan_name)
        plan_detail = self._get_plan(plan['id'])
        for elem in plan_detail['entries']:
            if test_run_name in elem['name']:
                entry_id = elem['runs'][0]['entry_id']
                break
        else:
            return False

        case_ids = self.check_test_id_duplicate(case_ids, test_run_id)
        if not case_ids:
            return False

        existing_tests = self.get_cases_in_run(test_run_id)
        for elem in existing_tests:
            case_ids.append(elem['case_id'])

        test_run_entry = {
            "include_all": False,
            "case_ids": case_ids
        }
        url = f"update_plan_entry/{plan['id']}/{entry_id}"
        return self.send_post(url, test_run_entry)

    def check_test_id_duplicate(self, test_list, run_id):
        """ Look for testcase present in the testrun and remove duplicate testcases

        Args:
            test_list (str): List of testcases to be validated
            run_id (object): test run id

        Returns:
            (list): Valid testcases (unique one)
        """

        url = f"get_tests/{run_id}"
        test_case_list = self.send_get(url)

        new_list = []
        for elem in test_case_list:
            new_list.append(elem['case_id'])

        new_list = set(test_list) - set(new_list)

        return list(new_list)

    def get_run_id(self, plan_name, run_name):
        """ Returns an existing test run id

        Args:
            plan_name (str): test plan name
            run_name (str): test run name

        Returns:
            int: test run id
        """

        plan = self._get_plan_by_name(plan_name)
        complete_plan = self._get_plan(plan["id"])
        for each in complete_plan["entries"]:
            # Added this to look for sub-string, Reason: we are creating test-run prepending with
            # time stamp and also wanted to remove duplicate testrun entries
            if run_name in each["runs"][0]["name"]:
                return each["runs"][0]["id"]

    def add_results(self, run_id, data):
        """ Add results for a test run/entry

        Args:
            run_id (string): test run or entry id
            data (dict): post body data

        Returns:
            dict: result
        """

        url = f"add_results/{run_id}"
        return self.send_post(url, data)

    def __check_case_in_run(self, run_id, case_id):
        """ Checks if the case is associated to the run

        Args:
            run_id (str): id the the run
            case_id (int): Case id (not the id that is created once associated to a run)

        Returns:
            id: test case if the case is present in the run
            bool: False if absent
        """
        if run_id not in self.cases_in_run:
            tc_list = self.get_cases_in_run(run_id=run_id)
        else:
            tc_list = self.cases_in_run[run_id]
        for test_case in tc_list:
            if test_case.get('case_id', None) == case_id:
                return test_case.get('id', None)
        return False

    def update_test_result(self, run_id, case_id, report):
        """ Update the test result of a test case associated to a run

        Args:
            run_id (str): Id of the test run
            case_id (id): Case id (not the id that is created once associated to a run)
            report (obj): instance of pytest TestReport

        Returns:
            bool: False if unsuccessful in updating
        """

        test_id = self.__check_case_in_run(run_id, case_id)

        if not test_id:
            return False

        data = {"results": [{
            "test_id": test_id,
            "status_id": self.result_map.get(report.outcome, 5),
            "elapsed": time.strftime('%Hh %Mm %Ss', time.gmtime(math.ceil(report.duration))),
            "comment": report.longreprtext
        }]
        }
        return self.send_post(
            uri='add_results/{run_id}'.format(run_id=run_id),
            data=data)

    def _get_runs(self, project_id=None):
        """ Returns a list of test runs for a project

        Args:
            project_id (int): project id
        Returns:
            list: list  of test runs

        """

        if not project_id:
            project_id = self.project_id
        url = f"get_runs/{project_id}"
        return self.send_get(url)

    def _get_run(self, run_id):
        """ Returns an existing test run

        Args:
            run_id (int): plan id

        Returns:
            dict: test run entry
        """

        url = f"get_run/{run_id}"
        return self.send_get(url)

    def _get_results_for_run(self, run_id):
        """ Returns a list of test results for a test run.

        Args:
            run_id (int): The ID of the test run

        Returns:
            list: list of test results
        """

        url = f"get_results_for_run/{run_id}"
        return self.send_get(url)

    def _get_testrun_by_name(self, project_name, plan_name, testrun_name):
        """ Searches for an exact match of the testrun name

        Args:
            project_name (string): name of the project
            testrun_name (str): testrun name

        Returns:
            dict: testrun
            None: if there is no match
        """

        project = self.__get_project_by_name(project_name)
        plan = self._get_plan_by_name(plan_name, project['id'])
        plan = self._get_plan(plan['id'])
        for entry in plan['entries']:
            if entry['name'] == testrun_name:
                for testrun in entry['runs']:
                    if testrun['name'] == testrun_name:
                        return testrun
        return None

    def get_testrun_results(self, project_name, plan_name, testrun_name):
        """ Gets testrun results

        Args:
            project_name (str): project name
            plane_name (str): plane name
            testrun_name (str): testrun name

        Returns:
            list: list of test results
        """

        testrun = self._get_testrun_by_name(project_name, plan_name, testrun_name)
        if testrun is not None:
            return self._get_results_for_run(testrun["id"])
        return None


class APIError(Exception):
    pass
