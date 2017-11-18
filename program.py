import json
import sys


patterns = []

tainted = {}

entrypoints = {}
sanitization = {} 
sensitive = {}
query = {}

paragraph = -1

def assign(i):
	if i['right']['kind'] == "offsetlookup": #assign -> offsetlookup

			entrypoints[i['left']['name']] = i['right']['what']['name']
			tainted[i['left']['name']] = isTainted(i['right']['what']['name'])

	if i['right']['kind'] == "encapsed": #assign -> encapsed
		query[i['left']['name']] = []
		
		for j in i['right']['value']:
			
			if j['kind'] == "variable":
				query[i['left']['name']].append(j['name'])
				
				if isTainted(j['name']):
					tainted[i['left']['name']] = True	
					
				else: 
					tainted[i['left']['name']] = False

	if i['right']['kind'] == "bin": #assign -> bin
		query[i['left']['name']] = []
		
		if i['right']['left']['kind'] == "variable":
			query[i['left']['name']].append(i['right']['left']['name'])

		if i['right']['right']['kind'] == "variable":
			query[i['left']['name']].append(i['right']['right']['name'])

		if isTainted(i['right']['right']['name']):
			tainted[i['left']['name']] = tainted[i['right']['right']['name']]
		elif isTainted(i['right']['left']['name']):
			tainted[i['left']['name']] = tainted[i['right']['left']['name']]


	if i['right']['kind'] == "call": #assign -> call
		sensitive[i['right']['what']['name']] = []
		sanitization[i['right']['what']['name']] = []

		for j in i['right']['arguments']:

			if j['kind'] == "variable":

				if patternScanner(i['right']['what']['name'],1) == 3: #sensitive sink
					sensitive[i['right']['what']['name']].append(j['name'])
					del sanitization[list(sanitization)[0]] #delete all the non 

					if isTainted(j['name']):
						tainted[i['right']['what']['name']] = True
						#means that the variable used in the sink is tainted ==> vulnerable
						#it is necessary to see if the entry point corresponds with the sink


					if paragraph != -1:  #means that exists sanitization previously 
						if i['right']['what']['name'] in patterns[paragraph][3]:
							print "Not vulnerable due to the sanitization function: " + str(list(sanitization)[0])
							sys.exit(0)

				if patternScanner(i['right']['what']['name'],1) == 2: #sanitization
					print str(i['right']['what']['name']) + " ++++++++ ESARARADEFF " + str(j['name'])
					sanitization[i['right']['what']['name']].append(j['name'])
					global paragraph
					paragraph = patternScanner(i['right']['what']['name'],3) #saves the paragraph number 
					print "ASADSFSGGFG      " + str(paragraph)
					
					tainted[i['left']['name']] = False

	if i['right']['kind'] == "variable": #assign -> variable
		query[i['left']['name']] = [i['right']['name']]
		if isTainted(i['right']['name']):
			tainted[i['left']['name']] = True
			recursiveVariables(i['left']['name'])
		else:
			tainted[i['left']['name']] = False


def isIf(i, recursion):
	for line in i['body']['children']:
		if line['kind'] == "assign":
			query[line['left']['name']] = []
			
			if line['right']['kind'] == "encapsed":

				for j in line['right']['value']:

					if j['kind'] == "variable":
						query[line['left']['name']].append(j['name'])
						if isTainted(j['name']):
							tainted[line['left']['name']] = tainted[j['name']]

	if recursion == True:
		if i['alternate']:
			isIf(i['alternate'], True)

	else:
		for line in i['alternate']['children']:
			if line['right']['kind'] == "encapsed":
				query[line['left']['name']] = []

				if line['right']['kind'] == "encapsed":

					for j in line['right']['value']:

						if j['kind'] == "variable":
							query[line['left']['name']].append(j['name'])
							if isTainted(j['name']):
								tainted[line['left']['name']] = tainted[j['name']]

def call(i):
	sensitive[i['what']['name']] = []

	for j in i['arguments']:
		if j['kind'] == "variable":
			sensitive[i['what']['name']].append(j['name'])

def echo(i):
	sensitive[i['kind']] = [i['arguments'][0]['what']['name']]
	tainted[i['arguments'][0]['what']['name']] = True

def isWhile(i):
	if i['body']: #while -> body
		for j in i['body']['children']:
			if j['kind'] == "assign": #assign
				assign(j)

			if j['kind'] == "if": #if
				isIf(j, True)

			if j['kind'] == "call": #if
				call(j)

def isTainted(var):

	if tainted.has_key(var) and tainted[var]:
		return True

	else:
		return patternScanner(var,2)

def patternScanner(value, mode):

	if mode == 1: 
		for group in patterns:

			for line in group:

				for field in line:

					if field == value:
						return group.index(line)

	elif mode == 2:
		for group in patterns:

			for line in group:

				for field in line:

					if field == value:
						return True

		return False

	else: 
		for group in patterns:

			for line in group:

				for field in line:

					if field == value:
						return patterns.index(group)

def recursiveVariables(var):
	for i in query.keys():
		for j in query.get(i):
			if j == var and tainted.has_key(i):
				tainted[i] = tainted[j]
				recursiveVariables(i)

def patternInicialization(filepath):

	patternFile = open(filepath, "r")

	i = 1
	name = ""
	aux = []
	for line in patternFile:
		if i == 1:
			name = line.rstrip()
			aux.append([name])
		if i == 2:
			aux2 = []
			for j in line.rstrip().split(','):
				aux2.append(j[1:])
			aux.append(aux2)
		if i == 3:
			aux2 = []
			for j in line.rstrip().split(','):
				aux2 = []
				aux2.append(j)
			aux.append(aux2)
		if i == 4:
			aux2 = []
			for j in line.rstrip().split(','):
				aux2.append(j)
			aux.append(aux2)
			patterns.append(aux)
			aux = []
			i = -1
		i = i + 1

def astAnalyser(astFilepath, patternsFilepath):

	patternInicialization(patternsFilepath)

	JSONslice = open(astFilepath, "r")
	json_data = json.load(JSONslice)

	for i in json_data['children']:

		if i['kind'] == "assign": #assign
			assign(i)
			
		if i['kind'] == "call": #call
			call(i)

		if i['kind'] == "echo": #echo
			echo(i)

		if i['kind'] == "while": #while
			isWhile(i)
			
		if i['kind'] == "if": #if
			isIf(i, False)


	print(entrypoints)
	print(sensitive)
	print(query)
	print(tainted)

astAnalyser(sys.argv[1], "vulnPatterns.txt")

