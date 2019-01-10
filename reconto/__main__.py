# -*- coding: utf-8 -*-
"""reconto module defining CLI interface"""
import argparse

def prepareParser():
    """Creates the CLI parser"""
    parser = argparse.ArgumentParser(
        prog = 'reconto', description = 'manage research compendia'
    )
    parser.add_argument('--verbose', action = 'store_true', help = 'verbose output')
    
    subparsers = parser.add_subparsers(help='sub-command help')
    subparser = subparsers.add_parser(
        'new',
        help='genairics new -h'
    )
    subparser.add_argument(
        'path',
        help='path where the research compendium will be created'
    )
    return parser

def main(args):
    parser = prepareParser()
    args = parser.parse_args(args)
    print(args)
