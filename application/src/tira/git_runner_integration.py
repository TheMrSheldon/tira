from django.conf import settings
from django.template.loader import render_to_string
from git import Repo
import tempfile
import logging
import gitlab
from github import Github
import ghapi
from pathlib import Path
import shutil
from datetime import datetime as dt
import os
import stat
import string
import json
from slugify import slugify
from tqdm import tqdm
from glob import glob
import subprocess
import markdown
from itertools import chain

from copy import deepcopy
from tira.grpc_client import new_transaction
from tira.model import TransactionLog, EvaluationLog
from .proto import tira_host_pb2, tira_host_pb2_grpc
import requests

logger = logging.getLogger('tira')


class GitRunner: 
    def create_task_repository(self, task_id):
        """
        Create the repository with the name "task_id" in the organization.
        An organization has task repositories (execute and evaluate submissions)
        and multiple user repositories (hosts docker images).
        Does nothing, if the repository already exists.

        Parameters
        ----------
        task_id: str
        Name of the task repository
        """
        logger.info(f"Creating task repository for task {task_id} ...")
        repo = self.__existing_repository(task_id)
        if repo:
            return int(repo.id)

        template_ci = template_ci()
        readme = self.template_readme(task_id)
        project = self._create_task_repository_on_gitHoster(task_id)
        
        tira_cmd_script = self.template_tira_cmd_script()

        with tempfile.TemporaryDirectory() as tmp_dir:
            repo = Repo.init(tmp_dir)
            self.__write_to_file(str(tmp_dir) + '/.git-ci.yml', template_ci)
            self.__write_to_file(str(tmp_dir) + '/README.md', readme)
            self.__write_to_file(str(tmp_dir) + '/tira', tira_cmd_script)
            os.chmod(str(tmp_dir) + '/tira', os.stat(str(tmp_dir) + '/tira').st_mode | stat.S_IEXEC)

            repo.create_remote('origin', self.repo_url(project.id))
            self.__ensure_branch_is_main(repo)
            repo.index.add(['README.md', '.git-ci.yml', 'tira'])
            repo.index.commit('Initial commit')
            repo.remote().push(settings.GIT_USER_REPOSITORY_BRANCH, o='ci.skip')

        logger.info(f"Created task repository for task {task_id} with new id {project.id}")
        return project.id

    def _create_task_repository_on_gitHoster(task_id):
        pass

    def __ensure_branch_is_main(self, repo):
        try:
            # for some git versions we need to manually switch, may fail if the branch is already correct
            repo.git.checkout('-b', settings.GIT_USER_REPOSITORY_BRANCH)
        except:
            pass

    def create_user_repository(self, user_name):
        """
        Create the repository for user with the name "user_name" in the organization.
        An organization has task repositories (execute and evaluate submissions)
        and multiple user repositories (hosts docker images).
        Creates an authentication token, that allows the user to upload images to this repository.
        Does nothing, if the repository already exists.

        Parameters
        ----------
        user_name: str
        Name of the user.  The created repository has the name tira-user-${user_name}
        """
        client = self.gitHoster_client
        repo = 'tira-user-' + user_name
        existing_repo = self.__existing_repository(repo)
        if existing_repo:
            return existing_repo.id
        
        project = self._create_task_repository_on_gitHoster(repo)

        token = self._create_access_token_gitHoster(project, repo)

        self.__initialize_user_repository(project.id, repo, token.token)
        
        return project.id

    def docker_images_in_user_repository(self, user_name):
        """   TODO  Dane
        List all docker images uploaded by the user with the name "user_name" to his user repository

        Parameters
        ----------
        user_name: str
        Name of the user.

        Return
        ----------
        images: Iterable[str]
        The images uploaded by the user.
        """
        cache_key = 'docker-images-in-user-repository-tira-user-' + user_name
        if cache:
            ret = cache.get(cache_key)        
            if ret is not None and not force_cache_refresh:
                return ret

        ret = []
        repo = self.__existing_repository('tira-user-' + user_name)
        if not repo:
            self.create_user_repository(user_name)
            return ret

        for registry_repository in repo.repositories.list():
            for registry in registry_repository.manager.list():
                for image in registry.tags.list(get_all=True):
                    ret += [image.location]
        
        ret = sorted(list(set(ret)))
        
        if cache:
            logger.info(f"Cache refreshed for key {cache_key} ...")
            cache.set(cache_key, ret)

        return ret


    def help_on_uploading_docker_image(self, user_name):
        """ TODO
        Each user repository has a readme.md , that contains instructions on 
        how to upload images to the repository.
        This method extracts those instructions from the readme and returns them.

        Parameters
        ----------
        user_name: str
        Name of the user.

        Return
        ----------
        help: [str]
        The personalized instructions on how to upload images 
        to be shown in the webinterface.
        """
        pass

    def add_new_tag_to_docker_image_repository(self, repository_name, existing_tag, new_tag):
        """ TODO Niklas
        The repository with the name "repository_name" contains an docker image
        with the tag "existing_tag".
        This method adds the tag "new_tag" to the image with the tag "existing_tag".

        Parameters
        ----------
        repository_name: str
        Name of the repository with an docker image with the tag "existing_tag".

        existing_tag: str
        Tag of the docker image.

        new_tag: str
        The to be added tag of the docker image.      
        """
        pass

    def all_user_repositories():
        """
        Lists all user repositories in the organization.

        Return
        ----------
        user_repositories: Iterable[str]
        List of all user repositories in the organization.
        """
        pass

    def run_and_evaluate_user_software(self, task_id, dataset_id, 
        user_name, run_id, user_software_id, user_docker_image, user_command, 
        git_repository_id, evaluator_id, evaluator_software_id, 
        evaluator_docker_image, evaluator_command):
        """ TODO
        Execute the specified software (docker image and a command)
        on a dataset and evaluate the output.

        Erzeugt neue Datei und commited diese als Trigger für Workflow/CI.

        Parameters
        ----------
        task_id: str
        Name of the task repository.

        dataset_id: str
        Dataset on which the software is to be executed.

        user_name: str
        Name of the user. The repository of the user has the name tira-user-${user_name}.

        run_id: str
        Identifier of the resulting run.

        user_software_id: str
        ID of the to be executed software.
        (identifies docker images and command)

        user_docker_image: str
        The to be execued docker image. 

        user_command: str
        The to be executed command in "user_docker_image".

        git_repository_id: str
        Identifier of the task repository
        (gitlab: int; github: ???)

        evaluator_id: str
        Identifier of the resulting evaluation.

        evaluator_software_id: str
        ID of the to be executed evaluation software. 
        (identifies the evaluation docker images and evaluation command)


        evaluator_docker_image: str
        The to be execued docker image used for evaluation.

        evaluator_command: str
        The to be executed evaluation command in "evaluation_docker_image".

        Return
        ----------
        transaction_id: str
        ID of the running transaction.
        """
        pass

    def stop_job_and_clean_up(self, git_repository_id, user_name, run_id):
        """
        All runs that are currently running, pending, or failed 
        life in a dedicated branch.
        Every successfully (without errors/failures and with evaluation) 
        executed software is merged into the main branch.
        This method stops a potentially running pipeline identified by the run_id
        of the user "user_id" and deletes the branch.

        Parameters
        ----------
        git_repository_id: str
        Identifier of the task repository.
        (gitlab: int; github: int)

        user_name: str
        Name of the user. The repository of the user has the name "tira-user-${user_name}".

        run_id: str
        Identifier of the to be stopped run.

        Return
        ----------
        -
        """
        pass

    def yield_all_running_pipelines(self, git_repository_id):
        """ TODO
        Yield all pipelines/workflows that are currently running, pending, or failed.


        Parameters
        ----------
        git_repository_id: str
        Identifier of the task repository.
        (gitlab: int; github: int)

        Return
        ----------
        jobs: Iteratable[dict]
        all pipelines/workflows that are currently running, pending, or failed.
        Each entry has the following fields:  
            'run_id',
            'execution',
            'stdOutput',
            'started_at',
            'pipeline_name',
            'job_config',
            'pipeline'
        """
        pass


