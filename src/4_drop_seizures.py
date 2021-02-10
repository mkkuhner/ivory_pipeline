#!/usr/bin/env python
"""
Filters seizure analysis file for heatmap purposes
Input: Seizure analysis file
       Seizure name file: which seizures to keep (e.g. list of forest seiz, savannah seiz)
"""

import argparse

def run(input_file, seizure_file):
    rem = []
    with open(seizure_file, 'r') as infile:
        for line in infile:
            line = line.strip().strip('"')
            rem.append(line)
    outf = input_file.strip('txt') + 'reduced.txt'
    with open(input_file, 'r') as infile:
        with open(outf, 'w') as outfile:
            header = infile.readline()
            outfile.write(header)
            for line in infile:
                line1 = line.strip().split('\t')
                s1 = line1[0]
                s2 = line1[1]
                if s1 not in rem or s2 not in rem:
                    continue
                outfile.write(line)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--input_file', 
        help='Name of input LR_file')
    parser.add_argument('--seizure_file',
        help='Name of seizures to keep file')
    args = parser.parse_args()
    run(args.input_file, args.seizure_file)
