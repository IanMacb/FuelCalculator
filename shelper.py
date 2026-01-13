import ast
import readline


class SHelper(object):
    def __init__(self):
        self.cmds = {}
        self.toplv_cmds = []
        self.init_cmds()
        print(str(self.__class__.__name__) + " initialized.")

    def parse_command(self, cmd_string):
        """
        Accepts a string, tokenizes, and matches to a command, passing args.

        :param cmd_string: Command received as a string.
        """
        if cmd_string.strip() == "":
            return ""
        try:
            args = cmd_string.strip().split(" ")
            command = args[0]
            args.pop(0)

            evaled = []
            for arg in args:
                try:
                    evaled.append(ast.literal_eval(arg))
                except Exception as ie:
                    evaled.append(str(arg))

            if command.lower() in self.cmds.keys():
                r = self.cmds[command.lower()](*args)
                return r
            else:
                raise KeyError('Command "' + command + '" not found.')
        except Exception as e:
            print(e)
            return e

    def init_cmds(self):
        self.cmds = {}
        for method in dir(self):
            if method.startswith("toplevel_cmd"):
                command = method[13:]
                m = getattr(self, method)
                self.cmds[command] = m
                self.toplv_cmds.append(command)
            elif method.startswith("cmd_"):
                command = method[4:]
                m = getattr(self, method)
                self.cmds[command] = m

    def cmd_help(self, arg=None):
        # TODO Simple service help
        """Print the help dialogue for this service"""

        robot_string = ""
        human_string = ""

        human_string += "-" * 40 + "\n"
        human_string += self.__class__.__name__ + "\n"
        human_string += self.__class__.__doc__ + "\n"
        human_string += "-" * 40 + "\n"

        robot_string += "COMMANDS:"
        for cmd, boundmeth in self.cmds.items():
            robot_string += " " + cmd
            if boundmeth.__doc__ is not None:
                human_string += cmd + ": " + boundmeth.__doc__ + "\n"
            else:
                human_string += cmd + "\n"
        return human_string

    def restart(self):
        """Overload method to return a new instance of self with contextual data of running stuff"""
        return None

    def cleanup(self):
        pass

    def disconnect_notification(self, address=None):
        pass
