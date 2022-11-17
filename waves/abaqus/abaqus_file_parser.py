#! /usr/bin/env python

"""Abaqus File Parser
Parse various file types created via Abaqus

.. moduleauthor:: Prabhu S. Khalsa <pkhalsa@lanl.gov>
"""

import re
import yaml
import os
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime

import xarray
import numpy
import h5py

from waves.abaqus import _settings


class AbaqusFileParser(ABC):
    """Parent class for parsing Abaqus files.

    :param str input_file: name of file to be parsed

    :Attributes:

        - **input_file**: *str* File Name given as input
        - **output_file**: *str* Default file name for output file
        - **parsed**: *dict* Dictionary for holding parsed data
      """

    def __init__(self, input_file, verbose=False, *args, **kwargs):
        self.input_file = input_file
        super().__init__()
        self.parsed = dict()
        if input_file:
            self.output_file = f"{input_file}{_settings._default_parsed_extension}"
        if verbose:
            self.verbose = True
        else:
            self.verbose = False
        self.parse(*args, **kwargs)
        return

    @abstractmethod
    def parse(self):
        pass  # pragma: no cover

    # Anybody who wishes to create a class that inherits from this class,
    # must create a method called parse

    def write_yaml(self, output_file=None):
        """Write the data in yaml format to the output file

        :param str output_file: Name of output file to write yaml (default: <input file>.parsed)
        """
        if output_file:
            self.output_file = output_file
        if Path(self.output_file).suffix != _settings._default_yaml_extension:
            self.output_file = str(Path(self.output_file).with_suffix(_settings._default_yaml_extension))
            self.print_warning(f'Changing suffix of output file to {_settings._default_yaml_extension}')
        try:
            f = open(self.output_file, 'w')
        except EnvironmentError as e:
            self.print_critical(f"Couldn't write file {self.output_file}: {e}")
            return
        yaml.safe_dump(self.parsed, f)

    def print_warning(self, message):
        """Print a warning message

        :param str message: string with a message to print
        """
        if self.verbose:
            print(message)

    def print_error(self, message):
        """Print an error message

        :param str message: string with a message to print
        """
        if self.verbose:
            print(message)

    def print_critical(self, message):
        """Print a critical message and exit with an exception

        :param str message: string with a message to print
        """
        print(message)
        raise SystemExit(-1)


