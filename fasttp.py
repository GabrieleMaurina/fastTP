#!/usr/bin/env python3

import dext
from os import walk, makedirs
from os.path import join, exists, relpath
from argparse import ArgumentParser as arg_par
from hashlib import sha1
from json import load, dump
from itertools import chain
from collections import deque
from sys import stdout, stderr

FOLDER = '.fasttp'

def sha1_file(path):
	with open(path, 'rb') as file:
		return sha1(file.read()).hexdigest()

def load_hashes(path):
	try:
		with open(join(path, FOLDER, 'hashes.json'), 'r') as hashes:
			return load(hashes)
	except:
		return {}

def fasttp_dir(path):
	path = join(path, FOLDER)
	if not exists(path):
    		try:
        		makedirs(path)
    		except: pass
	return path

def dump_json(path, name, obj):
	with open(join(fasttp_dir(path), name + '.json'), 'w') as file:
		dump(obj, file)	

def get_files(path, profile):
	for root, dirs, names in walk(path):
		dirs[:] = [d for d in dirs if d[0] != '.']
		for name in names:
			full = join(root, name)
			splt = name.rsplit('.', 1)
			if len(splt) == 2:
				name, ext = splt
				if ext in profile:
					yield full

def get_dependencies(profile, inputs, project_folder):
	dependencies = {}
	files, count = dext.extract(profile, inputs)
	for deps, items in files.values():
		if deps:
			for path1, ext1, src1 in items:
				path1 = relpath(path1, project_folder)
				dependencies[path1] = []
				for dep in deps:
					for path2, ext2, src2 in files[dep][1]:
						dependencies[path1].append(relpath(path2, project_folder))
	return dependencies

def dfs_changed(test, dependencies, changed):
	neighbors = deque(dependencies.get(test, []))
	visited = set(test)
	while neighbors:
		neighbor = neighbors.pop()
		if neighbor not in visited:
			visited.add(neighbor)
			if neighbor in changed:
				return True
			elif neighbor in dependencies:
				neighbors.extend(dependencies[neighbor])
	return False

def score_test(test, dependencies, changed):
	number_changed_dep, len_shortest_path, avg_len_shortest_paths = bfs(test, dependencies, changed)
	score = model(number_changed_dep, len_shortest_path, avg_len_shortest_paths)
	return score

def rank(tests, dependencies, changed):
	ranked = ((score_test(test), test) for test in tests)
	return sorted(ranked)

def tp(language, project_folder, test_folder, source_folder):
	profile = dext.get_profile(language)

	test_folder = join(project_folder, test_folder)
	source_folder = join(project_folder, source_folder)

	test_files = [relpath(file, project_folder) for file in get_files(test_folder, profile)]
	source_files = [relpath(file, project_folder) for file in get_files(source_folder, profile)]

	old_hashes = load_hashes(project_folder)
	new_hashes = {file:sha1_file(join(project_folder, file)) for file in chain(test_files, source_files)}

	changed = {file for file, hash in new_hashes.items() if file not in old_hashes or new_hashes[file] != old_hashes[file]}
	inputs = [test_folder, source_folder] if test_folder != source_folder else [test_folder]
	dependencies = get_dependencies(profile, inputs, project_folder)
	ranked = rank(test_files, dependencies, changed)	
	
	return ranked, dependencies, changed, new_hashes, test_files, source_files

def save_jsons(project_folder, ranked, dependencies, changed, new_hashes):
	dump_json(project_folder, 'ranked', ranked)
	dump_json(project_folder, 'dependencies',  dependencies)
	dump_json(project_folder, 'changed',  list(changed))
	dump_json(project_folder, 'hashes',  new_hashes)

def print_results_file(ranked, output):
	for score, test_file in ranked:
		print(score, test_file, file=output)

def print_results(ranked, output):
	if output:
		with open(output, 'w') as output:
			print_results_file(ranked, output)
	else:
		print_results_file(ranked, stdout)

def log(dependencies, changed, test_files, source_files):
	T = len(test_files)
	S = len(source_files)
	C = len(changed)
	D = sum(len(v) for v in dependencies.values())
	print('***Fasttp results***\nTest files: {}\nSource files: {}\nChanged: {}\nDependencies: {}'.format(T, S, C, D), file=stderr)

def run(language, project_folder, test_folder, source_folder, verbose, output):
	ranked, dependencies, changed, new_hashes, test_files, source_files = tp(language, project_folder, test_folder, source_folder)

	save_jsons(project_folder, ranked, dependencies, changed, new_hashes)

	if output != '': print_results(ranked, output)

	if verbose: log(ranked, dependencies, changed, test_files, source_files)

def parse_args():
	parser = arg_par(prog= 'python -m fasttp', description='Fasttp performs test case prioritization. Given a codebase that has changed, it rankes test cases according to their risk of revealing a fault. Find out more at https://github.com/GabrieleMaurina/fasttp')
	parser.add_argument('-v', '--verbose', action='store_true', help='increase output verbosity')
	parser.add_argument('-l', metavar='<lang profile>', default='all', help='set language profile (default "all")')
	parser.add_argument('-p', metavar='<project folder>', default='.', help='set project folder (default "current working directory")')
	parser.add_argument('-t', metavar='<test folder>', default='', help='set test folder relative to <project folder> (default same as <project folder>)')
	parser.add_argument('-s', metavar='<source folder>', default='', help='set source folder relative to <project folder> (default same as <project folder>)')
	parser.add_argument('-o', metavar='<output>', nargs='?', default='', help='set output file (default "stdout")')
	args = parser.parse_args()
	return args

def main():	
	args = parse_args()
	run(args.l, args.p, args.t, args.s, args.verbose, args.o)

if __name__ == '__main__':
	main()
