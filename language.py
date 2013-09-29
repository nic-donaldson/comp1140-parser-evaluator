import re
import sys

# parser+evaluator for toy comp1140 language
# Program ::= Statement*
# Statement ::= {Do | Print} ";"
# Print ::= "print" Value
# Do ::= "do" "{" Statement* "}" Number "times"
# Value := String | Number
# String ::= "`" [a-zA-Z]* "'"
# Number ::= [0-9]*

# Sample program:
# do {
# print `welcome';
# print 1140;
# } 15 times;

sample_p = """do {
print  'welcome';
print 1140;
} 15 times;"""

sample_p2 = """do {
    print 'firstloop';
    do {
        print 'secondloop';
    } 2 times;
} 5 times;"""

class Rules():
	Program = 1
	Statement = 2
	Print = 3
	Do = 4
	Value = 5
	String = 6
	Number = 7


class RoseTree:
	def __init__(self, value=None):
		self.children = []
		self.value = value

class ParseTree(RoseTree):
	def __init__(self,value=None,parent=None):
		RoseTree.__init__(self,value)
		self.parent = parent

	def insert(self, value):
		self.children.append(ParseTree(value,self))

	def __repr__(self):
		if self.children == []:
			return str(self.value)
		else:
			result = str(self.value) + ":\n"
			
			for child in self.children:
				child_str = ""
				child_str += str(child)
				for line in child_str.split("\n"):
					result += "\t" + line + "\n"

			return result.strip()


# class to generate a parse tree for the given language
class Parser:
	tokenstring = r";|print|do|{|}|times|'|[a-zA-z]+|[0-9]+"
	token_re = re.compile(tokenstring)
	string_re = re.compile(r"[a-zA-z]+")
	number_re = re.compile(r"[0-9]*")
	tokens = []
	parse_tree = ParseTree()
	parse_tree_pointer = parse_tree

	def parse(self, program):
		self.tokens = re.findall(Parser.token_re, program);
		#print(self.tokens)
		self.parse_program()

	def parse_program(self):
		self.parse_tree.insert(Rules.Program)
		self.parse_tree_pointer = self.parse_tree.children[-1]
		#print("Parse_program: " + str(self.tokens))
		while len(self.tokens) > 0:
			self.parse_statement()

	def parse_statement(self):
		#print("Parse statement: " + str(self.tokens))
		self.parse_tree_pointer.insert(Rules.Statement)
		statement_pointer = self.parse_tree_pointer

		self.parse_tree_pointer = self.parse_tree_pointer.children[-1]
		if self.tokens[0] == "do":
			self.parse_tree_pointer.insert(Rules.Do)
			self.parse_tree_pointer = self.parse_tree_pointer.children[-1]

			self.parse_do()

		elif self.tokens[0] == "print":
			self.parse_tree_pointer.insert(Rules.Print)
			self.parse_tree_pointer = self.parse_tree_pointer.children[-1]

			self.parse_print()

		else:
			raise Exception("Expected a statement token, got " + str(self.tokens)[0])

		self.parse_literal(";")

		self.parse_tree_pointer = statement_pointer

	def parse_do(self):
		#print("Parse do: " + str(self.tokens))
		self.parse_literal("do")
		self.parse_literal("{")

		while self.tokens[0] is not "}":
			self.parse_statement()

		self.parse_literal("}")
		self.parse_number()
		self.parse_literal("times")

	def parse_print(self):
		#print("Parse print " + str(self.tokens))
		self.parse_literal("print")
		self.parse_tree_pointer.insert(Rules.Value)

		value_pointer = self.parse_tree_pointer
		self.parse_tree_pointer = self.parse_tree_pointer.children[-1]

		self.parse_value()
		self.parse_tree_pointer = value_pointer

	def parse_value(self):
		pointer = self.parse_tree_pointer

		if self.tokens[0] == "'":
			self.parse_tree_pointer.insert(Rules.String)
			self.parse_tree_pointer = self.parse_tree_pointer.children[-1]
			self.parse_string()
		else:
			self.parse_tree_pointer.insert(Rules.Number)
			self.parse_tree_pointer = self.parse_tree_pointer.children[-1]
			self.parse_number()

		self.parse_tree_pointer = pointer

	def parse_literal(self, value):
		#print("parse literal(" + value + "): " + str(self.tokens))
		if self.tokens[0] == value:
			self.parse_tree_pointer.insert(value)
			self.tokens = self.tokens[1:]
		else:
			raise Exception("Expected literal " + value + ", got " + str(self.tokens)[0])

	def parse_string(self):
		#print("Parse string: " + str(self.tokens))
		self.parse_literal("'")
		re_match = re.match(self.string_re, self.tokens[0])
		if re_match == None:
			raise Exception("Expected string, got " + str(self.tokens)[0])

		self.parse_tree_pointer.insert(re_match.group(0))
		
		self.tokens = self.tokens[1:]
		self.parse_literal("'")

	def parse_number(self):
		#print("parse number: " + str(self.tokens))
		re_match = re.match(self.number_re, self.tokens[0])
		if re_match == None:
			raise Exception("Expected number, got " + str(self.tokens)[0])

		self.parse_tree_pointer.insert(int(re_match.group(0)))
		self.tokens = self.tokens[1:]

class Evaluator:
	def evaluate(self, parse_tree):
		#print("Evaluate")
		return self.evaluate_program(parse_tree.children[0]).strip()

	def evaluate_program(self, parse_tree):
		#print("Evaluate program")
		result = ""
		for child in parse_tree.children:
			result += self.evaluate_statement(child)
		return result

	def evaluate_statement(self, parse_tree):
		#print("Evaluate statement")
		result = ""
		for child in parse_tree.children:
			if child.value == Rules.Do:
				result += self.evaluate_do(child)
			elif child.value == Rules.Print:
				result += self.evaluate_print(child)
		return result

	def evaluate_do(self, parse_tree):
		#print ("Evaluate do")
		#print(parse_tree)
		result = ""
		# get the number of times to repeat
		times = parse_tree.children[-3].value

		while (times > 0):
			times -= 1
			for child in parse_tree.children[2:]:
				if child.value == Rules.Statement:
					result += self.evaluate_statement(child)
				else:
					break
		return result

	def evaluate_print(self, parse_tree):
		#print("Evaluate print")
		result = ""
		for child in filter((lambda x: x.value == Rules.Value), parse_tree.children):
			result += self.evaluate_value(child) + "\n"
		return result

	def evaluate_value(self, parse_tree):
		#print("Evaluate value:\n" + str(parse_tree))
		if parse_tree.children[0].value == Rules.Number:
			return str(parse_tree.children[0].children[0].value)
		else:
			return parse_tree.children[0].children[1].value



if __name__ == "__main__":
	#x = Parser()
	#x.parse(sample_p2)
	#evaluator = Evaluator()
	#print(evaluator.evaluate(x.parse_tree))
	
	program = ""
	for line in sys.stdin:
		program += line
	x = Parser()
	x.parse(program)
	evaluator = Evaluator()
	print(evaluator.evaluate(x.parse_tree))