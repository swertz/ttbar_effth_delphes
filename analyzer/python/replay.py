#! /bin/env python

import os, sys
import pickle, pprint
import TMVAReplayer

import yaml

import argparse

parser = argparse.ArgumentParser(description='Replay a tree on a new input file')
parser.add_argument('config')

args = parser.parse_args()

pprint.pprint(args)

configuration = {}
# Parse configuration
with open(args.config) as f:
    configuration = yaml.load(f)

    with open(configuration["analysis"]["trained_tree"]) as g:
        tree = pickle.Unpickler(g).load()

        # Clear old input files
        tree.cfg.procCfg = {}

        root = tree.firstBox
        mvaReader = TMVAReplayer.TMVAReplayer(configuration, root)
        mvaReader.run()
