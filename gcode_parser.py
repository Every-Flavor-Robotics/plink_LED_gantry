#!/usr/bin/env python3
"""
File: gcode_parser.py

Description:
    This module provides functionality for parsing G-code commands from files or streams.
    It contains two main classes:

    1. StatefulParams:
       - A helper class that maintains a stateful dictionary of parameters.
       - Useful for storing and retrieving parameter values in a consistent way.

    2. GCodeParser:
       - The primary class responsible for parsing G-code commands.
       - Supports registering callback functions for specific commands (e.g., "G0", "G1").
       - Provides two failure modes: "error" (raises an exception if an unregistered command is encountered)
         and "ignore" (skips unregistered commands).

Usage Guide:
    1. Create an instance of GCodeParser:
           parser = GCodeParser(failure_mode="error")
       The failure_mode parameter determines how the parser behaves when encountering an
       unregistered command.

    2. Register callback functions for commands:
           def g0_callback(command, params):
               print(f"G0: Command: {command}, Params: {params}")

           parser.register_callback("G0", g0_callback)
       Callbacks are functions that receive the command and a dictionary of parameters.

    3. Parse G-code lines:
           with open("test.gcode", "r") as f:
               lines = f.readlines()

           parser.parse_lines(lines)
       Each line in the G-code file is processed to extract the command and its parameters,
       and the corresponding callback is invoked.

    4. Handling different command formats:
       The parser normalizes commands so that, for example, "G01" and "G1" are treated equivalently.

Note:
    G-code commands usually start with a letter (e.g., G or M) followed by numerical values.
    The parser splits the command from its parameters based on spaces and then further processes
    each part to extract keys and values.

"""


class StatefulParams:
    """
    A class for managing a collection of parameters in a stateful manner.

    Attributes:
        params (dict): Dictionary holding parameter keys and their corresponding values.
    """

    def __init__(self):
        """
        Initialize a new instance of StatefulParams with an empty parameter dictionary.
        """
        self.params = {}

    def set_param(self, key, value):
        """
        Set a parameter in the dictionary.

        Args:
            key (str): The parameter key.
            value (Any): The value associated with the key.
        """
        self.params[key] = value

    def get_param(self, key):
        """
        Retrieve the value of a specified parameter.

        Args:
            key (str): The parameter key to retrieve.

        Returns:
            Any: The value associated with the provided key.

        Raises:
            KeyError: If the key is not found in the parameters.
        """
        return self.params[key]

    def remove_param(self, key):
        """
        Remove a parameter from the dictionary.

        Args:
            key (str): The parameter key to remove.

        Raises:
            KeyError: If the key does not exist in the parameters.
        """
        del self.params[key]


