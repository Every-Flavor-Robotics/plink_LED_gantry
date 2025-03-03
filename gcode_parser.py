class StatefulParams:

    def __init__(self):
        self.params = {}

    def set_param(self, key, value):
        self.params[key] = value

    def get_param(self, key):
        return self.params[key]

    def remove_param(self, key):
        del self.params[key]


class GCodeParser:

    def __init__(self, failure_mode="error"):
        # Callback functions that the user can register to execute the GCode commands
        self.callbacks = {}

        # Either "error" or "ignore"
        # Confirm that failure_mode is either "error" or "ignore"
        if failure_mode != "error" and failure_mode != "ignore":
            raise ValueError("failure_mode must be either 'error' or 'ignore'")
        self.failure_mode = failure_mode

    def register_callback(self, command, callback):
        # Confirm that the command is either "M*" or "G*"
        command = self._clean_command(command)

        if command[0] != "M" and command[0] != "G":
            raise ValueError("Command must be either 'M' or 'G'")

        # Register the callback function
        self.callbacks[command] = callback

    def parse_line(self, line):
        # Extract the command from the line
        command = self._extract_command(line)
        params = self._extract_params(line)

        # If the command is in the callbacks, execute the callback
        if command in self.callbacks:
            self.callbacks[command](command, params)
        else:
            # If the command is not in the callbacks, raise an error or ignore
            if self.failure_mode == "error":
                raise ValueError(f"Command {command} not registered")
            else:
                pass

        return

    def parse_lines(self, lines):

        # Parse each line
        for line in lines:
            self.parse_line(line)

    def _clean_command(self, command):
        command = command.strip().upper()

        # Make sure that 01 and 1 are treated as the same command
        # For example, G01 and G1 are the same command
        # Collapse numerical commands to the single digit
        if len(command) == 3 and command[1] == "0":
            command = command[0] + command[2]

        return command

    def _extract_command(self, line):
        # Extract the command from the line
        command = self._clean_command(line.split(" ")[0])

        return command

    def _extract_params(self, line):
        # Extract the parameters from the line
        params = line.split(" ")[1:]

        # Create a dictionary of the parameters
        param_dict = {}
        for param in params:
            param = param.strip().upper()

            key = param[0]
            value = param[1:]
            param_dict[key] = value

        # Return a dictionary of the parameters
        return param_dict


if __name__ == "__main__":

    test_parser = GCodeParser()

    def g0_callback(command, params):
        print(f"G0: Command: {command}, Params: {params}")

    def g1_callback(command, params):
        print(f"G1: Command: {command}, Params: {params}")

    test_parser.register_callback("G0", g0_callback)
    test_parser.register_callback("G1", g1_callback)

    with open("test.gcode", "r") as f:
        lines = f.readlines()

    test_parser.parse_lines(lines)
