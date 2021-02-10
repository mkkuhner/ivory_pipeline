#!/usr/bin/env python
"""
Add seizure names to LR results
Input: LR_results, name = "obs_LRs.{species}.txt"
       Seizure file matching sample names to seizures
"""

import argparse

def run(input_file, seizure_file): 
    with open(input_file, 'r') as infile:
        header = infile.readline().strip().split('\t')
        file_head = header
        samps = {}
        for i, line in enumerate(infile):
            line = line.strip().split('\t')
            samps[i] = line
    with open(seizure_file, 'r') as infile:
        header = infile.readline()
        seizures = {}
        for line in infile:
            line = line.strip().split('\t')
            seizures[line[1]] = line[0]
    output_file = input_file.replace('.txt', '.seizures.txt')
    with open(output_file, 'w') as outfile:
        outfile.write('\t'.join(file_head) + '\tseizure1\tseizure2\n')
        # line changed by Jon to work in python 3
        for k, v in samps.items():
            s1 = v[0]
            s2 = v[1]
            seizure1 = seizures[s1]
            seizure2 = seizures[s2]
            outfile.write('\t'.join(v) + '\t' + seizure1 + '\t' + seizure2 + '\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--input_file', 
        help='Name of input LR_file')
    parser.add_argument('--seizure_file',
        help='Name of seizure master file')
    args = parser.parse_args()
    run(args.input_file, args.seizure_file)