class MsgFileParser(AbaqusFileParser):
    """Class for parsing Abaqus msg files.
    """

    def parse(self, input_file=None):
        """Parse the file and store the results in the self.parsed dictionary.

        :param str input_file: Name of msg file to parse
        :return: None
        """
        if not input_file:
            input_file = self.input_file
        try:
            f = open(input_file, 'r')
        except EnvironmentError as e:
            self.print_critical(f"Couldn't read file {input_file}: {e}")
            return

        self.parsed["steps"] = dict()
        step_number = 0
        increment_number = 0
        attempt_number = 0
        iteration_number = 0
        number_of_equations = 0
        number_of_floating_pt_operations = 0
        elapsed_user_time = 0
        elapsed_system_time = 0
        elapsed_total_cpu_time = 0
        elapsed_wallclock_time = 0
        severe_discontinuities = 0
        points_changed = dict()
        data_type = ""
        contact_pair = list()

        line = f.readline()
        while line:
            line = line.strip()
            date_match = re.match(r'^.*Date\s+(\d\d-.*-\d\d\d\d)\s+Time\s+(\d\d:\d\d:\d\d)', line, re.IGNORECASE)
            if date_match:
                if "date" not in self.parsed:
                    self.parsed["date"] = date_match.group(1)
                    self.parsed["time"] = date_match.group(2)
            step_match = re.match(r'^\s*STEP\s+(\d+)\s+INCREMENT\s+(\d+)\s+STEP TIME\s+([\d.eE\-+]+)', line)
            if step_match:
                step_number = int(step_match.group(1))
                increment_number = int(step_match.group(2))
                try:
                    step_time = float(step_match.group(3))
                except ValueError as e:
                    self.print_error("Couldn't convert step time to float. Storing as string:{}".format(e))
                    step_time = step_match.group(3)
                if step_number not in self.parsed["steps"]:
                    self.parsed["steps"][step_number] = dict()
                    self.parsed["steps"][step_number]["increments"] = dict()
                    self.parsed["steps"][step_number]["step_time"] = step_time
                if increment_number not in self.parsed["steps"][step_number]["increments"]:
                    self.parsed["steps"][step_number]["increments"][increment_number] = dict()
                    self.parsed["steps"][step_number]["increments"][increment_number]["attempts"] = dict()
            increment_match = re.match(
                r'^\s*INCREMENT\s+(\d+)\s+STARTS.\s+ATTEMPT NUMBER\s+(\d+),\s+TIME INCREMENT\s+([\d.eE\-+]+)', line)
            if increment_match:
                increment_number = int(increment_match.group(1))
                attempt_number = int(increment_match.group(2))
                iteration_number = 0
                try:
                    time_increment = float(increment_match.group(3))
                except ValueError as e:
                    self.print_error("Couldn't convert time increment to float. Storing as string:{}".format(e))
                    time_increment = increment_match.group(3)
                if increment_number not in self.parsed["steps"][step_number]["increments"]:
                    self.parsed["steps"][step_number]["increments"][increment_number] = dict()
                    self.parsed["steps"][step_number]["increments"][increment_number]["attempts"] = dict()
                if "attempt times" not in self.parsed["steps"][step_number]["increments"][increment_number]:
                    self.parsed["steps"][step_number]["increments"][increment_number]["attempt times"] = dict()
                if attempt_number not in self.parsed["steps"][step_number]["increments"][increment_number]["attempts"]:
                    self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number] \
                        = dict()
                self.parsed["steps"][step_number]["increments"][increment_number]["attempt times"][attempt_number] = \
                    time_increment
            pair_match = re.match(r'^\s*CONTACT PAIR\s+\((.*)\).*', line)
            if pair_match:
                contact_pair = pair_match.group(1).split(',')
            note_match = re.match(r'^\s*\*\*\*NOTE:(.*UNLIKELY.*)', line)
            if note_match:
                if "unlikely" not in self.parsed["steps"][step_number]["increments"][increment_number][
                    "attempts"][attempt_number]:
                    self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                        "unlikely"] = dict()
                iteration_number = len(self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][
                                           attempt_number]["unlikely"]) + 1
                self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                    "unlikely"][iteration_number] = dict()
                self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                    "unlikely"][iteration_number]["note"] = note_match.group(1)
                self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                    "unlikely"][iteration_number]["contact pair"] = contact_pair
            numbers_match = re.match(
                r'^\s*NUMBER OF EQUATIONS =\s+(\d+)\s+NUMBER OF (.*) =\s+([\d.eE\-+]+)', line)
            if numbers_match:
                number_of_equations = int(numbers_match.group(1))
                if "FLOATING PT" in numbers_match.group(2):
                    try:
                        number_of_floating_pt_operations = float(numbers_match.group(3))
                    except ValueError as e:
                        self.print_error("Couldn't convert number of floating point operations to float. "
                                     "Storing as string:{}".format(e))
                        number_of_floating_pt_operations = numbers_match.group(3)
            # Found situations where the following pattern was on its own line
            floating_point_match = re.match(r'^\s*NUMBER OF FLOATING PT. OPERATIONS =\s+([\d.eE\-+]+)', line)
            if floating_point_match:
                try:
                    number_of_floating_pt_operations = float(floating_point_match.group(1))
                except ValueError as e:
                    self.print_error("Couldn't convert number of floating point operations to float. "
                                 "Storing as string:{}".format(e))
                    number_of_floating_pt_operations = floating_point_match.group(1)
            if "ELAPSED USER TIME (SEC)" in line:
                try:
                    elapsed_user_time = float(line.split('=')[1].strip())
                except ValueError as e:
                    self.print_error("Couldn't convert elapsed user time to float. Storing as string:{}".format(e))
                    elapsed_user_time = line.split('=')[1].strip()
            if "ELAPSED SYSTEM TIME (SEC)" in line:
                try:
                    elapsed_system_time = float(line.split('=')[1].strip())
                except ValueError as e:
                    self.print_error("Couldn't convert elapsed system time to float. Storing as string:{}".format(e))
                    elapsed_system_time = line.split('=')[1].strip()
            if "ELAPSED TOTAL CPU TIME (SEC)" in line:
                try:
                    elapsed_total_cpu_time = float(line.split('=')[1].strip())
                except ValueError as e:
                    self.print_error("Couldn't convert elapsed total cpu time to float. Storing as string:{}".format(e))
                    elapsed_total_cpu_time = line.split('=')[1].strip()
            if "ELAPSED WALLCLOCK TIME (SEC)" in line:
                try:
                    elapsed_wallclock_time = float(line.split('=')[1].strip())
                except ValueError as e:
                    self.print_error("Couldn't convert elapsed wallclock time to float. Storing as string:{}".format(e))
                    elapsed_wallclock_time = line.split('=')[1].strip()
            severe_match = re.match(r'^\s*(\d+)\s+SEVERE DISCONTINUITIES OCCURRED DURING THIS ITERATION.', line)
            if severe_match:
                severe_discontinuities = int(severe_match.group(1))
            points_match = re.match(r'^\s*(\d+)\s+POINTS CHANGED FROM (.*)', line)
            if points_match:
                points_changed[points_match.group(2).lower()] = int(points_match.group(1))
            iterations_match = re.match(r'^\s*CONVERGENCE CHECKS FOR (.*) ITERATION\s+(\d+).*', line)
            if iterations_match:
                iteration_type = iterations_match.group(1).lower()
                iteration_number = int(iterations_match.group(2))
                if iteration_type not in self.parsed["steps"][step_number]["increments"][increment_number][
                    "attempts"][attempt_number]:
                    self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                        iteration_type] = dict()
                self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][
                    attempt_number][iteration_type][iteration_number] = dict()
                self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                    iteration_type][iteration_number]["number of equations"] = number_of_equations
                self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                    iteration_type][iteration_number]["number of floating point operations"] = \
                    number_of_floating_pt_operations
                self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                    iteration_type][iteration_number]["elapsed user time"] = elapsed_user_time
                self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                    iteration_type][iteration_number]["elapsed system time"] = elapsed_system_time
                self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                    iteration_type][iteration_number]["elapsed total cpu time"] = elapsed_total_cpu_time
                self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                    iteration_type][iteration_number]["elapsed wallclock time"] = elapsed_wallclock_time
                if severe_discontinuities != 0:
                    self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                        iteration_type][iteration_number]["severe discontinuities occurred"] = severe_discontinuities
                if points_changed:
                    self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                        iteration_type][iteration_number]["points changed"] = points_changed
                severe_discontinuities = 0  # resetting this value
                points_changed = dict()  # resetting the dictionary for the next iteration
            max_pen_match = re.match(r'^\s*MAX. PENETRATION ERROR ([\d.eE\-+]+) AT NODE (.*) OF CONTACT PAIR', line)
            if max_pen_match:
                self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                    iteration_type][iteration_number]["max penetration error"] = dict()
                self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                    iteration_type][iteration_number]["max penetration error"]["value"] = float(max_pen_match.group(1))
                self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                    iteration_type][iteration_number]["max penetration error"]["node"] = max_pen_match.group(2)
                # get the next line
                line = f.readline()
                line = line.strip()
                if line[0] == '(' and line[-1] == ')':
                    self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                        iteration_type][iteration_number]["max penetration error"]["contact pair"] = \
                        line[1:-1].split(',')
                else:
                    line = f.readline()
                    continue
            max_contact_match = re.match(r'^\s*MAX. CONTACT FORCE ERROR ([\d.eE\-+]+)'
                                         r' AT NODE (.*) OF CONTACT PAIR', line)
            if max_contact_match:
                self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                    iteration_type][iteration_number]["max contact force error"] = dict()
                self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                    iteration_type][iteration_number]["max contact force error"]["value"] = \
                    float(max_contact_match.group(1))
                self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                    iteration_type][iteration_number]["max contact force error"]["node"] = max_contact_match.group(2)
                # get the next line
                line = f.readline()
                line = line.strip()
                if line[0] == '(' and line[-1] == ')':
                    self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                        iteration_type][iteration_number]["max contact force error"]["contact pair"] = \
                        line[1:-1].split(',')
                    line = f.readline()
                    line = line.strip()
                    self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                        iteration_type][iteration_number]["max contact force error"]["message"] = line

            avg_match = re.match(r'^\s*AVERAGE (.*)\s+([\d.eE\-+]+)\s+TIME AVG. (.*)\s+([\d.eE\-+]+)', line)
            if avg_match:
                data_type = avg_match.group(1).lower().strip().strip('.')
                if "data blocks" not in self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][
                    attempt_number][iteration_type][iteration_number]:
                    self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                        iteration_type][iteration_number]["data blocks"] = dict()
                self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                    iteration_type][iteration_number]["data blocks"][data_type] = dict()
                try:
                    self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                        iteration_type][iteration_number]["data blocks"][data_type]["average"] = \
                        float(avg_match.group(2))
                except ValueError as e:
                    self.print_error("Couldn't convert average " + data_type +
                                 " to float. Storing as string:{}".format(e))
                    self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                        iteration_type][iteration_number]["data blocks"][data_type]["average"] = avg_match.group(2)
                try:
                    self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                        iteration_type][iteration_number]["data blocks"][data_type]["time average"] = \
                        float(avg_match.group(4))
                except ValueError as e:
                    self.print_error("Couldn't convert time average " + data_type +
                                 "to float. Storing as string:{}".format(e))
                    self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                        iteration_type][iteration_number]["data blocks"][data_type]["time average"] = avg_match.group(4)

            largest_residual_match = re.match(r'^\s*LARGEST RESIDUAL (.*)\s+([\d.eE\-+]+)\s+'
                                              r'AT NODE\s+(\d+)\s+DOF\s+(\d+)', line)
            if largest_residual_match:
                residual_type = "largest residual " + largest_residual_match.group(1).lower().strip().strip('.')
                self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                    iteration_type][iteration_number]["data blocks"][data_type][residual_type] = dict()
                try:
                    self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                        iteration_type][iteration_number]["data blocks"][data_type][residual_type]["value"] = \
                        float(largest_residual_match.group(2))
                except ValueError as e:
                    self.print_error("Couldn't convert largest residual " + residual_type +
                                 "to float. Storing as string:{}".format(e))
                    self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                        iteration_type][iteration_number]["data blocks"][data_type][residual_type]["value"] = \
                        largest_residual_match.group(2)
                self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                    iteration_type][iteration_number]["data blocks"][data_type][residual_type]["at node"] = \
                    int(largest_residual_match.group(3))
                self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                    iteration_type][iteration_number]["data blocks"][data_type][residual_type]["degree of freedom"] = \
                    int(largest_residual_match.group(4))
                line = f.readline()
                line = line.strip()
                if "INSTANCE" in line:
                    self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                        iteration_type][iteration_number]["data blocks"][data_type][residual_type]["instance"] = \
                        line.split(':')[1].strip()
                else:
                    line = f.readline()
                    continue

            largest_increment_match = re.match(r'^\s*LARGEST INCREMENT OF (.*)\s+([\d.eE\-+]+)\s+AT NODE\s+(\d+)\s+'
                                               r'DOF\s+(\d+)', line)
            if largest_increment_match:
                largest_increment_type = largest_increment_match.group(1).lower().strip().strip('.')
                if largest_increment_type == "disp":
                    largest_increment_type = "displacement"
                if largest_increment_type == "temp":
                    largest_increment_type = "temperature"
                largest_increment_type = "largest increment of " + largest_increment_type
                self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                    iteration_type][iteration_number]["data blocks"][data_type][largest_increment_type] = dict()
                try:
                    self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                        iteration_type][iteration_number]["data blocks"][data_type][largest_increment_type]["value"] = \
                        float(largest_increment_match.group(2))
                except ValueError as e:
                    self.print_error("Couldn't convert largest increment of " + largest_increment_type + " to float."
                                                                                                     " Storing as string:{}".format(
                        e))
                    self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                        iteration_type][iteration_number]["data blocks"][data_type][largest_increment_type]["value"] = \
                        largest_increment_match.group(2)
                self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                    iteration_type][iteration_number]["data blocks"][data_type][largest_increment_type]["at node"] = \
                    int(largest_increment_match.group(3))
                self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                    iteration_type][iteration_number]["data blocks"][data_type][largest_increment_type][
                    "degree of freedom"] = int(largest_increment_match.group(4))
                line = f.readline()
                line = line.strip()
                if "INSTANCE" in line:
                    self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                        iteration_type][iteration_number]["data blocks"][data_type][largest_increment_type][
                        "instance"] = line.split(':')[1].strip()
                else:
                    line = f.readline()
                    continue

            largest_correction_match = re.match(r'^\s*LARGEST CORRECTION TO (.*)\s+([\d.eE\-+]+)\s+'
                                                r'AT NODE\s+(\d+)\s+DOF\s+(\d+)', line)
            if largest_correction_match:
                correction_type = largest_correction_match.group(1).lower().strip().strip('.')
                if correction_type == "disp":
                    correction_type = "displacement"
                if correction_type == "temp":
                    correction_type = "temperature"
                correction_type = "largest correction to " + correction_type
                self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                    iteration_type][iteration_number]["data blocks"][data_type][correction_type] = dict()
                try:
                    self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                        iteration_type][iteration_number]["data blocks"][data_type][correction_type]["value"] = \
                        float(largest_correction_match.group(2))
                except ValueError as e:
                    self.print_error("Couldn't convert largest correction to " + correction_type + " to float."
                                                                                               " Storing as string:{}".format(
                        e))
                    self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                        iteration_type][iteration_number]["data blocks"][data_type][correction_type]["value"] = \
                        largest_correction_match.group(2)
                self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                    iteration_type][iteration_number]["data blocks"][data_type][correction_type]["at node"] = \
                    int(largest_correction_match.group(3))
                self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                    iteration_type][iteration_number]["data blocks"][data_type][correction_type][
                    "degree of freedom"] = int(largest_correction_match.group(4))
                line = f.readline()
                line = line.strip()
                if "INSTANCE" in line:
                    self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                        iteration_type][iteration_number]["data blocks"][data_type][correction_type]["instance"] = \
                        line.split(':')[1].strip()
                    line = f.readline()
                    message = line.strip()
                    while line != "":
                        line = f.readline()
                        line = line.strip()
                        message = message + " " + line
                    self.parsed["steps"][step_number]["increments"][increment_number]["attempts"][attempt_number][
                        iteration_type][iteration_number]["data blocks"][data_type]["message"] = message
                else:
                    line = f.readline()
                    continue

            if "JOB TIME SUMMARY" in line:
                self.parsed["job summary"] = dict()
                line = f.readline()
                line = line.strip()
                while "=" in line:
                    time_type, time_value = line.split('=')
                    time_type = time_type.strip().lower()
                    if time_type[-6:] == ' (sec)':
                        time_type = time_type[:-6]
                    try:
                        self.parsed["job summary"][time_type] = float(time_value.strip())
                    except ValueError as e:
                        self.print_error("Couldn't convert " + time_type + " to float. Storing as string:{}".format(e))
                        self.parsed["job summary"][time_type] = time_value.strip()
                    line = f.readline()
                    line = line.strip()

            line = f.readline()
        f.close()

    def write_all(self, output_file=None):
        """Write all the data in the dictionary

        :param str output_file: Name of output file to write data (default: <input file>.parsed)
        :return: None
        """
        if not output_file:
            output_file = self.output_file
        try:
            f = open(output_file, 'w')
        except EnvironmentError as e:
            self.print_error(f"Couldn't write file {self.output_file}: {e}")
            return
        f.write("Filename: " + self.input_file + "\n")
        if "date" in self.parsed and "time" in self.parsed:
            f.write("Date: " + self.parsed["date"] + "    ")
            f.write("Time: " + self.parsed["time"] + "\n\n")
        for step in self.parsed["steps"]:
            f.write("Step " + str(step) + " (step time " + str(self.parsed["steps"][step]["step_time"]) + "): \n")
            for increment in self.parsed["steps"][step]["increments"]:
                f.write("  Increment " + str(increment) + ": \n")
                for attempt in self.parsed["steps"][step]["increments"][increment]["attempts"]:
                    f.write("    Attempt " + str(attempt) + " (time increment " + str(
                        self.parsed["steps"][step]["increments"][increment]["attempt times"][attempt]) + "): \n")
                    for iteration_type in self.parsed["steps"][step]["increments"][increment]["attempts"][attempt]:
                        for iteration in self.parsed["steps"][step]["increments"][increment]["attempts"][attempt][
                            iteration_type]:
                            if iteration_type == "unlikely":
                                f.write("        Note: " + str(self.parsed["steps"][step]["increments"][increment][
                                                                   "attempts"][attempt][iteration_type][iteration][
                                                                   "note"]) + "\n")
                                f.write("        Contact Pair: " + str(self.parsed["steps"][step]["increments"][
                                                                           increment]["attempts"][attempt][
                                                                           iteration_type][iteration][
                                                                           "contact pair"]) + "\n")
                                continue
                            f.write("      " + iteration_type + " iteration " + str(iteration) + "\n")
                            f.write("        Elapsed User Time (seconds): " + str(
                                self.parsed["steps"][step]["increments"][increment]["attempts"][attempt][
                                    iteration_type][iteration]["elapsed user time"]) + "\n")
                            f.write("        Elapsed System Time (seconds): " + str(
                                self.parsed["steps"][step]["increments"][increment]["attempts"][attempt][
                                    iteration_type][iteration]["elapsed system time"]) + "\n")
                            f.write("        Elapsed Total CPU Time (seconds): " + str(
                                self.parsed["steps"][step]["increments"][increment]["attempts"][attempt][
                                    iteration_type][iteration]["elapsed total cpu time"]) + "\n")
                            f.write("        Elapsed Wallclock Time (seconds): " + str(
                                self.parsed["steps"][step]["increments"][increment]["attempts"][attempt][
                                    iteration_type][iteration]["elapsed wallclock time"]) + "\n")
                            if "severe discontinuities occurred" in self.parsed["steps"][step]["increments"][
                                increment]["attempts"][attempt][iteration_type][iteration]:
                                f.write("        Severe Discontinuities During this Iteration: " + str(
                                    self.parsed["steps"][step]["increments"][increment]["attempts"][attempt][
                                        iteration_type][iteration]["severe discontinuities occurred"]) + "\n")
                                for points_changed in self.parsed["steps"][step]["increments"][increment]["attempts"][
                                    attempt][iteration_type][iteration]["points changed"]:
                                    f.write("        Points Changed from " + points_changed + " " + str(
                                        self.parsed["steps"][step]["increments"][increment]["attempts"][attempt][
                                            iteration_type][iteration]["points changed"][points_changed]) + "\n")

                            if "max penetration error" in self.parsed["steps"][step]["increments"][increment][
                                "attempts"][attempt][iteration_type][iteration]:
                                f.write("        Max Penetration Error: " + str(
                                    self.parsed["steps"][step]["increments"][increment]["attempts"][attempt][
                                        iteration_type][iteration]["max penetration error"]["value"]) + "\n")
                                f.write("          Node: " + str(self.parsed["steps"][step]["increments"][increment][
                                                                     "attempts"][attempt][iteration_type][iteration][
                                                                     "max penetration error"]["node"]) + "\n")
                                f.write("          Contact Pair: (" + self.parsed["steps"][step]["increments"][
                                    increment]["attempts"][attempt][iteration_type][iteration]["max penetration error"][
                                    "contact pair"][0] + ", " + self.parsed["steps"][step]["increments"][increment][
                                            "attempts"][attempt][iteration_type][iteration]["max penetration error"][
                                            "contact pair"][1] + ")\n")

                            if "max contact force error" in self.parsed["steps"][step]["increments"][increment][
                                "attempts"][attempt][iteration_type][iteration]:
                                f.write("        Max Contact Force Error: " + str(
                                    self.parsed["steps"][step]["increments"][increment]["attempts"][attempt][
                                        iteration_type][iteration]["max contact force error"]["value"]) + "\n")
                                f.write("          Node: " + str(self.parsed["steps"][step]["increments"][increment][
                                                                     "attempts"][attempt][iteration_type][iteration][
                                                                     "max contact force error"]["node"]) + "\n")
                                f.write("          Contact Pair: (" + self.parsed["steps"][step]["increments"][
                                    increment]["attempts"][attempt][iteration_type][iteration][
                                    "max contact force error"]["contact pair"][0] + ", " + self.parsed["steps"][step][
                                            "increments"][increment]["attempts"][attempt][iteration_type][iteration][
                                            "max contact force error"]["contact pair"][1] + ")\n")
                                f.write("          " + self.parsed["steps"][step]["increments"][increment]["attempts"][
                                    attempt][iteration_type][iteration]["max contact force error"]["message"] + "\n")

                            f.write("        Number of Equations: " + str(
                                self.parsed["steps"][step]["increments"][increment]["attempts"][attempt][
                                    iteration_type][iteration]["number of equations"]) + "    ")
                            f.write("        Number of Floating Point Operations: " + str(
                                self.parsed["steps"][step]["increments"][increment]["attempts"][attempt][
                                    iteration_type][iteration]["number of floating point operations"]) + "\n")

                            for data_type in self.parsed["steps"][step]["increments"][increment]["attempts"][
                                attempt][iteration_type][iteration]["data blocks"]:
                                f.write("        Average " + data_type.title() + ": " + str(
                                    self.parsed["steps"][step]["increments"][increment]["attempts"][attempt][
                                        iteration_type][iteration]["data blocks"][data_type]["average"]) + "    ")
                                f.write("        Time Average " + data_type.title() + ": " + str(
                                    self.parsed["steps"][step]["increments"][increment]["attempts"][attempt][
                                        iteration_type][iteration]["data blocks"][data_type]["time average"]) + "\n")
                                for key in self.parsed["steps"][step]["increments"][increment]["attempts"][attempt][
                                    iteration_type][iteration]["data blocks"][data_type]:
                                    if key == "message" or key == "average" or key == "time average":
                                        continue
                                    f.write("        " + key.title() + ": " + str(
                                        self.parsed["steps"][step]["increments"][increment]["attempts"][attempt][
                                            iteration_type][iteration]["data blocks"][data_type][key]["value"]) + "\n")
                                    f.write("          At Node: " + str(
                                        self.parsed["steps"][step]["increments"][increment]["attempts"][attempt][
                                            iteration_type][iteration]["data blocks"][data_type][key]["at node"])
                                            + "\n")
                                    f.write("          Degree of Freedom: " + str(
                                        self.parsed["steps"][step]["increments"][increment]["attempts"][attempt][
                                            iteration_type][iteration]["data blocks"][data_type][key][
                                            "degree of freedom"]) + "\n")
                                    f.write("          Instance: " + str(
                                        self.parsed["steps"][step]["increments"][increment]["attempts"][attempt][
                                            iteration_type][iteration]["data blocks"][data_type][key]["instance"])
                                            + "\n")
                                f.write("        " + str(self.parsed["steps"][step]["increments"][increment][
                                                             "attempts"][attempt][iteration_type][iteration][
                                                             "data blocks"][data_type]["message"]) + "\n")

        f.write("\nJob Summary:\n")
        for time_type in self.parsed["job summary"]:
            f.write("  " + time_type + " in seconds: " + str(self.parsed["job summary"][time_type]) + "\n")

    def write_summary_table(self, output_file=None, sta_file=None):
        """Write a summary of the data in a table

        :param str output_file: Name of output file to write data (default: <input file>.parsed)
        :param str sta_file: Name of sta file to parse for summary data
        :return: None
        """
        if not output_file:
            output_file = self.output_file
        try:
            f = open(output_file, 'w')
        except EnvironmentError as e:
            self.print_error(f"Couldn't write file {self.output_file}: {e}")
            return

        if sta_file:
            sta = StaFileParser(sta_file)
        else:
            sta_file = str(Path(self.input_file).with_suffix('.sta'))
            if os.path.exists(sta_file):
                sta = StaFileParser(sta_file)
            else:
                sta = None

        if sta and sta.parsed:
            f.write("Filename: " + self.input_file + "\n")
            f.write("sta filename: " + sta_file + "\n")
            f.write("Date: " + self.parsed["date"] + "    ")
            f.write("Time: " + self.parsed["time"] + "\n\n")
            f.write("                       Severe\n")
            f.write("                       Discontinuity Equilibrium Total      Total Step     Increment   DOF"
                    "     IF   Contact\n")
            f.write("Step Increment Attempt Iterations    Iterations  Iterations Time  Time/LPF of Time/LPF Monitor"
                    " RIKS Pair\n")

            u_iterations = dict()  # dictionary to keep track of number of unlikely iterations
            for column in sta.parsed["columns"]:
                if "dof monitor" in column:
                    dof_monitor = column['dof monitor']
                else:
                    dof_monitor = ""
                if "if riks" in column:
                    if_riks = column['if riks']
                else:
                    if_riks = ""

                total_time = str(column['total time'])
                if len(total_time) > 7:
                    try:
                        total_time = "{:.2E}".format(column['total time'])
                    except ValueError:  # Can't format as float, just cut the string to length 7
                        total_time = total_time[:7]

                step_time = str(column['step time'])
                if len(step_time) > 7:
                    try:
                        step_time = "{:.2E}".format(column['step time'])
                    except ValueError:
                        step_time = step_time[:7]

                increment_time = str(column['increment of time'])
                if len(increment_time) > 9:
                    try:
                        increment_time = "{:.2E}".format(column['increment of time'])
                    except ValueError:
                        increment_time = increment_time[:9]

                if "U" in column['attempt']:
                    attempt = int(column['attempt'][:-1])  # remove 'U' and get number
                    iteration_key = 's' + str(column['step']) + 'i' + str(column['increment']) + 'a' + str(attempt)
                    if iteration_key in u_iterations:
                        u_iterations[iteration_key] += 1
                    else:
                        u_iterations[iteration_key] = 1
                    contact_pair = str(self.parsed["steps"][column['step']]["increments"][column['increment']][
                                           "attempts"][attempt]["unlikely"][u_iterations[iteration_key]][
                                           "contact pair"])
                else:
                    contact_pair = ""
                f.write('{:5}{:10}{:8}{:14}{:12}{:11}{:9}{:9}{:12}{:8}{:5}{}\n'
                        .format(str(column['step']), str(column['increment']), column['attempt'],
                                str(column['severe discontinuity iterations']), str(column['equilibrium iterations']),
                                str(column['total iterations']), total_time, step_time, increment_time, dof_monitor,
                                if_riks, contact_pair))
        else:  # If there is no sta file, then write a summary from the msg file
            f.write("Filename: " + self.input_file + "\n")
            f.write("Date: " + self.parsed["date"] + "    ")
            f.write("Time: " + self.parsed["time"] + "\n\n")
            f.write("                       Severe\n")
            f.write("                       Discontinuity Equilibrium Total      Step     Increment   Contact\n")
            f.write("Step Increment Attempt Iterations    Iterations  Iterations Time/LPF of Time/LPF Pair\n")
            for step in self.parsed["steps"]:
                step_time = str(self.parsed["steps"][step]["step_time"])
                if len(step_time) > 7:
                    try:
                        step_time = "{:.2E}".format(self.parsed["steps"][step]["step_time"])
                    except ValueError:  # Can't format as float, just cut the string to length 7
                        step_time = step_time[:7]
                for increment in self.parsed["steps"][step]["increments"]:
                    for attempt in self.parsed["steps"][step]["increments"][increment]["attempts"]:
                        attempt_time = str(self.parsed["steps"][step]["increments"][increment]["attempt times"][
                                               attempt])
                        if len(attempt_time) > 9:
                            try:
                                attempt_time = "{:.2E}".format(self.parsed["steps"][step]["increments"][increment][
                                                                   "attempt times"][attempt])
                            except ValueError:
                                attempt_time = attempt_time[:9]
                        sdi_total = 0
                        equilibrium_total = 0
                        print_attempt = str(attempt)
                        contact_pair = ""
                        for iteration_type in self.parsed["steps"][step]["increments"][increment]["attempts"][attempt]:
                            if "severe" in iteration_type:
                                sdi_total = len(self.parsed["steps"][step]["increments"][increment]["attempts"][
                                                    attempt][iteration_type])
                            if "equilibrium" in iteration_type:
                                equilibrium_total = len(self.parsed["steps"][step]["increments"][increment][
                                                            "attempts"][attempt][iteration_type])
                            if "unlikely" in iteration_type:
                                # sdi_total = 1
                                print_attempt += "U"
                            for iteration in self.parsed["steps"][step]["increments"][increment]["attempts"][attempt][
                                iteration_type]:
                                if "unlikely" in iteration_type:
                                    contact_pair = str(self.parsed["steps"][step]["increments"][increment][
                                                           "attempts"][attempt]["unlikely"][iteration]["contact pair"])
                                f.write('{:5}{:10}{:8}{:14}{:12}{:11}{:9}{:12}{}\n'
                                        .format(str(step), str(increment), print_attempt, str(sdi_total),
                                                str(equilibrium_total), str(sdi_total + equilibrium_total), step_time,
                                                attempt_time, contact_pair))


