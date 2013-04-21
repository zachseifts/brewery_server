from __future__ import with_statement
from fabric.api import run, cd, sudo

def update_app():
    with cd('/home/zach/apps/brewery_server'):
        run('git pull')
        sudo('supervisorctl restart brewery_server')
