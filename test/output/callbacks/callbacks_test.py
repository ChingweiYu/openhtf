# Copyright 2016 Google Inc. All Rights Reserved.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Unit tests for the openhtf.output.callbacks module.

This test currently only provides line coverage, checking that the Python code
is sane. It might be worth expanding the tests to also check for things we
actually care for.
"""

import io
import sys
import unittest

import openhtf as htf
from openhtf import util
from examples import all_the_things
from openhtf.output.callbacks import console_summary
from openhtf.output.callbacks import json_factory
from openhtf.output.callbacks import mfg_inspector
from openhtf.output.proto import test_runs_pb2
from openhtf.util import test


class TestOutput(test.TestCase):

  @classmethod
  def setUpClass(cls):
    # Create input record.
    result = util.NonLocalResult()
    def _save_result(test_record):
      result.result = test_record
    cls._test = htf.Test(
        all_the_things.hello_world,
        all_the_things.dimensions,
        all_the_things.attachments,
    )
    cls._test.add_output_callbacks(_save_result)
    cls._test.make_uid = lambda: 'UNITTEST:MOCK:UID'

  @test.patch_plugs(user_mock='openhtf.plugs.user_input.UserInput')
  def test_json(self, user_mock):
    user_mock.prompt.return_value = 'SomeWidget'
    record = yield self._test
    if sys.version_info[0] < 3:
      json_output = io.BytesIO()
    else:
      json_output = io.StringIO()
    json_factory.OutputToJSON(
        json_output, sort_keys=True, indent=2)(record)

  @test.patch_plugs(user_mock='openhtf.plugs.user_input.UserInput')
  def test_test_run_from_test_record(self, user_mock):
    user_mock.prompt.return_value = 'SomeWidget'
    record = yield self._test

    test_run_proto = mfg_inspector._test_run_from_test_record(record)

    # Assert test status
    self.assertEqual(test_runs_pb2.FAIL, test_run_proto.test_status)

    # Verify all expected phases included.
    expected_phase_names = [
        'trigger_phase', 'hello_world', 'dimensions', 'attachments'
    ]
    actual_phase_names = [phase.name for phase in test_run_proto.phases]
    self.assertEqual(expected_phase_names, actual_phase_names)

    # Spot check a measurement (widget_size)
    measurement_name = 'widget_size'
    for parameter in test_run_proto.test_parameters:
      if parameter.name == measurement_name:
        self.assertEqual(3.0, parameter.numeric_value)

    # Spot check an attachment (example_attachment.txt)
    attachment_name = 'example_attachment.txt'
    for parameter in test_run_proto.info_parameters:
      if parameter.name == attachment_name:
        self.assertEqual(
          b'This is a text file attachment.\n',
          parameter.value_binary,
        )


  @test.patch_plugs(user_mock='openhtf.plugs.user_input.UserInput')
  def test_testrun(self, user_mock):
    user_mock.prompt.return_value = 'SomeWidget'
    record = yield self._test
    testrun_output = io.BytesIO()
    mfg_inspector.OutputToTestRunProto(testrun_output)(record)


class TestConsoleSummary(test.TestCase):

  def test_outcome_colors(self):
    """Ensure there is an output color for each outcome."""
    instance = console_summary.ConsoleSummary()
    for outcome in htf.test_record.Outcome:
      self.assertIn(outcome, instance.color_table)