class GitLabRunner(GitRunner):

    def __init__(self):
        self.git_token = settings.GIT_PRIVATE_TOKEN
        self.gitHoster_client = gitlab.Gitlab('https://' + settings.GIT_CI_SERVER_HOST, private_token=self.git_token)

    def template_ci(self):
        """
        returns the CI-Pipeline template file as string
        """
        return render_to_string('tira/git_task_repository_template_ci.yml', context={})

    def template_readme(self, task_id):
        """
        returns the readme template file for Gitlab as string
        """
        render_to_string('tira/git_task_repository_readme.md', context={'task_name': task_id})

    def template_tira_cmd_script(self, project_id):
        return render_to_string('tira/tira_git_cmd.sh', context={'project_id': project_id,
                                                                            'ci_server_host': settings.GIT_CI_SERVER_HOST})

    def add_new_tag_to_docker_image_repository(repository_name, old_tag, new_tag):
        """
        Background for the implementation:
        https://dille.name/blog/2018/09/20/how-to-tag-docker-images-without-pulling-them/
        https://gitlab.com/gitlab-org/gitlab/-/issues/23156
        """
        original_repository_name = repository_name
        repository_name = repository_name.split(settings.GIT_CONTAINER_REGISTRY_HOST + '/')[-1]
        
        token = requests.get(f'https://{settings.GIT_CI_SERVER_HOST}:{settings.GIT_PRIVATE_TOKEN}@git.webis.de/jwt/auth?client_id=docker&offline_token=true&service=container_registry&scope=repository:{repository_name}:push,pull')
        
        if not token.ok:
            raise ValueError(token.content.decode('UTF-8'))
        
        token = json.loads(token.content.decode('UTF-8'))['token']
        headers = {'Accept': 'application/vnd.docker.distribution.manifest.v2+json',
                'Content-Type': 'application/vnd.docker.distribution.manifest.v2+json',
                'Authorization': 'Bearer ' + token}
        
        manifest = requests.get(f'https://registry.webis.de/v2/{repository_name}/manifests/{old_tag}', headers=headers)

        if not manifest.ok:
            raise ValueError('-->' + manifest.content.decode('UTF-8'))
        manifest = manifest.content.decode('UTF-8')

        manifest = requests.put(f'https://registry.webis.de/v2/{repository_name}/manifests/{new_tag}', headers=headers, data=manifest)

        if not manifest.ok:
            raise ValueError(manifest.content.decode('UTF-8'))

        return original_repository_name + ':' + new_tag
    
    def all_user_repositories(self):
        """
        Lists all user repositories in the organization.

        Return
        ----------
        user_repositories: Iterable[str]
        List of all user repositories in the organization.
        """

        ret = []
        for potential_existing_projects in self.gitlab_client.projects.list(search='tira-user-'):
            if 'tira-user-' in potential_existing_projects.name and int(potential_existing_projects.namespace['id']) == int     (settings.GIT_USER_REPOSITORY_NAMESPACE_ID):
                ret += [potential_existing_projects.name]
        return set(ret)

    def _create_task_repository_on_gitHoster(self, task_id):
        project = self.gitHoster_client.projects.create(
            {'name': task_id, 'namespace_id': str(int(settings.GIT_USER_REPOSITORY_NAMESPACE_ID)),
            "default_branch": settings.GIT_USER_REPOSITORY_BRANCH})
        return project

    def _create_access_token_gitHoster(self, project, repo):
        return project.access_tokens.create(
            {"name": repo, "scopes": ['read_registry', 'write_registry'], "access_level": 30})

    def stop_job_and_clean_up(self, git_repository_id, user_name, run_id):
        """
        All runs that are currently running, pending, or failed 
        life in a dedicated branch.
        Every successfully (without errors/failures and with evaluation) 
        executed software is merged into the main branch.
        This method stops a potentially running pipeline identified by the run_id
        of the user "user_id" and deletes the branch.

        Parameters
        ----------
        git_repository_id: str
        Identifier of the task repository.
        (gitlab: int; github: int)

        user_name: str
        Name of the user. The repository of the user has the name "tira-user-${user_name}".

        run_id: str
        Identifier of the to be stopped run.

        Return
        ----------
        -
        """
        gl = self.gitHoster_client
        gl_project = gl.projects.get(int(git_repository_id))
        
        for pipeline in yield_all_running_pipelines(git_repository_id, user_id, cache, True):
            if run_id == pipeline['run_id']:
                branch = pipeline['branch'] if 'branch' in pipeline else pipeline['pipeline'].ref
                if ('---' + user_id + '---') not in branch:
                    continue
                if ('---' + run_id + '---') not in branch:
                    continue

                if 'pipeline' in pipeline:
                    pipeline['pipeline'].cancel()
                gl_project.branches.delete(branch)


    def yield_all_running_pipelines(git_repository_id, user_id, cache=None, force_cache_refresh=False):
        for pipeline in all_running_pipelines_for_repository(git_repository_id, cache, force_cache_refresh):
            pipeline = deepcopy(pipeline)

            if ('---' + user_id + '---') not in pipeline['pipeline_name']:
                continue

            if ('-training---' + user_id + '---') not in pipeline['pipeline_name']:
                pipeline['stdOutput'] = 'Output for runs on the test-data is hidden.'

            yield pipeline


    def all_running_pipelines_for_repository(git_repository_id, cache=None, force_cache_refresh=False):
        cache_key = 'all-running-pipelines-repo-' + str(git_repository_id)
        if cache:
            try:
                ret = cache.get(cache_key)
                if ret is not None and not force_cache_refresh:
                    logger.debug('get ret from cache', ret)
                    return ret
            except ModuleNotFoundError as e:
                logger.exception(f"Could not find cache module {cache_key}.")

        ret = []
        gl = self.gitHoster_client
        gl_project = gl.projects.get(int(git_repository_id))
        already_covered_run_ids = set()
        for status in ['scheduled', 'running', 'pending', 'created', 'waiting_for_resource', 'preparing']:
            for pipeline in gl_project.pipelines.list(status=status):
                user_software_job = None
                evaluation_job = None
                for job in pipeline.jobs.list():
                    if 'run-user-software' == job.name:
                        user_software_job = job
                    if 'evaluate-software-result' == job.name:
                        evaluation_job = job

                p = (pipeline.ref + '---started-').split('---started-')[0]
                
                execution = {'scheduling': 'running', 'execution': 'pending', 'evaluation': 'pending'}
                if user_software_job.status == 'running':
                    execution = {'scheduling': 'done', 'execution': 'running', 'evaluation': 'pending'}
                elif user_software_job.status != 'created':
                    execution = {'scheduling': 'done', 'execution': 'done', 'evaluation': 'running'}

                stdout = 'Output for runs on the test-data is hidden.'
                if '-training---' in p:
                    try:
                        stdout = ''
                        user_software_job = gl_project.jobs.get(user_software_job.id)
                        stdout = clean_job_output(user_software_job.trace().decode('UTF-8'))
                    except:
                        # Job is not started or similar
                        pass

                run_id = p.split('---')[-1]
                
                already_covered_run_ids.add(run_id)
                ret += [{
                    'run_id': run_id,
                    'execution': execution,
                    'stdOutput': stdout,
                    'started_at': p.split('---')[-1],
                    'pipeline_name': p,
                    'job_config': extract_job_configuration(gl_project, pipeline.ref),
                    'pipeline': pipeline
                }]
                
        ret += __all_failed_pipelines_for_repository(gl_project, already_covered_run_ids)
        
        if cache:
            logger.info(f"Cache refreshed for key {cache_key} ...")
            cache.set(cache_key, ret)
        
        return ret

    def extract_job_configuration(gl_project, branch):
        ret = {}
        
        try:
            for commit in gl_project.commits.list(ref_name=branch, page=0, per_page=3):
                if len(ret) > 0:
                    break

                if branch in commit.title and 'Merge' not in commit.title:
                    for diff_entry in commit.diff():
                        if len(ret) > 0:
                            break

                        if diff_entry['old_path'] == diff_entry['new_path'] and diff_entry['new_path'].endswith('/job-to-execute.txt'):
                            diff_entry = diff_entry['diff'].replace('\n+', '\n').split('\n')
                            ret = {i.split('=')[0].strip():i.split('=')[1].strip() for i in diff_entry if len(i.split('=')) == 2}
        except:
            pass

        try:
            from tira.tira_model import model
            software_from_db = model.get_docker_software(int(ret['TIRA_SOFTWARE_ID'].split('docker-software-')[-1]))
        except:
            software_from_db = {}

        return {
            'software_name': software_from_db.get('display_name', 'Loading...'),
            'image': software_from_db.get('user_image_name', 'Loading...'),
            'command': software_from_db.get('command', 'Loading...'),
            'cores': str(ret.get('TIRA_CPU_COUNT', 'Loading...')) + ' CPU Cores',
            'ram': str(ret.get('TIRA_MEMORY_IN_GIBIBYTE', 'Loading...')) + 'GB of RAM',
            'gpu': str(ret.get('TIRA_GPU', 'Loading...')) + ' GPUs',
            'dataset_type': ret.get('TIRA_DATASET_TYPE', 'Loading...'),
            'dataset': ret.get('TIRA_DATASET_ID', 'Loading...'),
            'software_id': ret.get('TIRA_SOFTWARE_ID', 'Loading...'),
            'task_id': ret.get('TIRA_TASK_ID', 'Loading...'),
        }

    def __all_failed_pipelines_for_repository(gl_project, already_covered_run_ids):
        ret = []

        for branch in gl_project.branches.list():
            branch = branch.name
            p = (branch + '---started-').split('---started-')[0]
            run_id = p.split('---')[-1]
            
            if run_id in already_covered_run_ids:
                continue
            
            ret += [{'run_id': run_id, 'execution': {'scheduling': 'failed', 'execution': 'failed', 'evaluation': 'failed'}, 'pipeline_name': p, 'stdOutput': 'Job did not run. (Maybe it is still submitted to the cluster or failed to start. It might take up to 5 minutes to submit a Job to the cluster.)', 'started_at': p.split('---')[-1], 'branch': branch, 'job_config': extract_job_configuration(gl_project, branch)}]

        return ret

