# -*- coding: utf-8 -*-
"""reconto: REsearch COmpound memeNTO

Basic module, describes the reconto start class
that defines a research project.

"""
import os, logging, git, yaml

class Reconto(object):
    """Reconto object

    Is defined by a path were all files will be stored and executions
    will be run.
    """
    def __init__(self,path):
        self.name = os.path.basename(path)
        self.path = path

        if os.path.exists(path):
            self.repo = git.Repo(self.path)
        else:
            try:
                os.mkdir(path)
            except FileNotFoundError:
                logging.error(
                    'Parent directory "%s" does not exist',
                    os.path.dirname(path)
                )
                raise
            # initialize git repo
            self.repo = git.Repo.init(self.path)
            import pkgutil
            with open(self.yamlfile,'wb') as f:
                f.write(pkgutil.get_data('reconto','templates/reconto.yml'))
            self.repo.index.add(['reconto.yml'])
            self.repo.index.commit('reconto yaml file added')
            
            # read reconto yaml configuration
            self.config = yaml.load(open(self.yamlfile))

    @property
    def yamlfile(self):
        return os.path.join(self.path,'reconto.yml')