class GCodeParser:
    """
    A parser for processing G-code command lines with support for user-defined callbacks.

    Attributes:
        callbacks (dict): A mapping from normalized G-code commands to callback functions.
        failure_mode (str): Determines behavior when encountering an unregistered command.
                            Valid values are "error" (raises an exception) or "ignore" (skips).
    """

    def __init__(self, failure_mode="error"):
        """
        Initialize the GCodeParser.

        Args:
            failure_mode (str, optional): Mode for handling unregistered commands. Must be either "error" or "ignore".
                                          Defaults to "error".

        Raises:
            ValueError: If failure_mode is not "error" or "ignore".
        """
        # Initialize a dictionary for command callbacks.
        self.callbacks = {}

        # Validate failure_mode parameter.
        if failure_mode != "error" and failure_mode != "ignore":
            raise ValueError("failure_mode must be either 'error' or 'ignore'")
        self.failure_mode = failure_mode

    def register_callback(self, command, callback):
        """
        Register a callback function for a specific G-code command.

        Args:
            command (str): The G-code command for which the callback should be registered.
                           Must start with either "M" or "G".
            callback (callable): The function to execute when the command is encountered.
                                 It should accept two parameters: command (str) and params (dict).

        Raises:
            ValueError: If the command does not start with "M" or "G".
        """
        # Clean and normalize the command.
        command = self._clean_command(command)

        # Validate the command prefix.
        if command[0] != "M" and command[0] != "G":
            raise ValueError("Command must be either 'M' or 'G'")

        # Register the callback for the cleaned command.
        self.callbacks[command] = callback

    def parse_line(self, line):
        """
        Parse a single line of G-code and execute the corresponding callback if registered.

        Args:
            line (str): A line of G-code containing a command and its parameters.

        Raises:
            ValueError: If the command is unregistered and failure_mode is "error".
        """
        # Extract the command and parameters from the line.
        command = self._extract_command(line)
        params = self._extract_params(line)

        # Check if the command has a registered callback.
        if command in self.callbacks:
            # Execute the registered callback with the command and parameters.
            self.callbacks[command](command, params)
        else:
            # Handle unregistered commands based on failure_mode.
            if self.failure_mode == "error":
                raise ValueError(f"Command {command} not registered")
            else:
                # In "ignore" mode, simply do nothing.
                pass

    def parse_lines(self, lines):
        """
        Parse multiple lines of G-code.

        Args:
            lines (iterable): An iterable of G-code lines (e.g., a list of strings).

        Each line is processed individually using parse_line.
        """
        for line in lines:
            self.parse_line(line)

    def _clean_command(self, command):
        """
        Clean and normalize a G-code command string.

        This method strips extra whitespace, converts the command to uppercase,
        and normalizes commands such as "G01" to "G1" by collapsing the numerical part.

        Args:
            command (str): The raw command string.

        Returns:
            str: The normalized command string.
        """
        command = command.strip().upper()

        # Normalize commands like "G01" to "G1" (i.e., collapse "0" in the middle if present)
        if len(command) == 3 and command[1] == "0":
            command = command[0] + command[2]

        return command

    def _extract_command(self, line):
        """
        Extract the G-code command from a line.

        Args:
            line (str): A line of G-code containing a command and its parameters.

        Returns:
            str: The normalized command extracted from the line.
        """
        # Split the line by spaces and clean the first segment as the command.
        command = self._clean_command(line.split(" ")[0])
        return command

    def _extract_params(self, line):
        """
        Extract the parameters from a G-code line.

        Args:
            line (str): A line of G-code containing a command and its parameters.

        Returns:
            dict: A dictionary mapping parameter keys to their values.

        Details:
            - The line is split by spaces.
            - The first token is assumed to be the command.
            - Remaining tokens are parameters in the form "X123", "Y456", etc.
            - Each parameter is split into a key (first character) and a value (the remainder).
        """
        # Split the line into tokens; first token is the command.
        params = line.split(" ")[1:]
        param_dict = {}

        # Process each parameter token.
        for param in params:
            param = param.strip().upper()
            if not param:
                continue

            # Assume the first character is the key and the rest is the value.
            key = param[0]
            value = param[1:]
            param_dict[key] = value

        return param_dict


# Example usage
if __name__ == "__main__":
    # Create a parser instance with error failure mode.
    test_parser = GCodeParser()

    # Define callback functions for specific commands.
    def g0_callback(command, params):
        """
        Callback function for the G0 command.

        Args:
            command (str): The G-code command (expected to be "G0").
            params (dict): A dictionary of parameters for the command.
        """
        print(f"G0: Command: {command}, Params: {params}")

    def g1_callback(command, params):
        """
        Callback function for the G1 command.

        Args:
            command (str): The G-code command (expected to be "G1").
            params (dict): A dictionary of parameters for the command.
        """
        print(f"G1: Command: {command}, Params: {params}")

    # Register the callbacks with the parser.
    test_parser.register_callback("G0", g0_callback)
    test_parser.register_callback("G1", g1_callback)

    # Open a sample G-code file and read its lines.
    with open("test.gcode", "r") as f:
        lines = f.readlines()

    # Parse each line in the file.
    test_parser.parse_lines(lines)
