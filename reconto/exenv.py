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

    @property
    @abc.abstractmethod
    def env_working_dir(self):
        pass

    def get_env_filepath(self,filepath):
        """get an absolute filepath for set environment

        Args:
            filepath (str): should be a relative reco path
              for a data or result file/dir
        """
        return os.path.join(self.env_working_dir,filepath)

    def get_env_data_filepath(self,filepath):
        """get an absolute data filepath for set environment

        Args:
            filepath (str): should be a relative reco path
              for a data file/dir
        """
        return os.path.join(self.env_working_dir,'data',filepath)

    def get_env_result_filepath(self,filepath):
        """get an absolute result filepath for set environment

        Args:
            filepath (str): should be a relative reco path
              for a result file/dir
        """
        return os.path.join(self.env_working_dir,'results',filepath)

    def reset_escaped_annotations(self, command):
        """Reset the escaped annotations

        A command list can contain reco escaped bash symbols as elements,
        this function replaces them with their bash symbol.

        Args:
            command (str[]): a command list
        """
        return [
            e if not e in self.reco.annotations['special']
            else self.reco.annotations['special'][e]
            for e in command
        ]

    def contains_escaped_annotations(self, command):
        """Return if there are any escaped annotations

        Args:
            command (str[]): a command list
        """
        for e in command:
            if e in self.reco.annotations['special']:
                return True
        #if this statement is reached no special annotations present
        return False
    
    def __enter__(self):
        self.load_environment()
        return self
        
    def __exit__(self, exc_type, exc_value, traceback):
        self.stop_environment()

    @staticmethod
    def get_env(uid,reco):
        if uid.startswith('pyenv'): return Pyenv(uid,reco)
        elif uid.startswith('docker'): return Docker(uid,reco)
        else: raise NotImplementedError('in future should allow registering 3rd party env')

class Pyenv(Exenv):
    """Python execution environment"""
    _uid_regex = re.compile(r'(?P<typenv>pyenv)://(?P<pyver>py\d\.\d)/(?P<uid>\w\S+)')

    @property
    def env_working_dir(self):
        return self.reco.path
    
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

    @property
    def env_working_dir(self):
        return '/app'
    
    def load_environment(self):
        import docker
        self.client = docker.from_env()

    def execute_command(self, command, *args):
        from docker.errors import ImageNotFound
        if args and type(command) is str:
            command += ' '+' '.join(args)
        elif type(command) is not str:
            escape_command = self.contains_escaped_annotations(command)
            if escape_command: command = self.reset_escaped_annotations(command)
            command = ' '.join(command) + ' ' + ' '.join(args)
            command = 'sh -c "{}"'.format(command.replace('"',r'\"'))
        try:
            self.image = self.client.images.get(self.uid)
        except ImageNotFound:
            self.image = self.client.images.pull(self.uid)
        self.container = self.client.containers.create(
            self.uid, command,
            volumes={
                os.path.join(self.reco.path,'data'):{'bind':'/app/data','mode':'ro'},
                os.path.join(self.reco.path,'results'):{'bind':'/app/results','mode':'rw'},
            },
            working_dir = '/app'
        )
        self.container.start()

    def stop_environment(self):
        self.container.stop()
        del self.client, self.image, self.container
