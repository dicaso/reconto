# -*- coding: utf-8 -*-
"""reconto: REsearch COmpound memeNTO

Basic module, describes the reconto start class
that defines a research project.

"""
import os, logging, git, yaml, re

class Reconto(object):
    """Reconto object

    Is defined by a path were all files will be stored and executions
    will be run.
    """
    def __init__(self,path,init=False,default_exenv='docker://python:3.7'):
        self.name = os.path.basename(path)
        self.path = path
        self.default_exenv = default_exenv

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

    annotations = {
        'script': re.compile(r'@(?P<exenv>\S+)@(?P<script>\S+)'),
        'datasource': re.compile(r'@(?P<datasource>\S*)@(?P<filepath>\S+?)(?P<include>@?)'),
        'result': re.compile(r'=(?P<result>\S*)=(?P<filepath>\S+?)(?P<include>=?)')
    }
        
    def add(self, command, exenv=None, datasources = [], results = []):
        """add a workflow command to the reconto yml file
        this does not commit the command yet to the workflow history.

        A command can have annotated elements, an annotated element is of the form:
          `@...@`, `=...=`, or `%...%`

        Annotations:
            @[exenv]@[script]: annotates the execution environment of the command script,
              can only be the first element in the command, e.g. `@docker://ubuntu@echo`
            @[datasource]@[filepath]: annotates an external location for a datasource used
              in the command, e.g. `@https://examples.com/archive.tar.gz@cmdfilename.tar.gz`
            @[datasource]@[filepath]@: same as before, but avoiding redundancy when last part
              of datasource uid is the same as commandline filepath,
              e.g. `@https://examples.com/@archive.tar.gz@`
            =[result]=[filepath]: annotates the location for a result produced
              by the command, e.g. `=https://examples.com/result.tar.gz=cmdfilename.tar.gz`
            =[result]=[filepath]=: same as before, but avoiding redundancy when last part
              of result uid is the same as commandline filepath,
              e.g. `=https://examples.com/=result.tar.gz=`
            %IN%: escape for shell redirection `<`
            %OUT%: escape for shell redirection `>`
            %PIPE%: escape for shell redirection '|'

        Args:
            command (str or str list): The command that should be executed.
              If provided as a str, it will be split according to whitespace.
              In case some of the arguments contain whitespace, provide as a
              list not str.
            exenv (str): The execution environment, if none is given defaults 
              to the workflow default.
            datasources (str list): List of datasourses used in the workflow step.
            results (str list): List of result files or directories generated 
              in workflow step.

        When commandline is fully annotated, `exenv`, `datasources` and `results` do not 
        need to be provided. If the commandline is not fully annotated, the provided strings
        in these extra arguments need to be informative enough to extract their corresponding
        positions in the commandline. If both are provided, consistency is checked and function
        raises Exception when inconsistent.
        """
        # Normalizing command
        command = command.split() if type(command) is str else list(command)
        
        # Setting exenv
        script_annot = Reconto.annotations['script'].fullmatch(command[0])
        if script_annot:
            script_annot = script_annot.groupdict()
            if exenv and not script_annot['exenv']==exenv:
                raise Exception('--exenv and command annotation inconsistent')
            exenv = script_annot['exenv']
        else:
            if not exenv and self.config['exenv']:
                print('using reconto default exenv:')
                exenv = self.config['exenv'][0]
                print(exenv)
            if not exenv:
                raise Exception('no exenv provided and no default available')
        if exenv not in self.config['exenv']:
            self.config['exenv'].append(exenv)
        cmdenv = [script_annot['script'] if script_annot else command[0],exenv]
        if cmdenv not in self.config['scripts']:
            self.config['scripts'].append(cmdenv)
        if not script_annot:
            command[0] = '@{}@{}'.format(exenv,command[0])
            
        # Setting datasources
        extracted_dsources = [
            Reconto.annotations['datasource'].fullmatch(e) for e in command[1:]
            if Reconto.annotations['datasource'].fullmatch(e)
        ]
        if extracted_dsources:
            eds_strings = [eds.string for eds in extracted_dsources]
            for eds in eds_strings:
                if not eds in self.config['data']:
                    self.config['data'].append(eds)
            if datasources and not (set(datasources) == set(eds_strings)):
                raise Exception(
                    "annotated datasources and provided datasources inconsistent",
                    datasources, eds_strings
                )
        elif datasources:
            # Find command line elements that need to be annotated
            for ds in datasources:
                ds_annot = Reconto.annotations['datasource'].fullmatch(ds).groupdict()
                for i,cle in enumerate(command):
                    if not i: continue
                    if ds_annot['filepath'] == cle:
                        command[i] = ds
                if not ds in self.config['data']:
                    self.config['data'].append(ds)

        # Setting results
        extracted_results = [
            Reconto.annotations['result'].fullmatch(e) for e in command[1:]
            if Reconto.annotations['result'].fullmatch(e)
        ]
        if extracted_results:
            er_strings = [er.string for er in extracted_results]
            for er in er_strings:
                if not er in self.config['results']:
                    self.config['results'].append(er)
            if results and not (set(results) == set(er_strings)):
                raise Exception(
                    "annotated results and provided results inconsistent",
                    results, er_strings
                )
        elif results:
            # Find command line elements that need to be annotated
            for r in results:
                r_annot = Reconto.annotations['result'].fullmatch(r).groupdict()
                for i,cle in enumerate(command):
                    if not i: continue
                    if r_annot['filepath'] == cle:
                        command[i] = r
                if not r in self.config['results']:
                    self.config['results'].append(r)

        # Output updated workflow
        self.config['workflow'].append(command)
        with open(self.yamlfile,'wt') as f:
            yaml.dump(self.config,f)
            
    def build(self,cached=True):
        """build the workflow

        Args:
            cached (bool): If True, does not reexecute earlier build steps
        """
        from reconto.exenv import Exenv
        for step in self.config['workflow']:
            env, command = Reconto.annotations['script'].fullmatch(step[0]).groups()
            exenv = Exenv.get_env(env,reco)
            datasources = {
                i: Reconto.annotations['datasource'].fullmatch(se).groupdict()
                for i,se in enumerate(step) if i and
                Reconto.annotations['datasource'].fullmatch(se)
            }
            results = {
                i: Reconto.annotations['result'].fullmatch(se).groupdict()
                for i,se in enumerate(step) if i and
                Reconto.annotations['result'].fullmatch(se)
            }
            if cached:
                pass #TODO check if results are there if true continue
            with exenv:
                exenv.execute_command(step)

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

    def prepare_datasource(self,datasource,filepath,include):
        # if include
        datasource+=filepath
        # if no datasource but only filepath, file should already be available
        complete_filepath = os.path.join(self.path, 'data', filepath)
        source_present = os.path.exists(complete_filepath)
        if not source_present:
            if datasource:
                pass #TODO retrieve datasource logic, incorporate lostdata package
            else:
                raise FileNotFoundError('datasource not available in reco data folder')

    def check_result(self,result,filepath,include):
        # if include
        result+=filepath
        complete_filepath = os.path.join(self.path, 'results', filepath)
        source_present = os.path.exists(complete_filepath)
        return source_present
