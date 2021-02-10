#!/usr/bin/env python
"""
filter_LRs.py
Filter LRs by cutoff (on log10 scale) and on >= 10 loci
Pick out the top LR among the different relationship types
Input: LR_results (after seizures have been added!)
       name: "obs_LRs.{species}.seizures.txt"
       cutoff
"""

import argparse
import math
import numpy as np

def run(input_file, cutoff):
    suffix = '.' + str(cutoff) + '.filtered.txt'
    output_file = input_file.replace('.txt', suffix)
    with open(input_file, 'r') as infile:
        with open(output_file, 'w') as outfile:
            header = infile.readline().strip().split('\t')
            outfile.write('\t'.join(header) + '\ttop_type\ttop_LR\n')
            for line in infile:
                line = line.strip().split('\t')
                top_index = np.argmax([float(line[2]), 
                                     float(line[3]), 
                                     float(line[4]), 
                                     float(line[5])])
                top_type = ['DM', 'PO', 'FS', 'HS'][top_index]
                top_LR = max(float(line[2]), float(line[3]), 
                          float(line[4]), float(line[5]))
                nloci = int(line[6])
                if math.log10(top_LR) >= cutoff and nloci >= 10:
                    outfile.write('\t'.join(line) + '\t' + top_type + '\t' + str(top_LR) + '\n') 

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--input_file', 
        help='Name of input LR file')
    parser.add_argument('--cutoff', type=float,
        help='LR cutoff')
    args = parser.parse_args()
    run(args.input_file, args.cutoff)
