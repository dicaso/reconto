# -*- coding: utf-8 -*-
"""reconto module defining CLI interface"""
import argparse, os
from reconto import Reconto

def prepareParser():
    """Creates the CLI parser"""
    parser = argparse.ArgumentParser(
        prog = 'reconto', description = 'manage research compendia'
    )
    parser.add_argument('--verbose', action = 'store_true', help = 'verbose output')
    
    subparsers = parser.add_subparsers(help='sub-command help')
    newparser = subparsers.add_parser(
        'new',
        help='reconto new -h'
    )
    newparser.set_defaults(selectedparser='new')
    newparser.add_argument(
        'path',
        help='path where the research compendium will be created'
    )
    addparser = subparsers.add_parser(
        'add',
        help='reconto add -h'
    )
    addparser.set_defaults(selectedparser='add')
    addparser.add_argument(
        'command', nargs='+',
        help='command to execute in workflow'
    )
    addparser.add_argument(
        '--path',
        help='research compendium. if not provided takes current location, or first upstream location containing `reconto.yml`'
    )
    addparser.add_argument(
        '--exenv',
        help='workflow step execution environment `python://...` or `docker://`'
    )
    addparser.add_argument(
        '--datasources',
        help='workflow step required datasources (can be one item or `,` separated list)'
    )
    addparser.add_argument(
        '--results',
        help='workflow step generated result files (can be one item or `,` separated list)'
    )
    commitparser = subparsers.add_parser(
        'commit',
        help='reconto commit -h'
    )
    commitparser.add_argument(
        'msg',
        help='commit message. A reconto commit executes a full (cached) workflow before commiting the changes to the git repo'
    )
    return parser

def search_reco():
    path = os.getcwd()
    while not os.path.exists(os.path.join(path,'reconto.yml')):
        if path == '/':
            raise FileNotFoundError(
                'Current directory or upstream directory is not a reconto repository'
            )
        path = os.path.dirname(path)
    return path
                
def main(args=None):
    parser = prepareParser()
    args = parser.parse_args(args)
    if args.selectedparser == 'new':
        reco = Reconto(path = args.path, init = True)
        print(reco)
    elif args.selectedparser == 'add':
        if not args.path:
            args.path = search_reco()
        reco = Reconto(path = args.path)
        reco.add(
            command = args.command,
            exenv = args.exenv,
            datasources = args.datasources.split(',') if args.datasources else [],
            results = args.results.split(',') if args.results else []
        )
    elif args.selectedparser == 'commit':
        if not args.path:
            args.path = search_reco()
        reco = Reconto(path = args.path)
        reco.commit(args.message)
