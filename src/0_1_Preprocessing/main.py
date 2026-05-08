#!/garnet2/Tools/META_Analysis/Tools/miniconda3/bin/python3

import argparse
from src.preprocessing import DataPreprocessor
import os
import sys

def split_comma(value):
	return [item.strip() for item in value.split(',')] if value else []

def parse_arguments():
	parser = argparse.ArgumentParser(description="META Statistics Analysis Preprocessing")
	
	# Preprocessing
	parser.add_argument("-t", "--type", type=str, required=True, choices=['asv','read-based','mag'])
	parser.add_argument("-adiv", type=str, help="Alpha divesity table (e.g., alpha_diveristy.txt)")
	parser.add_argument("-it", "--input_tax", type=split_comma, help="Taxonomy file(s) (Auto-detected by name).")
	parser.add_argument("-if", "--input_func", type=split_comma, help="Functional DB file(s).(e.g, uniref90_eggnog_eggnog.tsv,uniref90_pfam.tsv)")
	parser.add_argument("-ic", "--input_custom", type=split_comma, help="Custom input files")
	parser.add_argument("-m" , "--metadata", type= str, required=True, help="Metadata file (#Sample\tGroup)")
	parser.add_argument("-o", "--output", default="preprocessing", help="Output directory (default: preprocessing)")
	return parser.parse_args()

def validate_args(args):
	tax_keywords = [
		'phylum', 'class', 'order', 'family', 'genus', 'species',
		'l2', 'l3', 'l4', 'l5', 'l6', 'l7', 'l8', 'mag', 'asv'
	]
	
	if args.input_tax:
		found_levels = []
		for path in args.input_tax:
			filename = os.path.basename(path).lower()
			matched = [k for k in tax_keywords if k in filename]

			if not matched:
				print(f"Error: Cannot identify taxonomy level from filename: '{os.path.basename(path)}'")
				print(f"Filename must contain one of: {tax_keywords}")
				sys.exit(1)
			level = matched[0]

			if level == 'mag' and args.type != 'mag':
				print(f"Error: File '{os.path.basename(path)}' (mag) is only allowed for '--type mag'.")
				sys.exit(1)
			if level == 'asv' and args.type != 'asv':
				print(f"Error: File '{os.path.basename(path)}' (asv) is only allowed for '--type asv'.")
				sys.exit(1)

			found_levels.append(level)

		print(f"[*] Detected Taxonomy Levels: {', '.join(found_levels)}")

	if not any([args.input_tax, args.input_func, args.adiv, args.input_custom]):
		print("Error: No input files provided. Use -it, -if, -adiv, or -ic.")
		sys.exit(1)

	if not os.path.exists(args.metadata):
		print(f"Error: Metadata file not found: {args.metadata}")
		sys.exit(1)

def main():
	args = parse_arguments()
	validate_args(args)
	
	preprocessor = DataPreprocessor(args)
	preprocessor.execute()

if __name__ == "__main__":
	main()

