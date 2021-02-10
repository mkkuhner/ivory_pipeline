#!/usr/bin/env python
"""
Analyze number of matches per seizure
using filtered LRs
Input: filtered_LR_results
"""

import argparse

def run(filtered_file):
    outf = filtered_file.strip('txt') + 'seizanalysis.txt'
    # structure of this dict is a list with 
    # [DM pairs, PO pairs, FS pairs, HS pairs]
    seiz = {}
    with open(filtered_file, 'r') as infile:
        header = infile.readline().strip().split('\t')
        s1_ind = header.index('seizure1')
        top_ind = header.index('top_type')
        for line in infile:
            line = line.strip().split('\t')
            seiz1 = line[s1_ind]
            seiz2 = line[s1_ind + 1]
            pair = (seiz1, seiz2)
            top_LR = line[top_ind]
            if pair not in seiz:
                seiz[pair] = [0,0,0,0]
            if top_LR == 'DM':
                seiz[pair][0] += 1
            elif top_LR == 'PO':
                seiz[pair][1] += 1
            elif top_LR == 'FS':
                seiz[pair][2] += 1
            elif top_LR == 'HS':
                seiz[pair][3] += 1
    with open(outf, 'w') as outfile:
        outfile.write('seizure1\tseizure2\tDM\tPO\tFS\tHS\n')
        for k,v in seiz.items():
            outfile.write('\t'.join(k) + '\t')
            outfile.write('\t'.join([str(i) for i in v]) + '\n') 

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--filtered_file', 
        help='Name of filtered LR file')
    args = parser.parse_args()
    run(args.filtered_file)
