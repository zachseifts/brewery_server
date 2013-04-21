from __future__ import with_statement
from fabric.api import run, cd, sudo, local

def update_app():
    with cd('/Users/zach/projects/brewery_server'):
        local('git push')
    with cd('/home/zach/apps/brewery_server'):
        run('git pull')
        sudo('supervisorctl restart brewery_server')