class StaFileParser(AbaqusFileParser):
    """Class for parsing Abaqus sta files.
    """

    def parse(self, input_file=None):
        """Parse the file and store the results in the self.parsed dictionary.

        :param str input_file: Name of sta file to parse
        :return: None
        """
        if not input_file:
            input_file = self.input_file
        try:
            f = open(input_file, 'r')
        except EnvironmentError as e:
            self.print_critical(f"Couldn't read file {input_file}: {e}")
            return

        self.parsed["columns"] = list()
        line = f.readline()
        while line:
            date_match = re.match(r'^.*DATE\s+(\d\d-.*-\d\d\d\d)\s+TIME\s+(\d\d:\d\d:\d\d)', line, re.IGNORECASE)
            if date_match:
                self.parsed["date"] = date_match.group(1)
                self.parsed["time"] = date_match.group(2)
            column_match = re.match(r'^.*(\d+)\s+(\d+)\s+(\d+U*)\s+(\d+)\s+(\d+)\s+(\d+)\s+'
                                    r'([\d.eE\-+]+)\s+([\d.eE\-+]+)\s+([\d.eE\-+]+)\s+(\S*)\s*(\S*)', line)
            if column_match:
                column = dict()
                column['step'] = int(column_match.group(1))
                column['increment'] = int(column_match.group(2))
                column['attempt'] = column_match.group(3)
                column['severe discontinuity iterations'] = int(column_match.group(4))
                column['equilibrium iterations'] = int(column_match.group(5))
                column['total iterations'] = int(column_match.group(6))
                try:
                    column['total time'] = float(column_match.group(7))
                except ValueError as e:
                    self.print_error("Couldn't convert total time to float. Storing as string:{}".format(e))
                    column['total time'] = column_match.group(7)
                try:
                    column['step time'] = float(column_match.group(8))
                except ValueError as e:
                    self.print_error("Couldn't convert step time to float. Storing as string:{}".format(e))
                    column['step time'] = column_match.group(8)
                try:
                    column['increment of time'] = float(column_match.group(9))
                except ValueError as e:
                    self.print_error("Couldn't convert increment time to float. Storing as string:{}".format(e))
                    column['increment of time'] = column_match.group(9)
                if column_match.group(10):
                    column['dof monitor'] = column_match.group(10)
                if column_match.group(11):
                    column['if riks'] = column_match.group(11)
                self.parsed["columns"].append(column)

            line = f.readline()
        f.close


