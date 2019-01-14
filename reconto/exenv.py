# -*- coding: utf-8 -*-
"""exenv: module defining the execution environment object

Defines a python and a docker execution environment

TODO: allow a way to register 3rd party execution environments
"""
import abc, re, os

class Exenv(abc.ABC):
    """Exenv object
    defining common interface for exenvs
    the inheriting Exenv needs to define an class attribute `_uid_regex`,
    which should be a compiled regular expression with named groups.
    At the very least define a group "typenv" identifying the Exenv and 
    a group "uid" that within the Exenv should fully define it.

    Args:
        uid (str): The string that uniquely identifies the execution environment.
        reco (Reconto): the research compendium that depends on this environment.
    """
    def __init__(self,uid,reco):
        regex_attributes = self._uid_regex.fullmatch(uid).groupdict()
        for key in regex_attributes:
            setattr(self, key, regex_attributes[key])
        self.reco = reco
        
    @abc.abstractmethod
    def load_environment(self):
        pass

    @abc.abstractmethod
    def execute_command(self, command, *args):
        pass

    @abc.abstractmethod
    def stop_environment(self):
        pass

class Pyenv(Exenv):
    """Python execution environment"""
    _uid_regex = re.compile(r'(?P<typenv>pyenv)://(?P<pyver>py\d\.\d)/(?P<uid>\w\S+)')

    def load_environment(self):
        import plumbum as pb
        self.envdir = os.path.join(self.reco.path,'exenv',self.pyver,self.uid)
        if not os.path.exists(self.envdir):
            if not os.path.exists(os.path.join(self.reco.path,'exenv')):
                os.mkdir(os.path.join(self.reco.path,'exenv'))
            if not os.path.exists(os.path.join(self.reco.path,'exenv',self.pyver)):
                os.mkdir(os.path.join(self.reco.path,'exenv',self.pyver))
            os.mkdir(self.envdir)
            with pb.local.env(PIPENV_IGNORE_VIRTUALENVS=1):
                with pb.local.cwd(self.envdir):
                    pb.local['pipenv']('--python','python'+self.pyver[2:])

    def execute_command(self, command, *args):
        import plumbum as pb
        if type(command) is str:
            command = (command,)
        with pb.local.env(PIPENV_IGNORE_VIRTUALENVS=1):
            with pb.local.cwd(self.envdir):
                pb.local['pipenv'].bound_command(
                    'run',*command,*args
                ) & pb.FG

    def stop_environment(self):
        del self.envdir
        
class Docker(Exenv):
    """Docker container execution environment"""
    _uid_regex = re.compile(r'(?P<type>docker)://(?P<uid>\w\S+)')
    
    def load_environment(self):
        import docker
        self.client = docker.from_env()

    def execute_command(self, command, *args):
        if args and type(command) is str:
            command += ' '+' '.join(args)
        elif type(command) is not str:
            command = ' '.join(command) + ' ' + ' '.join(args)
        self.container = self.client.containers.create(self.uid, command)
        self.container.start()

    def stop_environment(self):
        self.container.stop()