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
    def __init__(self,path,init=False):
        self.name = os.path.basename(path)
        self.path = path

        if os.path.exists(self.yamlfile):
            self.repo = git.Repo(self.path)
        elif not init:
            raise FileNotFoundError('reconto repo does not yet exist')
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

    def add(self, command, exenv=None, datasources = [], results = []):
        """add a workflow command to the reconto yml file
        this does not commit the command yet to the workflow history.

        Args:
            command (str or str list): The command that should be executed.
            exenv (str): The execution environment, if none is given defaults 
              to the workflow default.
            datasources (str list): List of datasourses used in the workflow step.
            results (str list): List of result files or directories generated 
              in workflow step.
        """
        pass

    def add_exenv(self,exenv):
        """add exenv to reco config if proper
        """
        self.config['exenv'].append(exenv)

    def build(self,cached=True):
        """build the workflow

        Args:
            cached (bool): If True, does not reexecute earlier build steps
        """
        pass

    def commit(self,message):
        """commit new workflow steps to the research compendium
        if they properly execute. This step will take as much time
        as is needed for the execution of the workflow steps to complete

        Args:
            message (str): Commit message to include
        """
        # check if there are workflow changes compared to last commit

        # build the new steps
        # in a commit step it is not part of design to reexecute what has been committed earlier
        self.build(cached=True)

        # commit new workflow

        
