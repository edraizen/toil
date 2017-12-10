# Copyright (C) 2017- Regents of the University of California
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Debug tool for copying files contained in a toil jobStore.
"""

from __future__ import absolute_import
import logging
import fnmatch
import os.path

from toil.lib.bioio import getBasicOptionParser
from toil.lib.bioio import parseBasicOptions
from toil.common import Toil, jobStoreLocatorHelp, Config
from toil.version import version

logger = logging.getLogger( __name__ )

def recursiveGlob(directoryname, glob_pattern):
    '''
    Walks through a directory and its subdirectories looking for files matching
    the glob_pattern and returns a list=[].

    :param directoryname: Any accessible folder name on the filesystem.
    :param glob_pattern: A string like "*.txt", which would find all text files.
    :return: A list=[] of absolute filepaths matching the glob pattern.
    '''
    directoryname = os.path.abspath(directoryname)
    matches = []
    for root, dirnames, filenames in os.walk(directoryname):
        for filename in fnmatch.filter(filenames, glob_pattern):
            absolute_filepath = os.path.join(root, filename)
            matches.append(absolute_filepath)
    return matches

def fetchJobStoreFiles(jobStore, options):
    """
    Takes a list of file names as glob patterns, searches for these within a
    given directory, and attempts to take all of the files found and copy them
    into options.localFilePath.

    :param jobStore: A fileJobStore object.
    :param options.fetchTheseJobStoreFiles: List of file glob patterns to search
        for in the jobStore and copy into options.localFilePath.
    :param options.localFilePath: Local directory to copy files into.
    :param options.jobStore: The path to the jobStore directory.
    """
    for jobStoreFile in options.fetchTheseJobStoreFiles:
        jobStoreHits = recursiveGlob(directoryname=options.jobStore, glob_pattern=jobStoreFile)
        for jobStoreFileID in jobStoreHits:
            localFileID = os.path.join(jobStoreFileID, options.localFilePath)
            logger.info("Copying job store file: %s to %s", jobStoreFileID, localFileID)
            jobStore.readGlobalFile(jobStoreFileID, localFileID, symlink=options.useSymlinks)

def printContentsOfJobStore(jobStore):
    """
    Fetch a list of files contained in the jobStore directory input, then prints
    out that list to the log.  Also generates a file called:
    list_of_jobstore_files.txt in the current working directory with this list.

    :param jobStore: Directory path to recursively look for files.
    """
    list_of_files = recursiveGlob(directoryname=jobStore, glob_pattern="*")
    for gfile in list_of_files:
        logger.info("File: %s", gfile)
        with open("list_of_jobstore_files.txt", "w") as f:
            f.write(gfile)
            f.write("\n")

def main():
    parser = getBasicOptionParser()

    parser.add_argument("jobStore",
                        type=str,
                        help="The location of the job store used by the workflow." +
                        jobStoreLocatorHelp)
    parser.add_argument("localFilePath",
                        nargs=1,
                        help="Location to which to copy job store files.")
    parser.add_argument("--fetchTheseJobStoreFiles",
                        nargs='+',
                        help="List of job-store files to be copied locally."
                        "Use either explicit names (i.e. 'data.txt'), or "
                        "specify glob patterns (i.e. '*.txt')")
    parser.add_argument("--listFilesInJobStore",
                        help="Prints a list of the current files in the jobStore.")
    parser.add_argument("--fetchEntireJobStore",
                        help="Copy all job store files into a local directory.")
    parser.add_argument("--useSymlinks",
                        help="Creates symlink 'shortcuts' of files in the localFilePath"
                        " instead of hardlinking or copying, where possible.  If this is"
                        "not possible, it will copy the files (shutil.copyfile()).")
    parser.add_argument("--version", action='version', version=version)
    
    # Load the jobStore
    options = parseBasicOptions(parser)
    config = Config()
    config.setOptions(options)
    jobStore = Toil.resumeJobStore(config.jobStore)
    logger.info("Connected to job store: %s", config.jobStore)

    if options.fetchTheseJobStoreFiles:
        # Copy only the listed files locally
        fetchJobStoreFiles(jobStore=jobStore, options=options)

    elif options.fetchEntireJobStore:
        # Copy all jobStore files locally
        options.fetchTheseJobStoreFiles = "*"
        fetchJobStoreFiles(jobStore=jobStore, options=options)

    if options.listFilesInJobStore:
        # Log filenames and create a file containing these names in cwd
        printContentsOfJobStore(options.jobStore)

if __name__=="__main__":
    main()