class GithubRunner(GitRunner):

    def __init__(self, github_token):
        self.git_token = github_token
        self.gitHoster_client = Github(self.git_token)

    def _convert_repository_id_to_repository_name(self, repository_id):
        for repo in self.gitHoster_client.get_user().get_repos():
            if repo.id == rep_id : 
                return repo.name

    def template_ci(self):
        """
        returns the Workflow template file as string
        """
        # TODO: create workflow template file at tira/application/src/tira/templates/tira/git_task_repository_github_workflow.yml 
        return render_to_string('tira/git_task_repository_github_workflow.yml', context={})

    def template_readme(self, task_id):
        """
        returns the readme template file for Github as string
        """
        # TODO: create readme template file for Github at tira/application/src/tira/templates/tira/git_task_repository_github_workflow.yml 
        render_to_string('tira/git_task_repository_github_readme.md', context={'task_name': task_id})

    def template_tira_cmd_script(self, project_id):
        return render_to_string('tira/tira_git_cmd.sh', context={'project_id': project_id,
                                                                            'ci_server_host': "https://github.com"})

    def add_new_tag_to_docker_image_repository(self, repository_name, old_tag, new_tag):

        for repo in self.gitHoster_client.get_user().get_repos():
            if repo.name == repository_name:
                tags = repo.tags
                if new_tag not in tags:
                    repo.create_tag(new_tag)
                    repo.git.push(tags=True) #Brauchen wir das?
                else:
                    logger.info(f"Tag: {new_tag} already exists with the same name")
                                                                           
    def all_user_repositories(self):
        """
        Lists all user repositories in the organization "user_name".

        Return
        ----------
        user_repositories: Iterable[str]
        List of all user repositories in the organization.
        """

        ret = []
        for repo in self.gitHoster_client.get_user().get_repos():
            ret.append(repo.name)

        return set(ret)


    def stop_job_and_clean_up(self, git_repository_id, user_name, run_id):
        """
        All runs that are currently running, pending, or failed 
        life in a dedicated branch.
        Every successfully (without errors/failures and with evaluation) 
        executed software is merged into the main branch.
        This method stops a potentially running pipeline identified by the run_id
        of the user "user_id" and deletes the branch.

        Parameters
        ----------
        git_repository_id: str
        Identifier of the task repository.
        (gitlab: int; github: int)

        user_name: str
        Name of the user. The repository of the user has the name "tira-user-${user_name}".

        run_id: str
        Identifier of the to be stopped run.

        Return
        ----------
        -
        """
        repository_name = self._convert_repository_id_to_repository_name(git_repository_id)

        # cancel worflow run
        run = self.gitHoster_client.get_user().get_repo(repository_name).get_workflow_run(run_id)
        run.cancel()

        # delete branch
        branch_name = run.head_branch
        self.gitHoster_client.get_user().get_repo(repository_name).get_git_ref(f"heads/{branch_name}").delete

    def _create_task_repository_on_gitHoster(self, task_id):
        # create new repository and rename the default branch
        project = self.gitHoster_client.get_user().create_repo(name = task_id)
        for branch in project.get_branches():
            project.rename_branch(branch=branch, new_name= settings.GIT_USER_REPOSITORY_BRANCH)
        return project

    def _create_access_token_gitHoster(self, project ,repo):
        return self.git_token

        def yield_all_running_pipelines(self, git_repository_id):
        """
        Yield all pipelines/workflows that are currently running, pending, or failed.


        Parameters
        ----------
        git_repository_id: str
        Identifier of the task repository.
        (gitlab: int; github: int)

        Return
        ----------
        jobs: Iteratable[dict]
        all pipelines/workflows that are currently running, pending, or failed.
        Each entry has the following fields:  
            'run_id',
            'execution',
            'stdOutput',
            'started_at',
            'pipeline_name',
            'job_config',
            'pipeline'
        """
        #https://docs.github.com/en/rest/actions/workflow-jobs?apiVersion=2022-11-28#get-a-job-for-a-workflow-run
        pass