class OdbReportFileParser(AbaqusFileParser):
    """Class for parsing Abaqus odbreport files.
       Expected input includes only files that are in the csv format and which have used the 'blocked' option.

       Results are stored either in a dictionary which mimics the format of the odb file (see Abaqus documentation),
       or stored in a specialized 'extract' format written to an hdf5 file.

       :Format of HDF5 file:

       .. code-block::

           /                 # Top level group required in all hdf5 files
           /<instance name>/ # Groups containing data of each instance found in an odb
               FieldOutputs/      # Group with multiple xarray datasets for each field output
                   <field name>/  # Group with datasets containing field output data for a specified set or surface
                                  # If no set or surface is specified, the <field name> will be 'ALL'
               HistoryOutputs/    # Group with multiple xarray datasets for each history output
                   <region name>/ # Group with datasets containing history output data for specified history region name
                                  # If no history region name is specified, the <region name> will be 'ALL NODES'
               Mesh/              # Group written from an xarray dataset with all mesh information for this instance
           /<instance name>_Assembly/ # Group containing data of assembly instance found in an odb
               Mesh/              # Group written from an xarray dataset with all mesh information for this instance
           /odb/             # Catch all group for data found in the odbreport file not already organized by instance
               info/              # Group with datasets that mostly give odb meta-data like name, path, etc.
               jobData/           # Group with datasets that contain additional odb meta-data
               rootAssembly/      # Group with datasets that match odb file organization per Abaqus documentation
               sectionCategories/ # Group with datasets that match odb file organization per Abaqus documentation
           /xarray/          # Group with a dataset that lists the location of all data written from xarray datasets
               Dataset  # HDF5 Dataset that lists the location within the hdf5 file of all xarray datasets
    """

    def parse(self, format='extract', h5_file=f'extract{_settings._default_h5_extension}', time_stamp=None):
        """Parse the file and store the results in the self.parsed dictionary.
         Can parse csv formatted output with the blocked option from the odbreport command

        :param str format: Format in which to store data can be 'odb' or 'extract'
        :param str h5_file: Name of hdf5 file to store data into when using the extract format
        :param str time_stamp: Time stamp for possibly appending to hdf5 file names
        :return: None
        """
        # To interrogate the odb structure to know what to parse, follow the links and subsequent links at:
        # simulia:8080/EstProdDocs2021/English/DSSIMULIA_Established.htm?show=SIMACAEKERRefMap/simaker-c-odbpyc.htm
        # In the Abaqus documentation under Scripting Reference -> Python commands -> Odb commands -> Odb object
        # At the bottom of this page will list all the members of the odb and each member with a link will have links
        # to their members
        self.format = format
        self.history_extract_format = dict()
        self.field_extract_format = dict()
        input_file = self.input_file
        try:
            f = open(input_file, 'r')
        except EnvironmentError as e:
            self.print_critical(f"Couldn't read file {input_file}: {e}")
            return

        if not time_stamp:
            time_stamp = datetime.now().strftime(_settings._default_timestamp_format)

        self.parsed['odb'] = dict()
        self.parsed['odb']['info'] = dict()
        line = f.readline()
        while not line.startswith("General ODB information") and line != "":
            if line.startswith('ODB Report'):
                if not re.search('csv', line, re.IGNORECASE):
                    self.print_critical(f"ODB report file must be in CSV format")
                    return
            line = f.readline()

        while not line.startswith("Job Data") and line != "" and not line.startswith('---'):
            try:
                key, value = line.split(',', 1)
                self.parsed['odb']['info'][key.strip()] = value.strip()
            except ValueError:  # If there's no comma, then just ignore the line
                pass
            line = f.readline()

        self.parsed['odb']['jobData'] = dict()
        while not line.startswith("Section Categories") and line != "" and not line.startswith('---'):
            try:
                key, value = line.split(',', 1)
                self.parsed['odb']['jobData'][key.strip()] = value.strip()
            except ValueError:  # If there's no comma, then just ignore the line
                pass
            line = f.readline()

        if line.startswith('Section Categories'):
            self.parsed['odb']['sectionCategories'] = dict()
            line = f.readline()
            if line.strip().startswith('number of categories'):
                number_of_categories = int(line.split('=')[1].strip())
                self.parse_section_categories(f, self.parsed['odb']['sectionCategories'], number_of_categories)

        number_of_instances = 0
        number_of_steps = 0
        self.parsed['odb']['rootAssembly'] = dict()
        while line.strip() != '-----------------------------------------------------------' and line != "":
            if line.strip().startswith('Root assembly name'):
                self.parsed['odb']['rootAssembly']['name'] = line.strip().split("'")[1]
            if line.strip().startswith('number of instances'):
                number_of_instances = int(line.split('=')[1].strip())
            if line.strip().startswith('Total number of steps'):
                number_of_steps = int(line.split('=')[1].strip())
            line = f.readline()

        self.parsed['odb']['rootAssembly']['instances'] = dict()
        if number_of_instances > 0:
            try:
                self.parse_instances(f, self.parsed['odb']['rootAssembly']['instances'], number_of_instances)
            except Exception as e:  # TODO: Remove the generic try/except block and error message after alpha release
                self.print_critical(f"Unknown error occurred parsing odbreport file: {e}. Please report error "
                                f"to {_settings._parsing_error_contact} and send odb or "
                                f"odbreport ({_settings._default_odbreport_extension}) file.")
        # The following members of the root assembly object in the odb don't appear to be listed in the odbreport
        # nodeSets, elementSets, surfaces, nodes, elements, datumCsyses, sectionAssignments, rigidBodies,
        # pretensionSections, connectorOrientations
        # TODO: find out if above missing members are listed in odbreport and parse them if they are

        self.parsed['odb']['steps'] = dict()
        if number_of_steps == 0:
            while not line.strip().startswith('Total number of steps ') and line != "":
                line = f.readline()
            if line != "":
                number_of_steps = int(line.split('=')[1].strip())

        if number_of_steps > 0:
            self.parsed['odb']['steps'] = dict()
            try:
                self.parse_steps(f, self.parsed['odb']['steps'], number_of_steps)
            except Exception as e:  # TODO: Remove the generic try/except block and error message after alpha release
                self.print_critical(f"Unknown error occurred parsing odbreport file: {e}. Please report error "
                                f"to {_settings._parsing_error_contact} and send odb or "
                                f"odbreport ({_settings._default_odbreport_extension}) file.")
        # TODO: Find out if any of the following members of the odb appear in odbreport output: amplitudes, filters,
        #  jobData, parts, materials, sections, sectorDefinition, userData, customData, profiles

        f.close()
        if self.format == 'extract':
            self.parsed = self.create_extract_format(self.parsed, h5_file, time_stamp)

    def parse_section_categories(self, f, categories, number_of_categories):
        """Parse the section that contains section categories

        :param file object f: open file
        :param dict categories: dictionary for storing the section categories
        :param int number_of_categories: number of section categories to parse
        :return: None
        """
        line = f.readline()
        while (len(categories) < number_of_categories) and not \
                line.startswith('-------------------------------------------------------------------------------') and \
                line != "":
            # TODO: Find odb with sectionPoint array and likely parse sectionPoint data within this array
            if line.strip().startswith('Section category name'):
                section_category = dict()
                section_category['name'] = line.strip().split("'")[1]  # split on quote to remove from name
                line = f.readline()
                while not line.strip().startswith('Section category name') and line != '\n' and line != "":
                    if line.strip().startswith('description'):
                        section_category['description'] = line.split(":")[1].strip()
                    line = f.readline()
                categories[section_category['name']] = section_category
            line = f.readline()
            if line == "":
                break

    def parse_instances(self, f, instances, number_of_instances):
        """Parse the section that contains instances

        :param file object f: open file
        :param dict instances: dictionary for storing the instances
        :param int number_of_instances: number of instances to parse
        :return: None
        """
        while len(instances.keys()) < number_of_instances + 1:  # Get the part instances plus the assembly instance
            instance = dict()
            line = f.readline()  # won't enter loop if line is still on dashed line
            while not line.startswith('-----------------------------------------------------------') and line != "":
                if line.strip().startswith('Part instance') or line.strip().startswith('Assembly instance'):
                    instance['name'] = line.strip().split("'")[1]
                    if line.strip().startswith('Assembly'):  # Add suffix to specify it is an assembly instance
                        instance['name'] += "_Assembly"  # The suffix serves to differentiate the name
                    while line != '\n' and line != "":
                        line = f.readline()
                        if line.strip().startswith('embedded space'):
                            instance['embeddedSpace'] = line.split(":")[1].strip()
                        if line.strip().startswith('type'):
                            instance['type'] = line.split(":")[1].strip()
                        if line.strip().startswith('result'):
                            instance['resultState'] = line.split(":")[1].strip()
                        # TODO: verify resultState starts with 'result' and splits on ':'
                if line.strip().startswith('number of nodes ='):
                    number_of_nodes = int(line.split('=')[1].strip())
                    if number_of_nodes > 0:
                        self.parse_nodes(f, instance, number_of_nodes, instance['embeddedSpace'])
                if line.strip().startswith('number of element classes ='):
                    number_of_element_classes = int(line.split('=')[1].strip())
                    if number_of_element_classes > 0:
                        self.parse_element_classes(f, instance, number_of_element_classes)
                if line.strip().startswith('number of elements ='):
                    number_of_elements = int(line.split('=')[1].strip())
                    if number_of_elements > 0:
                        self.parse_elements(f, instance, number_of_elements)
                if line.strip().startswith('number of node sets ='):
                    number_of_node_sets = int(line.split('=')[1].strip())
                    if number_of_node_sets > 0:
                        self.parse_node_set(f, instance, number_of_node_sets)
                if line.strip().startswith('number of element sets ='):
                    number_of_element_sets = int(line.split('=')[1].strip())
                    if number_of_element_sets > 0:
                        self.parse_element_set(f, instance, number_of_element_sets)
                if line.strip().startswith('number of surfaces = '):
                    number_of_surfaces = int(line.split('=')[1].strip())
                    if number_of_surfaces > 0:
                        self.parse_surfaces(f, instance, number_of_surfaces)
                if line.strip().startswith('Analytical surface '):
                    self.parse_analytic_surface(f, instance, line)
                if line.strip().startswith('number of rigid bodies = '):
                    number_of_rigid_bodies = int(line.split('=')[1].strip())
                    if number_of_rigid_bodies > 0:
                        self.parse_rigid_bodies(f, instance, number_of_rigid_bodies)

                # TODO: Need to parse: sectionAssignments, beamOrientations, materialOrientations, rebarOrientations
                # TODO: get example of these in order to parse
                line = f.readline()
            instances[instance['name']] = instance
            if line == "":
                break

    def parse_nodes(self, f, instance, number_of_nodes, embedded_space):
        """Parse the section that contains nodes

        :param file object f: open file
        :param dict instance: dictionary for storing the nodes
        :param int number_of_nodes: number of nodes to parse
        :param str embedded_space: type of embedded space
        :return: None
        """
        line = f.readline()  # read line with words 'Label' and 'Coordinates'
        if 'Label' not in line:  # Case where nodes are not listed
            return
        line = f.readline()  # read line with dash dividers
        if self.format == 'extract':
            instance['nodes'] = dict()
            instance['nodes']['labels'] = list()
            instance['nodes']['coordinates'] = list()
            while len(instance['nodes']['labels']) < number_of_nodes:
                line = f.readline()
                line_values = line.split(',')
                instance['nodes']['labels'].append(int(line_values[0].strip()))
                coordinates = list(float(_.strip()) for _ in line_values[1:])
                if embedded_space.upper() == 'AXISYMMETRIC':
                    try:  # if axisymmetric, third coordinate should always be 0 and can be ignored
                        if coordinates[2] == 0:
                            del coordinates[2]
                    except IndexError:
                        pass
                instance['nodes']['coordinates'].append(coordinates)
                if line == "":
                    break
        else:
            instance['nodes'] = list()
            while len(instance['nodes']) < number_of_nodes:
                node = dict()
                line = f.readline()
                line_values = line.split(',')
                node['label'] = int(line_values[0].strip())
                node['coordinates'] = tuple(float(_.strip()) for _ in line_values[1:])
                instance['nodes'].append(node)
                if line == "":
                    break

    def parse_element_classes(self, f, instance, number_of_element_classes):
        """Parse the section that contains element classes

        :param file object f: open file
        :param dict instance: dictionary for storing the elements
        :param int number_of_element_classes: number of element classes to parse
        :return: None
        """
        instance['element_classes'] = dict()
        line = f.readline()
        for element_class_number in range(number_of_element_classes):
            if line.strip().startswith('Class '):
                class_name = line.replace('Class ', '').strip()
                if class_name == 'Number of elements':
                    line = f.readline()
                    class_name, number_of_elements = line.strip().split()
                    instance['element_classes'][class_name] = dict()
                    instance['element_classes'][class_name]['number_of_elements'] = number_of_elements
                else:
                    instance['element_classes'][class_name] = dict()
                line = f.readline()
                while not line.strip().startswith('Class ') and line != '\n' and line != "":
                    if line.strip().startswith('number of elements in class  ='):
                        instance['element_classes'][class_name]['number_of_elements'] = \
                            int(line.split('=')[1].strip())
                    if line.strip().startswith('number of nodes per element  ='):
                        instance['element_classes'][class_name]['number_of_nodes_per_element'] = \
                            int(line.split('=')[1].strip())
                    if line.strip().startswith('number of integration points ='):
                        instance['element_classes'][class_name]['number_of_integration_points'] = \
                            int(line.split('=')[1].strip())
                    if line.strip().startswith('number of faces per element  ='):
                        instance['element_classes'][class_name]['number_of_faces_per_element'] = \
                            int(line.split('=')[1].strip())
                    if line.strip().startswith('max integr. points per face  ='):
                        instance['element_classes'][class_name]['max_integration_points_per_face'] = \
                            int(line.split('=')[1].strip())
                    if line.strip().startswith('section category name        ='):
                        instance['element_classes'][class_name]['section_category_name'] = \
                            line.split('=')[1].strip()
                    line = f.readline()

    def parse_elements(self, f, instance, number_of_elements):
        """Parse the section that contains elements

        :param file object f: open file
        :param dict instance: dictionary for storing the elements
        :param int number_of_elements: number of elements to parse
        :return: None
        """
        line = f.readline()  # read header line
        if 'Label' not in line:  # Case where elements are not listed
            return
        line = f.readline()
        if self.format == 'extract':
            instance['elements'] = dict()
            element_count = 0
            while element_count < number_of_elements:
                line = f.readline()
                line_values = line.split(',')
                element_number = int(line_values[0].strip())
                element_type = line_values[1].strip()
                connectivity_list = list()
                section_category_name = 'All'
                for i, line_value in enumerate(line_values[2:]):
                    try:
                        connectivity_list.append(int(line_value.strip()))
                    except ValueError:
                        # sometimes the section category name is a string at the end of the line
                        section_category_name = ' '.join(line_values[i - 1:])
                try:
                    instance['elements'][element_type]['labels'].append(element_number)
                    instance['elements'][element_type]['connectivity'].append(connectivity_list)
                    instance['elements'][element_type]['section_category'].append(section_category_name)
                except KeyError:
                    instance['elements'][element_type] = dict()
                    instance['elements'][element_type]['labels'] = list()
                    instance['elements'][element_type]['connectivity'] = list()
                    instance['elements'][element_type]['section_category'] = list()
                    instance['elements'][element_type]['labels'].append(element_number)
                    instance['elements'][element_type]['connectivity'].append(connectivity_list)
                    instance['elements'][element_type]['section_category'].append(section_category_name)
                if line == "":
                    break
                else:
                    element_count += 1
        else:
            instance['elements'] = list()
            while len(instance['elements']) < number_of_elements:
                element = dict()
                line = f.readline()
                line_values = line.split(',')
                element['label'] = int(line_values[0].strip())
                element['type'] = line_values[1].strip()
                # element['connectivity'] = tuple(int(_.strip()) for _ in line_values[2:])
                connectivity_list = list()
                for i, line_value in enumerate(line_values[2:]):
                    try:
                        connectivity_list.append(int(line_value.strip()))
                    except ValueError:
                        # sometimes the section category name is a string at the end of the line
                        element['sectionCategory'] = dict()
                        element['sectionCategory']['name'] = ' '.join(line_values[i - 1:])
                element['connectivity'] = tuple(connectivity_list)
                instance['elements'].append(element)
                if line == "":
                    break

    def parse_node_set(self, f, instance, number_of_node_sets):
        """Parse the section that contains node sets

        :param file object f: open file
        :param dict instance: dictionary for storing the node sets
        :param int number_of_node_sets: number of node sets to parse
        :return: None
        """
        instance['nodeSets'] = dict()
        summary_node_set = False
        while len(instance['nodeSets']) < number_of_node_sets:
            line = f.readline()
            if line.strip().split() == ['Name', 'Size']:  # If only a summary of the node set info is given
                summary_node_set = True
                line = f.readline()
            if summary_node_set:
                line_values = line.strip().split()
                if len(line_values) == 2:
                    node_set = dict()
                    node_name, node_size = line_values
                    node_set['name'] = node_name.strip()[1:-1]  # Removing single quotes
                    node_set['size'] = node_size
                    instance['nodeSets'][node_set['name']] = node_set
                else:
                    return
            # Code below to deal with complete node set list
            if line.strip().startswith('Node set '):
                node_set = dict()
                node_set['name'] = line.replace('Node set ', '').strip()
                line = f.readline()
                node_set_size = int(line.split('=')[1].strip())
                instance_names = set()
                node_set['nodes'] = list()
                while len(node_set['nodes']) < node_set_size:
                    line = f.readline()
                    if line.strip().startswith('node labels from instance '):
                        instance_names.add(line.replace('node labels from instance', '')
                                           .replace(':', '').strip()[1:-1])
                    elif line != '\n':
                        line_values = line.split(',')
                        for value in line_values:
                            if self.format == 'extract':
                                node_set['nodes'].append(int(value))
                            else:
                                node = dict()
                                node['label'] = int(value)
                                node_set['nodes'].append(node)
                    if line == "":
                        break
                node_set['instanceNames'] = tuple(instance_names)
                instance['nodeSets'][node_set['name']] = node_set
            if line == "":
                break

    def parse_element_set(self, f, instance, number_of_element_sets):
        """Parse the section that contains element sets

        :param file object f: open file
        :param dict instance: dictionary for storing the element sets
        :param int number_of_element_sets: number of element sets to parse
        :return: None
        """
        instance['elementSets'] = dict()
        summary_element_set = True
        while len(instance['elementSets']) < number_of_element_sets:
            line = f.readline()
            if line.strip().split() == ['Name', 'Size']:  # If only a summary of the element set info is given
                summary_element_set = True
                line = f.readline()
            if summary_element_set:
                line_values = line.strip().split()
                if len(line_values) == 2:
                    element_set = dict()
                    element_name, element_size = line_values
                    element_set['name'] = element_name.strip()[1:-1]  # Removing single quotes
                    element_set['size'] = element_size
                    instance['elementSets'][element_set['name']] = element_set
                else:
                    return
            # Code below to deal with complete element set list
            if line.strip().startswith('Element set '):
                element_set = dict()
                element_set['name'] = line.replace('Element set ', '').strip()
                line = f.readline()
                element_set_size = int(line.split('=')[1].strip())
                instance_names = set()
                if self.format == 'extract':
                    element_set['elements'] = dict()
                    element_count = 0
                    while element_count < element_set_size:
                        line = f.readline()
                        if line.strip().startswith('element labels from instance '):
                            instance_name = \
                                line.replace('element labels from instance', '').replace(':', '').strip()[1:-1]
                        elif line != '\n':
                            line_values = line.split(',')
                            for value in line_values:
                                try:
                                    element_set['elements'][instance_name].append(int(value))
                                except KeyError:
                                    element_set['elements'][instance_name] = list()
                                    element_set['elements'][instance_name].append(int(value))
                                element_count += 1
                        if line == "":
                            break
                    instance['elementSets'][element_set['name']] = element_set
                else:
                    element_set['elements'] = list()
                    while len(element_set['elements']) < element_set_size:
                        line = f.readline()
                        if line.strip().startswith('element labels from instance '):
                            instance_name = \
                                line.replace('element labels from instance', '').replace(':', '').strip()[1:-1]
                            instance_names.add(instance_name)
                        elif line != '\n':
                            line_values = line.split(',')
                            for value in line_values:
                                element = dict()
                                element['label'] = int(value)
                                element['instanceName'] = instance_name
                                element_set['elements'].append(element)
                        if line == "":
                            break
                    element_set['instanceNames'] = tuple(instance_names)
                    instance['elementSets'][element_set['name']] = element_set
            if line == "":
                break

    def parse_surfaces(self, f, instance, number_of_surfaces):
        """Parse the section that contains surfaces

        :param file object f: open file
        :param dict instance: dictionary for storing the surfaces
        :param int number_of_surfaces: number of surfaces to parse
        :return: None
        """
        instance['surfaces'] = dict()
        summary_surface_set = False
        while len(instance['surfaces']) < number_of_surfaces:
            line = f.readline()
            if line.strip().split() == ['Name', 'Size']:  # If only a summary of the surface set info is given
                summary_surface_set = True
                line = f.readline()
            if summary_surface_set:
                line_values = line.strip().split()
                if len(line_values) == 2:
                    surface = dict()
                    surface_name, surface_size = line_values
                    surface['name'] = surface_name.strip()[1:-1]  # Removing single quotes
                    surface['size'] = surface_size
                    instance['surfaces'][surface['name']] = surface
                else:
                    return
            # Code below to deal with complete surface set list
            if line.strip().startswith('Surface set '):
                surface = dict()
                surface['name'] = line.replace('Surface set ', '').strip()[
                                  1:-1]  # removing single quote at front and end
                line = f.readline()
                line = f.readline()
                instance_names = set()
                faces = set()
                if line.strip().startswith('nodes from instance '):
                    instance_name = line.replace('nodes from instance', '').replace(':', '').strip()[1:-1]
                    instance_names.add(instance_name)
                    surface['nodes'] = list()
                    while line != '\n' and line != "":
                        # Found instances where it said the set size is 2, but only 1 node was listed
                        # so instead of looping through the number of nodes, the loop goes until there is a new line
                        line = f.readline()
                        if line != '\n':
                            for value in line.split(','):
                                if self.format == 'extract':
                                    surface['nodes'].append(int(value))
                                else:
                                    node = dict()
                                    node['label'] = int(value)
                                    # except ValueError:
                                    surface['nodes'].append(node)
                elif line.strip().startswith('element label:face pairs from instance '):
                    instance_name = line.replace('element label:face pairs from instance ', '').replace(
                        ':', '').strip()[1:-1]
                    instance_names.add(instance_name)
                    if self.format == 'extract':
                        surface['elements'] = dict()
                        element_count = 0
                        while line != '\n':
                            line = f.readline()
                            if line.strip().startswith('element label:face pairs from instance '):
                                instance_name = line.replace('element label:face pairs from instance ', '').replace(
                                    ':', '').strip()[1:-1]
                                instance_names.add(instance_name)
                            elif line != '\n':
                                for value in line.split(','):
                                    element_label, face = value.split(':')
                                    faces.add(face.strip())
                                    try:
                                        surface['elements'][instance_name].append(int(element_label.strip()))
                                    except KeyError:
                                        surface['elements'][instance_name] = list()
                                        surface['elements'][instance_name].append(int(element_label.strip()))
                                    element_count += 1
                            if line == "":
                                break
                    else:
                        surface['elements'] = list()
                        while line != '\n':
                            line = f.readline()
                            if line.strip().startswith('element label:face pairs from instance '):
                                instance_name = line.replace('element label:face pairs from instance ', '').replace(
                                    ':', '').strip()[1:-1]
                                instance_names.add(instance_name)
                            elif line != '\n':
                                for value in line.split(','):
                                    element_label, face = value.split(':')
                                    faces.add(face.strip())
                                    element = dict()
                                    element['label'] = int(element_label.strip())
                                    element['instanceName'] = instance_name
                                    surface['elements'].append(element)
                            if line == "":
                                break
                surface['faces'] = tuple(faces)
                surface['instanceNames'] = tuple(instance_names)
                instance['surfaces'][surface['name']] = surface
            if line == "":
                break

    def parse_analytic_surface(self, f, instance, line):
        """Parse the section that contains analytic surface

        :param file object f: open file
        :param dict instance: dictionary for storing the analytic surface
        :param str line: current line of file
        :return: None
        """
        # TODO: get odb with localCoordData under Analytic surface
        instance['analyticSurface'] = dict()
        instance['analyticSurface']['name'] = line.replace('Analytical surface ', '').strip()[1:-1]
        profile = False
        while line != '\n' and line != "":
            line = f.readline()
            if line.strip().startswith('type'):
                instance['analyticSurface']['type'] = line.replace('type', '').strip()
                if instance['analyticSurface']['type'] == 'SEGMENTS':
                    instance['analyticSurface']['segments'] = dict()
            if line.strip().startswith('fillet radius = '):
                instance['analyticSurface']['filletRadius'] = float(line.split('=')[1].strip())
            if line.strip().startswith('profile:'):
                profile = True
                continue
            if 'segments' in instance['analyticSurface'] and profile and line != '\n':
                segment = dict()
                line_values = line.strip().split(',')
                if line_values[0] == 'START':
                    segment['name'] = line_values[0]
                    segment['origin'] = [float(_.strip()) for _ in line_values[1:]]
                elif line_values[0] == 'LINE':
                    segment['name'] = line_values[0]
                    segment['endPoint'] = [float(_.strip()) for _ in line_values[1:]]
                elif line_values[0] == 'CIRCLE':
                    segment['name'] = line_values[0]
                    segment['endPoint'] = [float(_.strip()) for _ in line_values[1:]]
                # TODO: get odb with parabola segments and parse that data here
                instance['analyticSurface']['segments'][segment['name']] = segment

    def parse_rigid_bodies(self, f, instance, number_of_rigid_bodies):
        """Parse the section that contains rigid_bodies

        :param file object f: open file
        :param dict instance: dictionary for storing the rigid bodies
        :param int number_of_rigid_bodies: number of rigid bodies to parse
        :return: None
        """
        instance['rigidBodies'] = list()
        line = f.readline()
        while len(instance['rigidBodies']) < number_of_rigid_bodies:
            if line.strip().startswith('Rigid Body #'):
                rigid_body = dict()
                line = f.readline()
                while line != '\n' and not line.strip().startswith('Rigid Body #') and line != "":
                    if line.strip().startswith('position:'):
                        rigid_body['position'] = line.replace('position:', '').strip()
                    if line.strip().startswith('reference node(s):'):
                        # TODO: need odb with example of referenceNode members: elements, faces
                        line = f.readline()
                        instance['referenceNode'] = dict()
                        instance['referenceNode']['nodes'] = list()
                        instance_names = set()
                        while (line.startswith('      ')):
                            re_match = re.match(r'(\d+) from instance (.*)', line.strip(), re.IGNORECASE)
                            if re_match:
                                if self.format == 'extract':
                                    instance['referenceNode']['nodes'].append(int(re_match.group(1)))
                                else:
                                    node = dict()
                                    node['label'] = int(re_match.group(1))
                                    instance['referenceNode']['nodes'].append(node)
                                instance_names.add(re_match.group(2))
                            line = f.readline()
                        instance['referenceNode']['instanceNames'] = tuple(instance_names)
                    if line.strip().startswith('analytical surface '):
                        surface_name = line.replace('analytical surface ', '').strip()
                        if 'analyticSurface' in instance and 'name' in instance['analyticSurface'] and \
                                instance['analyticSurface']['name'] == surface_name:
                            rigid_body['analyticSurface'] = instance['analyticSurface']
                        else:
                            rigid_body['analyticSurface'] = dict()
                            rigid_body['analyticSurface']['name'] = surface_name
                    if line != '\n':
                        line = f.readline()
                    # TODO: need to get an odb with following rigid body members:
                    #  isothermal, elements, tieNodes, pinNodes

                instance['rigidBodies'].append(rigid_body)
            else:
                line = f.readline()
            if line == "":
                break

    def parse_steps(self, f, steps, number_of_steps):
        """Parse the section that contains the data for steps

        :param file object f: open file
        :param dict steps: dictionary for storing the steps
        :param int number_of_steps: number of steps to parse
        :return: None
        """
        line = f.readline()
        self.number_of_steps = number_of_steps
        self.current_step_count = 0
        while line.strip() != 'End of ODB Report.' and line != "":
            # TODO: Find odbreport with loadCases in the steps
            if line.strip().startswith('Step name'):
                step = dict()
                step['name'] = line.replace('Step name', '').strip()[1:-1]
                if self.format == 'extract':
                    self.current_step_name = step['name']
                while not line.strip().startswith('Total number of frames') and \
                        not line.strip().startswith('Number of history regions') and line != "":
                    line = f.readline()
                    if ',' in line:
                        key, value = line.split(',', 1)
                        step[key.strip()] = value.strip()
                if 'frames' in line:
                    number_of_frames = int(line.split('=')[1].strip())
                    step['frames'] = list()
                    line = self.parse_frames(f, step['frames'], number_of_frames)
                    while not line.strip().startswith('Number of history regions') and line != "":
                        line = f.readline()
                number_of_history_regions = 0
                if line.strip().startswith('Number of history regions'):
                    number_of_history_regions = int(line.split('=')[1].strip())
                step['historyRegions'] = dict()
                line = self.parse_history_regions(f, step['historyRegions'], number_of_history_regions)
                steps[step['name']] = step
                self.current_step_count += 1
            else:
                line = f.readline()
            if line == "":
                break

    def parse_frames(self, f, frames, number_of_frames):
        """Parse the section that contains the data for frames

        :param file object f: open file
        :param list frames: list for storing the frames
        :param int number_of_frames: number of frames to parse
        :return: current line of file
        :rtype: str
        """
        line = f.readline()
        if line.strip().startswith('Number of field outputs'):  # Summary instead of full details
            frame = dict()
            frame['total_number'] = number_of_frames
            frame['fields'] = list()
            while line != '\n' and line != "":
                line = f.readline()
                frame['fields'].append(line.replace('Field name', '').strip()[1:-1])
            frames.append(frame)
            return
        # Code below handles full list of frames
        current_frame_number = 0
        while 'history' not in line.lower() and line != "":
            if line.strip().startswith('Frame number'):
                frame = dict()
                frame_number = int(line.replace('Frame number', '').strip())
                current_frame_number += 1
                while not line.strip().startswith('Number of field outputs') and not \
                        line.strip().startswith('Field name') and line != "":
                    line = f.readline()
                    if ',' in line:
                        key, value = line.split(',', 1)
                        frame[key.strip()] = value.strip()
                if self.format == 'extract':
                    self.current_frame = frame
                    self.current_frame_number = current_frame_number
                frame['fields'] = dict()
                line = self.parse_fields(f, frame['fields'], line)
                frames.append(frame)
            else:
                line = f.readline()
            if line == "":
                break
        return line

    def parse_fields(self, f, fields, line):
        """Parse the section that contains the data for field outputs

        :param file object f: open file
        :param dict fields: dictionary for storing the field outputs
        :param str line: current line of file
        :return: current line of file
        :rtype: str
        """
        self.current_field_number = 0
        field = dict()
        while 'history' not in line.lower() \
                and not line.startswith('-----------------------------------------------------------') \
                and not line.startswith('  -------------------------------------') and line != "":
            nodal = False
            if line.strip().startswith('Field name'):
                self.current_field_number += 1
                field = dict()
                if line.strip()[-1] == '/':  # Line has continuation
                    continuation_line = f.readline()
                    line += continuation_line
                field['name'] = line.replace('Field name', '').strip()[1:-1]
                field['locations'] = list()
                while not line.strip().startswith('Components of field ') and not \
                        line.strip().startswith('Invariants of field') and line != "":
                    line = f.readline()
                    if ':' in line:
                        key, value = line.split(':', 1)
                        if line.strip().startswith('component labels'):
                            field[key.strip()] = value.strip().split()  # component labels are separated by spaces
                        else:
                            field[key.strip()] = value.strip()
                    if line.strip().startswith('Location'):
                        # TODO: Find odb with multiple Locations and Location with sectionPoints
                        location = dict()
                        line = f.readline()
                        if 'position' in line:
                            location['position'] = line.split(':', 1)[1].strip()
                            if location['position'] == 'NODAL':
                                nodal = True
                        field['locations'].append(location)
                if line.strip().startswith('Components of field ') or line.strip().startswith('Invariants of field'):
                    line = self.parse_components_of_field(f, line, field, nodal)
            if line.strip().startswith('Components of field ') or line.strip().startswith('Invariants of field'):
                line = self.parse_components_of_field(f, line, field, nodal)
            if 'name' in field:
                fields[field['name']] = field  # This may get called more than once, but there is no problem in doing so
            # if line != '\n':
            line = f.readline()
        return line

    def parse_components_of_field(self, f, line, field, nodal):
        """Parse the section that contains the data for field outputs found after the 'Components of field' heading

        :param file object f: open file
        :param str line: current line of file
        :param dict field: dictionary for storing field output
        :param bool nodal: says whether data is nodal
        :return: current line of file
        :rtype: str
        """

        if line.strip()[-1] == '/':  # Line has continuation
            continuation_line = f.readline()
            line += continuation_line
        if self.format == 'extract':
            if self.current_frame_number == 1 and self.current_step_count == 0:
                self.first_field_data = True
            else:
                self.first_field_data = False
            if self.current_frame_number == 1 and self.current_step_count > 0:
                self.new_step = True
            else:
                self.new_step = False
            field_values = self.setup_extract_field_format(field, nodal)
            line = self.parse_field_values(f, line, field_values)
        else:
            field['values'] = list()
            line = self.parse_field_values(f, line, field['values'])
        return line

    def setup_extract_field_format(self, field, nodal):
        """Do setup of field output formatting for extract format

        :param dict field: dictionary with field data
        :param bool nodal: indicates whether field data includes nodal data
        :return: dictionary for which to store field values
        :rtype: dict
        """
        try:
            field_name, region_name = field['name'].split('  ', 1)  # Two spaces are usually used to separate the values
        except ValueError:  # If field name doesn't have a space (e.g. 'NT11') or only a single space
            if nodal:  # Have not yet seen an INTEGRATION_POINT or WHOLE_ELEMENT with a region name, just NODAL
                try:  # TODO: adjust if different case is discovered
                    field_name, region_name = field['name'].rsplit(' ', 1)
                except ValueError:  # If field name doesn't have a space (e.g. 'U')
                    region_name = 'ALL'
                    field_name = field['name']
            else:
                region_name = 'ALL'
                field_name = field['name']

        field_name = field_name.replace('/', '|').strip()
        region_name = region_name.replace('/', '|').strip()
        try:
            current_output = self.field_extract_format[region_name][field_name]
        except KeyError:
            try:
                self.field_extract_format[region_name][field_name] = dict()
            except KeyError:
                self.field_extract_format[region_name] = dict()
                self.field_extract_format[region_name][field_name] = dict()
            current_output = self.field_extract_format[region_name][field_name]
        return current_output

    def parse_field_values(self, f, line, values):
        """Parse the section that contains the data for field values

        :param file object f: open file
        :param str line: current line
        :param list values: list for storing the field values
        :return: current line of file
        :rtype: str
        """
        instance_match = re.match(r".*for part instance '(.*?)'", line, re.IGNORECASE)
        if instance_match:
            value_instance = instance_match.group(1)
            if not value_instance.strip():  # If the string is empty
                value_instance = "rootAssembly"
        else:
            value_instance = "rootAssembly"  # The element or node belongs to the rootAssembly
        element_match = re.match(r".*element type '.*?(\d+)\D*'", line, re.IGNORECASE)
        if element_match:
            element_size = int(element_match.group(1))
        else:
            element_size = None
        line = f.readline()
        headers = line.split(',')
        number_of_data_values = 0  # The number of values that don't include: Instance, Element, Node, SP, IP
        element_given = False
        node_given = False
        section_point_given = False
        integration_point_given = False
        for i, header in enumerate(headers):
            header = header.strip()
            if header == 'Element':
                element_given = True
            elif header == 'Node':
                node_given = True
            elif header == 'SP':
                section_point_given = True
            elif header == 'IP':
                integration_point_given = True
            elif header == 'Instance':
                pass
            else:
                number_of_data_values += 1
            headers[i] = header  # Need to store stripped header, without spaces or line breaks
        value_headers = headers[-number_of_data_values:]  # Storing the names of the headers that have data
        line = f.readline()  # Blank line
        line = 'Ready for first line of data'

        while line != '\n' and line != "":
            value = dict()
            line = f.readline()
            if line == '\n' or line.strip() == "":
                break
            line_values = line.split(',')
            line_value_number = 0
            if self.format != 'extract':
                value['instance'] = value_instance
                if element_given:
                    value['elementLabel'] = int(line_values[line_value_number])
                    line_value_number += 1
                if node_given:
                    value['nodeLabel'] = int(line_values[line_value_number])
                    line_value_number += 1
                if section_point_given:
                    value['sectionPoint'] = int(line_values[line_value_number])
                    line_value_number += 1
                if integration_point_given:
                    try:
                        value['integrationPoint'] = int(line_values[line_value_number])
                    except ValueError:
                        value['integrationPoint'] = None
                # get the values after the first 5 values of: Instance, Element, Node, SP, IP
                for i, datum in enumerate(line_values[-number_of_data_values:]):
                    try:
                        value[value_headers[i]] = float(datum)
                    except ValueError:  # The float command will fail on None
                        value[value_headers[i]] = None
                values.append(value)
            else:
                time_value = float(self.current_frame['frame value'])
                try:
                    values[value_instance]['value_names'] = value_headers
                except KeyError:
                    values[value_instance] = dict()
                    values[value_instance]['time'] = list()
                    values[value_instance]['time_index'] = dict()
                    values[value_instance]['sectionPoint'] = list()
                    values[value_instance]['integrationPoint'] = list()
                    values[value_instance]['value_names'] = value_headers
                    values[value_instance]['element_size'] = element_size
                    values[value_instance]['values'] = [list() for _ in range(self.number_of_steps)]

                if element_given:
                    index_key, just_added = self.get_position_index(int(line_values[line_value_number]), 'elements',
                                                                    values[value_instance])
                    position_length = len(values[value_instance]['elements'])
                    line_value_number += 1
                if node_given:
                    index_key, just_added = self.get_position_index(int(line_values[line_value_number]), 'nodes',
                                                                    values[value_instance])
                    position_length = len(values[value_instance]['nodes'])
                    line_value_number += 1
                if section_point_given:
                    current_section_point = int(line_values[line_value_number])
                    if element_size:
                        if just_added:
                            values[value_instance]['sectionPoint'].append(list())
                            values[value_instance]['sectionPoint'][index_key].append(current_section_point)
                        else:
                            if current_section_point not in values[value_instance]['sectionPoint'][index_key]:
                                values[value_instance]['sectionPoint'][index_key].append(current_section_point)
                    else:
                        if just_added:
                            values[value_instance]['sectionPoint'].append(int(line_values[line_value_number]))
                    line_value_number += 1
                if integration_point_given:
                    try:
                        current_integration_point = int(line_values[line_value_number])
                    except ValueError:
                        current_integration_point = None
                    if element_size:
                        if just_added:
                            values[value_instance]['integrationPoint'].append(list())
                            values[value_instance]['integrationPoint'][index_key].append(current_integration_point)
                        else:
                            if current_integration_point not in values[value_instance]['integrationPoint'][index_key]:
                                values[value_instance]['integrationPoint'][index_key].append(current_integration_point)
                    else:
                        if just_added:
                            values[value_instance]['integrationPoint'].append(current_integration_point)

                if self.new_step and not values[value_instance]['values'][self.current_step_count]:
                    for time_index in range(len(values[value_instance]['time_index'])):
                        values[value_instance]['values'][self.current_step_count].append(list())
                        self.pad_none_values(self.current_step_count, time_index, position_length,
                                             number_of_data_values, element_size,
                                             values[value_instance]['values'])

                try:
                    time_index = values[value_instance]['time_index'][time_value]
                except KeyError:  # New time
                    time_index = len(values[value_instance]['time'])
                    values[value_instance]['time_index'][time_value] = time_index
                    values[value_instance]['time'].append(time_value)

                    values[value_instance]['values'][self.current_step_count].append(list())

                    if not self.first_field_data:
                        self.pad_none_values(self.current_step_count, time_index, position_length,
                                             number_of_data_values, element_size,
                                             values[value_instance]['values'])
                    if self.current_step_count > 0:  # If there's a new time in a step after the first step
                        for previous_step in range(self.current_step_count):  # Then all previous steps must be padded
                            values[value_instance]['values'][previous_step].append(list())
                            self.pad_none_values(previous_step, time_index, position_length, number_of_data_values,
                                                 element_size, values[value_instance]['values'])

                # get the values after the first 5 values of: Instance, Element, Node, SP, IP
                if number_of_data_values == 1:
                    data_value = float(line_values[-1])
                else:
                    data_value = list()
                    for datum in line_values[-number_of_data_values:]:
                        try:
                            data_value.append(float(datum))
                        except ValueError:  # Should be raised on None values
                            data_value.append(None)

                if element_size:
                    value_length = len(values[value_instance]['values'][self.current_step_count][time_index])
                    if just_added:
                        if self.first_field_data:
                            values[value_instance]['values'][self.current_step_count][time_index].append(list())
                            values[value_instance]['values'][self.current_step_count][time_index][
                                value_length].append(data_value)
                        else:  # Must pad all previous steps and frames as new field data has shown up
                            for previous_step in range(self.current_step_count + 1):
                                for previous_frame in range(time_index):
                                    if number_of_data_values == 1:
                                        values[value_instance]['values'][previous_step][previous_frame].append(
                                            [None for _ in range(element_size)])
                                    else:
                                        values[value_instance]['values'][previous_step][previous_frame].append(
                                            [[None for _ in range(number_of_data_values)] for _ in range(
                                                element_size)])
                            if index_key == value_length:
                                values[value_instance]['values'][self.current_step_count][time_index].append(list())
                                values[value_instance]['values'][self.current_step_count][time_index][
                                    value_length].append(data_value)
                            else:
                                values[value_instance]['values'][self.current_step_count][time_index][
                                    index_key].append(data_value)
                    else:
                        if index_key == len(values[value_instance]['values'][self.current_step_count][time_index]):
                            # If the index_key is the length of the list, then it's one more index than currently exists
                            values[value_instance]['values'][self.current_step_count][time_index].append(list())
                            values[value_instance]['values'][self.current_step_count][time_index][
                                index_key].append(data_value)
                        else:
                            values[value_instance]['values'][self.current_step_count][time_index][
                                index_key].append(data_value)
                else:
                    if just_added:
                        if self.first_field_data:
                            values[value_instance]['values'][self.current_step_count][time_index].append(data_value)
                        else:  # Must pad all previous steps and frames
                            for previous_step in range(self.current_step_count + 1):
                                for previous_frame in range(time_index):
                                    if number_of_data_values == 1:
                                        values[value_instance]['values'][previous_step][previous_frame].append(None)
                                    else:
                                        values[value_instance]['values'][previous_step][previous_frame].append(
                                            [None for _ in range(number_of_data_values)])
                            if index_key == len(values[value_instance]['values'][self.current_step_count][time_index]):
                                values[value_instance]['values'][self.current_step_count][time_index].append(data_value)
                            else:
                                values[value_instance]['values'][self.current_step_count][time_index][
                                    index_key] = data_value
                    else:
                        if index_key == len(values[value_instance]['values'][self.current_step_count][time_index]):
                            # If the index_key is the length of the list, then it's one more index than currently exists
                            values[value_instance]['values'][self.current_step_count][time_index].append(data_value)
                        else:
                            values[value_instance]['values'][self.current_step_count][time_index][index_key] \
                                = data_value
        return line


    def get_position_index(self, position, position_type, values):
        """Get the index of the position (node or element) currently used

        :param int position: integer representing a node or element
        :param str position_type: string of either 'nodes' or 'elements'
        :param dict values: dictionary where values are stored
        :return: index, just_added
        :rtype: int, bool
        """
        try:
            index_key = values['keys'][position]
            just_added = False
        except KeyError:
            try:
                position_length = len(values[position_type])
            except KeyError:  # If nodes or elements list hasn't been created than neither has the keys dictionary
                values[position_type] = list()
                values['keys'] = dict()
                position_length = 0
            values['keys'][position] = position_length
            values[position_type].append(position)
            just_added = True
            index_key = values['keys'][position]
        return index_key, just_added

    def pad_none_values(self, step_number, frame_number, position_length, data_length, element_size, values):
        """Pad the values list with None or lists of None values in the locations indicated by the parameters

        :param int step_number: index of current step
        :param int frame_number: index of current frame
        :param int position_length: number of nodes or elements
        :param int data_length: length of data given in field
        :param int element_size: number of element lines that could be listed, e.g. for a hex this value would be 6
        :param list values: list that holds the data values
        """
        if element_size:
            if data_length == 1:
                values[step_number][frame_number] = \
                    [[None for _ in range(element_size)] for _ in range(position_length)]
            else:
                values[step_number][frame_number] = \
                    [[[None for _ in range(data_length)] for _ in range(element_size)] for _ in range(position_length)]
        else:
            if data_length == 1:
                values[step_number][frame_number] = [None for _ in range(position_length)]
            else:
                values[step_number][frame_number] = [[None for _ in range(data_length)] for _ in range(position_length)]
        return

    def parse_history_regions(self, f, regions, number_of_history_regions):
        """Parse the section that contains history regions

        :param file object f: open file
        :param dict regions: dict for storing the history region data
        :param int number_of_history_regions: number of history regions to parse
        :return: current line of file
        :rtype: str
        """
        line = f.readline()
        history_region_summary = False
        while not line.startswith('-----------------------------------------------------------') and line != "":
            if line.strip().startswith('History Region'):
                region = dict()
                if line.strip()[-1] == '/':  # Line has continuation
                    continuation_line = f.readline()
                    line += continuation_line
                region['name'] = line.replace('History Region', '').strip()[1:-1]
                while not line.strip().startswith('History Point') and line != "":
                    line = f.readline()
                    if ':' in line:
                        key, value = line.split(':', 1)
                        region[key.strip()] = value.strip()
                    if line.strip().startswith('Number of history outputs'):
                        number_of_history_outputs = int(line.split('=')[1].strip())
                        history_region_summary = True
                        break
                if history_region_summary:
                    region['historyOutputs'] = list()
                    while len(region['historyOutputs']) < number_of_history_outputs and line != "":
                        if line.strip().startswith('History Output'):
                            if line.strip()[-1] == '/':  # Line has continuation
                                continuation_line = f.readline()
                                line += continuation_line
                            output_name = line.replace('History Output', '').strip()[1:-1]
                            region['historyOutputs'].append(output_name)
                        line = f.readline()
                    regions[region['name']] = region
                    continue
                region['point'] = dict()
                while not line.strip().startswith('Number of history outputs') and not \
                        line.strip().startswith('History Output') and line != "":
                    line = f.readline()
                    if ':' in line:
                        key, value = line.split(':', 1)
                        region['point'][key.strip()] = value.strip()
                # TODO: Find odb with historyPoint that has the following listed
                #  element, sectionPoint, assembly
                if self.format == 'extract':
                    self.current_region = region
                region['historyOutputs'] = dict()
                line = self.parse_history_outputs(f, region['historyOutputs'], line)
                regions[region['name']] = region
            else:
                line = f.readline()
            if line == "":
                break
        return line

    def setup_extract_history_format(self, output, current_history_output):
        """Do setup of history output formatting for extract format

        :param dict output: dictionary with history output data
        :param int current_history_output: current history output count
        """
        try:
            instance_name = self.current_region['point']['instance'].upper()
        except KeyError:
            instance_name = 'ALL'
        try:
            region_name = self.current_region['point']['region'].upper()
        except KeyError:
            region_name = self.current_region['name']

        output_name = output['name'].replace('/', '|')
        try:
            current_output = self.history_extract_format[instance_name][region_name][output_name]
        except KeyError:
            try:
                self.history_extract_format[instance_name][region_name][output_name] = dict()
            except KeyError:
                try:
                    self.history_extract_format[instance_name][region_name] = dict()
                except KeyError:
                    self.history_extract_format[instance_name] = dict()
                    self.history_extract_format[instance_name][region_name] = dict()
                self.history_extract_format[instance_name][region_name][output_name] = dict()
            current_output = self.history_extract_format[instance_name][region_name][output_name]
            # Within this except, current_output is always a new dictionary
            current_output['time'] = list()
            current_output['time_index'] = dict()
            current_output['type'] = list()
            current_output['description'] = list()
            current_output['data'] = [list() for _ in range(self.number_of_steps)]
            current_output['previous_step'] = None

        if self.current_step_name != current_output['previous_step']:
            current_output['type'].append(output['type'])
            current_output['description'].append(output['description'])

            if 'node' in self.current_region['point']:
                try:
                    current_output['node'].append(self.current_region['point']['node'])
                except KeyError:
                    current_output['node'] = list()
                    current_output['node'].append(self.current_region['point']['node'])
            elif 'element' in self.current_region['point']:
                try:
                    current_output['element'].append(self.current_region['point']['element'])
                except KeyError:
                    current_output['element'] = list()
                    current_output['element'].append(self.current_region['point']['element'])
            current_output['data'][self.current_step_count] = [None for _ in current_output['data'][0]]

        if self.current_step_count == 0 and current_history_output == 0:
            if not current_output['time']:
                for time_value in output['time']:
                    time_index = len(current_output['time'])
                    current_output['time_index'][time_value] = time_index
                    current_output['time'].append(time_value)
                current_output['data'][0] = output['data']
        else:
            for data_index, time_value in enumerate(output['time']):
                try:
                    time_index = current_output['time_index'][time_value]
                except KeyError:  # New time
                    time_index = len(current_output['time'])
                    current_output['time_index'][time_value] = time_index
                    current_output['time'].append(time_value)
                    for prev_step in range(self.current_step_count):
                        current_output['data'][prev_step].append(None)
                    current_output['data'][self.current_step_count].append(output['data'][data_index])
                current_output['data'][self.current_step_count][time_index] = output['data'][data_index]

        del output['type']  # Don't need this now that it's in the extract format
        del output['description']
        del output['time']
        del output['data']
        current_output['previous_step'] = self.current_step_name

    def parse_history_outputs(self, f, outputs, line):
        """Parse the section that contains history outputs

        :param file object f: open file
        :param dict outputs: dict for storing the history output data
        :param str line: current line of file
        :return: current line of file
        :rtype: str
        """
        if not line.strip().startswith('History Output'):
            line = f.readline()
        while not line.strip().startswith('History Region') and line != "" \
                and not line.startswith('-----------------------------------------------------------'):
            if line.strip().startswith('History Output'):
                output = dict()
                if line.strip()[-1] == '/':  # Line has continuation
                    continuation_line = f.readline()
                    line += continuation_line
                output['name'] = line.replace('History Output', '').strip()[1:-1]
                while not line.strip().startswith('Frame value') and line != "":
                    line = f.readline()
                    if ':' in line:
                        key, value = line.split(':', 1)
                        output[key.strip()] = value.strip()
                output['data'] = list()
                if self.format == 'extract':
                    output['time'] = list()
                if line.strip().startswith('Frame value') and line != "":
                    line = f.readline()
                    while line != "\n":
                        frame, datum = line.split(',')
                        if self.format == 'extract':
                            output['time'].append(float(frame.strip()))
                            output['data'].append(float(datum.strip()))
                        else:
                            output['data'].append((float(frame.strip()), float(datum.strip())))  # tuple of floats
                        line = f.readline()
                outputs[output['name']] = output
                if self.format == 'extract':
                    self.setup_extract_history_format(output, len(outputs.keys()))
            else:
                line = f.readline()
        return line

    def create_extract_format(self, odb_dict, h5_file, time_stamp):
        """Format the dictionary with the odb data into something that resembles previous abaqus extract method

        :param dict odb_dict: Dictionary with odb data
        :param str h5_file: Name of h5_file to use for storing data
        :param str time_stamp: Time stamp for possibly appending to hdf5 file names
        :return: None
        """
        if self.format != 'extract':
            self.print_error("Must specify extract format to utilize this routine.")
            return None  # If extract format wasn't given when parsing the data, this method won't work
        extract = dict()
        datasets = list()
        try:
            extract_h5 = h5py.File(h5_file, 'a')
        except EnvironmentError as e:
            self.print_critical(f"Couldn't open file {h5_file}: {e}")

        # Format Mesh information
        for instance_key in odb_dict['odb']['rootAssembly']['instances']:
            instance = odb_dict['odb']['rootAssembly']['instances'][instance_key]
            try:
                mesh = extract[instance['name']]['Mesh']
            except KeyError:
                try:
                    extract[instance['name']]['Mesh'] = xarray.Dataset()
                    datasets.append(f'{instance["name"]}/Mesh')
                except KeyError:
                    extract[instance['name']] = dict()
                    extract[instance['name']]['Mesh'] = xarray.Dataset()
                    datasets.append(f'{instance["name"]}/Mesh')
                mesh = extract[instance['name']]['Mesh']
            try:
                node_labels = instance['nodes']['labels']
            except KeyError:  # If the key 'nodes' is not present it is an assembly instance not a part instance
                continue
            coords = [node_labels, ['x', 'y', 'z']]
            if instance['embeddedSpace'].upper() == 'AXISYMMETRIC':
                try:
                    mesh['node_location'] = xarray.DataArray(data=instance['nodes']['coordinates'],
                                                         coords=[node_labels, ['r', 'z']],
                                                         dims=['node', 'vector'])
                except ValueError:  # If somehow the data are not 2 dimensional, use the 3 dimensional coordinates
                    mesh['node_location'] = xarray.DataArray(data=instance['nodes']['coordinates'], coords=coords,
                                                         dims=['node', 'vector'])
            else:
                mesh['node_location'] = xarray.DataArray(data=instance['nodes']['coordinates'], coords=coords,
                                                     dims=['node', 'vector'])
            del instance['nodes']  # Clear up memory now that it's stored elsewhere
            if 'elements' in instance:
                for element_key in instance['elements']:
                    element_type = instance['elements'][element_key]
                    mesh_key = f'{element_key}_mesh'
                    node_key = f'{element_key}_node'

                    length_cols = len(element_type['connectivity'][0])
                    coords = {element_key: element_type['labels'],
                              node_key: list(range(length_cols)),
                              'section_category': (element_key, element_type['section_category'])}
                    mesh[mesh_key] = xarray.DataArray(
                        data=element_type['connectivity'], coords=coords, dims=[element_key, node_key])
                del instance['elements']

        history_length = dict()
        step_names = [_ for _ in self.parsed['odb']['steps'].keys()]
        true_step_numbers = len(step_names)
        # Format history outputs
        # For history outputs, rather than do memory intensive xarray concatenations, the data has been already
        # formatted in such a way that it lends itself to building datasets and data arrays
        for instance_name in self.history_extract_format:
            for region_name in self.history_extract_format[instance_name]:
                # Get the current dataset for which to add data arrays
                try:
                    current_dataset = extract[instance_name]['HistoryOutputs'][region_name]
                except KeyError:
                    try:
                        extract[instance_name]['HistoryOutputs'][region_name] = xarray.Dataset()
                        datasets.append(f'{instance_name}/HistoryOutputs/{region_name}')
                    except KeyError:
                        try:
                            extract[instance_name]['HistoryOutputs'] = dict()
                        except KeyError:
                            extract[instance_name] = dict()
                            extract[instance_name]['HistoryOutputs'] = dict()
                        extract[instance_name]['HistoryOutputs'][region_name] = xarray.Dataset()
                        datasets.append(f'{instance_name}/HistoryOutputs/{region_name}')
                    current_dataset = extract[instance_name]['HistoryOutputs'][region_name]
                # Loop through data meant for data arrays and create data arrays
                for output_name in self.history_extract_format[instance_name][region_name]:
                    current_output = self.history_extract_format[instance_name][region_name][output_name]
                    coords = {'step': step_names, 'time': current_output['time']}
                    dims = ['step', 'time']
                    if 'node' in current_output:
                        coords['node'] = ('step', current_output['node'])
                        coords['type'] = ('step', current_output['type'])
                    elif 'element' in current_output:
                        coords['element'] = ('step', current_output['element'])
                        coords['type'] = ('step', current_output['type'])
                    else:
                        coords['type'] = ('step', current_output['type'])
                    if len(current_output['data']) != true_step_numbers:
                        current_output['data'] = current_output['data'][:true_step_numbers]

                    array_length = len(coords['type'])
                    # Get the length of the previous dataset with the current instance and region names
                    try:
                        previous_length = history_length[instance_name][region_name]
                    except KeyError:
                        try:
                            history_length[instance_name][region_name] = array_length
                        except KeyError:
                            history_length[instance_name] = dict()
                            history_length[instance_name][region_name] = array_length
                        previous_length = history_length[instance_name][region_name]

                    # If the current dataset isn't empty check if the length of the nodes/elements are the same
                    if current_dataset:
                        region_number = 1
                        new_region_name = region_name
                        while previous_length != array_length:
                            new_region_name = f'{region_name}_{region_number}'
                            try:
                                previous_length = history_length[instance_name][new_region_name]
                            except KeyError:
                                history_length[instance_name][new_region_name] = array_length
                                previous_length = history_length[instance_name][new_region_name]
                            region_number += 1
                        if region_name != new_region_name:
                            try:
                                current_dataset = extract[instance_name]['HistoryOutputs'][new_region_name]
                            except KeyError:
                                extract[instance_name]['HistoryOutputs'][new_region_name] = xarray.Dataset()
                                datasets.append(f'{instance_name}/HistoryOutputs/{new_region_name}')
                                current_dataset = extract[instance_name]['HistoryOutputs'][new_region_name]

                    # Create data array and put it in the current dataset
                    current_dataset[output_name] = xarray.DataArray(
                        data=numpy.asarray(current_output['data'], dtype='f'), coords=coords, dims=dims)
                    current_dataset[output_name].attrs['description'] = current_output['description']
        del self.history_extract_format
        del history_length

        # Format field outputs
        dataset_length = dict()
        for region_name in self.field_extract_format:
            for field_name in self.field_extract_format[region_name]:
                for instance_name in self.field_extract_format[region_name][field_name]:
                    current_output = self.field_extract_format[region_name][field_name][instance_name]
                    dims = ['step', 'time']
                    coords = {'step': step_names,
                              'time': current_output['time']}
                    position = 'elements'
                    if 'nodes' in current_output:
                        position = 'nodes'
                    coords[position] = current_output[position]
                    dims.append(position)
                    position_length = len(coords[position])
                    data = current_output['values']
                    if current_output['sectionPoint']:
                        coords['sectionPoint'] = (position, current_output['sectionPoint'])
                        if current_output['element_size'] and len(data[0][0][0]) > 1:
                            dims.append('section point')  # In this case section point would also be a dimension
                    if current_output['integrationPoint']:
                        coords['integrationPoint'] = (position, current_output['integrationPoint'])
                        if current_output['element_size'] and len(data[0][0][0]) > 1:
                            dims.append('integration point')  # In this case IP would also be a dimension

                    if len(current_output['value_names']) > 1:
                        # If there is more than one data point, value_names is another dimension
                        coords[f'{field_name} values'] = current_output['value_names']
                        dims.append(f'{field_name} values')

                    if len(data) != true_step_numbers:
                        data = data[:true_step_numbers]

                    # Get the current dataset for which to add data arrays
                    try:
                        current_dataset = extract[instance_name]['FieldOutputs'][region_name]
                    except KeyError:
                        try:
                            extract[instance_name]['FieldOutputs'][region_name] = xarray.Dataset()
                            datasets.append(f'{instance_name}/FieldOutputs/{region_name}')
                        except KeyError:
                            try:
                                extract[instance_name]['FieldOutputs'] = dict()
                            except KeyError:
                                extract[instance_name] = dict()
                                extract[instance_name]['FieldOutputs'] = dict()
                            extract[instance_name]['FieldOutputs'][region_name] = xarray.Dataset()
                            datasets.append(f'{instance_name}/FieldOutputs/{region_name}')
                        current_dataset = extract[instance_name]['FieldOutputs'][region_name]
                    # Get the length of the previous dataset with the current instance and region names
                    try:
                        previous_length = dataset_length[instance_name][region_name]
                    except KeyError:
                        try:
                            dataset_length[instance_name][region_name] = position_length
                        except KeyError:
                            dataset_length[instance_name] = dict()
                            dataset_length[instance_name][region_name] = position_length
                        previous_length = dataset_length[instance_name][region_name]

                    # If the current dataset isn't empty check if the length of the nodes/elements are the same
                    if current_dataset:
                        region_number = 1
                        new_region_name = region_name
                        while previous_length != position_length:
                            new_region_name = f'{region_name}_{region_number}'
                            try:
                                previous_length = dataset_length[instance_name][new_region_name]
                            except KeyError:
                                dataset_length[instance_name][new_region_name] = position_length
                                previous_length = dataset_length[instance_name][new_region_name]
                            region_number += 1
                        if region_name != new_region_name:
                            try:
                                current_dataset = extract[instance_name]['FieldOutputs'][new_region_name]
                            except KeyError:
                                extract[instance_name]['FieldOutputs'][new_region_name] = xarray.Dataset()
                                datasets.append(f'{instance_name}/FieldOutputs/{new_region_name}')
                                current_dataset = extract[instance_name]['FieldOutputs'][new_region_name]

                    try:
                        # Create data array and put it in the current dataset
                        current_dataset[field_name] = xarray.DataArray(data=numpy.asarray(data, dtype='f'),
                                                                       coords=coords, dims=dims)
                    except ValueError as e:
                        print(f'coords: {coords}\n')
                        print(f'dims: {dims}\n')
                        print(f'steps: {len(data)}\n')
                        print(f'time: {len(data[0])}\n')
                        print(f'{position}: {len(data[0][0])}\n')
                        print(f'element_size: {len(data[0][0][0])}\n')
                        print(f'data_items: {data[0][0][0][0]}\n')
                        raise e

        del self.field_extract_format

        non_empty_datasets = list()  # Store the names of the datasets that aren't empty
        datasets_file = Path(h5_file)
        datasets_file = datasets_file.parent / f"{datasets_file.stem}_datasets{_settings._default_h5_extension}"
        if datasets_file.exists():
            datasets_file = datasets_file.parent / f"{datasets_file.stem}_datasets_{time_stamp}" \
                                                   f"{_settings._default_h5_extension}"
        filename = str(datasets_file)
        for dataset in datasets:
            keys = dataset.split('/')  # Get instance, (Mesh|HistoryOutputs|FieldOutputs),(region name|None)
            if keys[1] == 'Mesh':
                xr_dataset = extract[keys[0]][keys[1]]
            else:
                xr_dataset = extract[keys[0]][keys[1]][keys[2]]
            # Create or append to h5 file with xarray datasets
            if xr_dataset:  # If the dataset isn't empty
                xr_dataset.to_netcdf(path=filename, mode='a', format="NETCDF4", group=dataset, engine=_settings._default_xarray_engine)
                extract_h5[dataset] = h5py.ExternalLink(filename, dataset)  # Link to datasets in file
                non_empty_datasets.append(dataset)

        extract_h5.create_group('xarray')
        extract_h5['xarray'].create_dataset('Dataset', data=numpy.asarray(non_empty_datasets, dtype='S'))
        extract_h5['xarray']['Dataset'].attrs['filename'] = filename
        # TODO: consider removing statement below, if this information is not required
        del extract  # Don't need the dictionary any more, so just remove it
        self.save_dict_to_group(extract_h5, 'odb/', odb_dict['odb'], h5_file)
        extract_h5.close()
        return None

    def save_dict_to_group(self, h5file, path, data_member, output_file):
        """Recursively save data from python dictionary to hdf5 file.

        This method can handle data types of int, float, str, and xarray Datasets, as well as lists or dictionaries of the
        aforementioned types. Tuples are assumed to have ints or floats.

        :param stream h5file: file stream to write data into
        :param str path: name of hdf5 group to write into
        :param dict data_member: member of dictionary
        :param str output_file: name of h5 output file
        """
        if not data_member:
            return
        for key, item in data_member.items():
            # Check for h5py types
            # FIXME: Make this if statement more robust by building the tuple from h5py metadata instead of hardcoded
            if isinstance(item, (h5py._hl.group.ExternalLink, h5py._hl.group.Group)):
                h5file[f'{path}{key}'] = item
            # Check everything else
            elif isinstance(item, (str, bytes)):
                try:
                    h5file.create_group(path)
                except ValueError:  # pragma: no cover
                    pass  # If group is already created, just ignore the error
                h5file[path].attrs[key] = item
            elif isinstance(item, list):
                if all(isinstance(x, (str, bytes)) for x in item):
                    h5file.create_dataset(f'{path}/{key}', data=numpy.array(item, dtype='S'))
                elif all(isinstance(x, int) for x in item):
                    h5file.create_dataset(f'{path}/{key}', data=numpy.array(item))
                elif all(isinstance(x, float) for x in item):
                    h5file.create_dataset(f'{path}/{key}', data=numpy.array(item, dtype=numpy.float64))
                else:
                    for index, list_item in enumerate(item):
                        if isinstance(list_item, (str, bytes)):
                            h5file[f'{path}{key}/{index}'] = list_item
                        elif isinstance(list_item, int):
                            h5file[f'{path}{key}/{index}'] = numpy.int64(list_item)
                        elif isinstance(list_item, float):
                            h5file[f'{path}{key}/{index}'] = numpy.float64(list_item)
                        elif isinstance(list_item, dict):
                            self.save_dict_to_group(h5file, f'{path}{key}/{index}/', list_item, output_file)
            elif isinstance(item, int):
                try:
                    h5file.create_group(path)
                except ValueError:  # pragma: no cover
                    pass  # If group is already created, just ignore the error
                h5file[path].attrs[key] = numpy.int64(item)
            elif isinstance(item, float):
                try:
                    h5file.create_group(path)
                except ValueError:  # pragma: no cover
                    pass  # If group is already created, just ignore the error
                h5file[path].attrs[key] = numpy.float(item)
            elif isinstance(item, tuple):
                if item:
                    if isinstance(item[0], (str, bytes)):
                        h5file[f'{path}{key}'] = numpy.array(item, dtype='S')
                    else:
                        h5file[f'{path}{key}'] = numpy.array(item)
            elif isinstance(item, dict):
                self.save_dict_to_group(h5file, f'{path}{key}/', item, output_file)
            elif isinstance(item, xarray.core.dataset.Dataset) or isinstance(item, xarray.core.dataarray.DataArray):
                item.to_netcdf(path=output_file, mode='a', format="NETCDF4", group=f'{path}{key}/', engine=_settings._default_xarray_engine)
                # TODO: In future additions of xarray, consider using option 'invalid_netcdf=True'
            else:
                raise ValueError(f'Cannot save {type(item)} type to hdf5 file.')
