### IMPORTS ###
from abc import ABC, abstractmethod

class default_module(ABC):
	def __init__(self, *args):
		self.commands = {}
		self.restriction = {}
		self.arguments = {}
		self.description = {}

	def get_commands(self):
		return self.commands
	def get_args(self, command):
		return self.arguments[command] if command in self.arguments else ""
	def get_desc(self, command):
		return self.description[command] if command in self.description else ""
	def get_restriction(self, command):
		return self.restriction[command] if command in self.restriction else 0


	### COMMAND FUNCTIONS ###

	#def example(self, *args):
		#if len(args) > 0:
			#return (1,"example PASS")
		#else:
			#return (0,"example FAIL")

	### END COMMAND FUNCTIONS ###