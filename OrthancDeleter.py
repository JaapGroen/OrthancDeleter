#!/usr/bin/env python
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This code is an analysis module for WAD-QC 2.0: a server for automated
# analysis of medical images for quality control.
#
# The WAD-QC Software can be found on
# https://bitbucket.org/MedPhysNL/wadqc/wiki/Home
#
#
# Changelog:
#   20200623: initial version

from __future__ import print_function

__version__ = '20200623'
__author__ = 'jmgroen'

from wad_qc.module import pyWADinput
from wad_qc.modulelibs import wadwrapper_lib
import numpy as np
import json
from datetime import datetime
import RestToolbox
import time
import os

def deleter_run(settings):

    # set credentials for orthanc
    RestToolbox.SetCredentials(settings['orthanc_user'], settings['orthanc_password'])
    orthanc_url = 'http://'+settings['orthanc_ip']+':'+str(settings['orthanc_port'])

    # get all studies in orthanc
    studies = RestToolbox.DoGet('%s/studies' % orthanc_url)
    results.addFloat('Checked studies',len(studies))
    print('checking',len(studies),'studies.')

    # loop over all studies
    count_deleted_studies = 0
    for study in studies:
        study_date_str = RestToolbox.DoGet('%s/studies/%s' % (orthanc_url,study))['MainDicomTags']['StudyDate']
        study_date = datetime.strptime(study_date_str, '%Y%m%d')
        study_age = now - study_date
        if study_age.days > settings['delete_after']:
            RestToolbox.DoDelete('%s/studies/%s' % (orthanc_url, study))
            print('Deleted study',study)
            count_deleted_studies+=1

    # save the date of the last run
    with open(dir_path+'/last_run.json', 'w') as outfile:
        json.dump({'last_run':now.strftime('%d/%m/%Y, %H:%M:%S')}, outfile)

    # save the number of deleted studies as a result
    results.addFloat('Deleted studies',count_deleted_studies)

    return True

# read in config
data, results, config = pyWADinput()

# set some moments we use later
start_time = time.time()
now = datetime.now()
results.addDateTime('DateTime', now)

# check the last run of the deleter

import os

dir_path = os.path.dirname(os.path.realpath(__file__))
with open(dir_path+'/last_run.json', 'r') as read_file:
    last_run_str = json.load(read_file)['last_run']
    last_run_datetime = datetime.strptime(last_run_str, '%d/%m/%Y, %H:%M:%S')

difference = now-last_run_datetime
if difference.days < config['actions']['deleter']['params']['run_interval']:
    print('Last run was only',difference.days,'days ago, not running the deleter.')
    results.addBool('Deleter run',False)
    results.addFloat('Deleted studies',0)
else:
    # run the deleter
    print('Last run was',difference.days,'days ago, running the deleter.')
    results.addBool('Deleter run',True)
    settings = config['actions']['deleter']['params']
    completed = deleter_run(settings)

    if completed:
        run_time = time.time() - start_time
        print("Deleter complete in %s seconds." % run_time)

results.write()
