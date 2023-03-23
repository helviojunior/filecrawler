import datetime
import hashlib
import json
import os
from pathlib import Path
from typing import Iterator
import git

from filecrawler.libs.cpath import CPath
from filecrawler.util.tools import Tools


class GitFinder(object):
    _git_path = None
    _repo = None
    _DATE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
    _EMPTY_TREE_SHA = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"

    def __init__(self, git_path: CPath):
        self._git_path = git_path
        self._repo = git.Repo(self._git_path.path)

    def get_diffs(self) -> Iterator[dict]:
        path = str(Path(self._git_path.path_real).parent)
        # branches = [str(b) for b in self._repo.heads]

        for branch in self._repo.heads:
            # Iterate through every commit for the given branch in the repository
            for commit in self._repo.iter_commits(branch):
                # Determine the parent of the commit to diff against.
                # If no parent, this is the first commit, so use empty tree.
                # Then create a mapping of path to diff for each file changed.
                parent = commit.parents[0] if commit.parents else self._EMPTY_TREE_SHA
                diffs = {
                    diff.a_path: diff for diff in commit.diff(parent)
                }

                # The stats on the commit is a summary of all the changes for this
                # commit, we'll iterate through it to get the information we need.
                for objpath, stats in commit.stats.files.items():

                    # Select the diff for the path in the stats
                    diff = diffs.get(objpath)

                    # If the path is not in the dictionary, it's because it was
                    # renamed, so search through the b_paths for the current name.
                    if not diff:
                        for diff in diffs.values():
                            if diff.b_path == path and diff.renamed:
                                break

                    try:
                        # Update the stats with the additional information
                        opath = Path(os.path.join(self._git_path.path_virtual, objpath))
                        stats.update(dict(
                            branch=branch.name,
                            commit=commit.hexsha,
                            object=str(objpath),
                            author=commit.author.email,
                            message='\n'.join([
                                m for m in commit.message.strip('').replace('\r', '').split('\n')
                                if m.strip() != ''
                            ]) if commit.message is not None else '',
                            timestamp=commit.authored_datetime.strftime(self._DATE_TIME_FORMAT),
                            type=self._diff_type(diff),
                        ))

                        if diff.a_blob is not None:
                            bdata_a = diff.a_blob.data_stream.read()
                            yield dict(
                                fingerprint=self._diff_fingerprint(stats, 'a'),
                                filename=opath.name,
                                extension=opath.suffix.strip('. '),
                                mime_type=Tools.get_mimes(bdata_a),
                                file_size=diff.a_blob.size,
                                created=commit.authored_datetime,
                                last_accessed=commit.authored_datetime,
                                last_modified=commit.authored_datetime,
                                indexing_date=datetime.datetime.utcnow(),
                                path_real=self._git_path.path_real,
                                path_virtual=f'{self._git_path.path_virtual}/<gitcommit>/{branch.name}/{commit.hexsha}/blob_a/{objpath.strip("/")}',
                                metadata=json.dumps(stats, default=Tools.json_serial),
                                content=bdata_a
                            )

                        if diff.b_blob is not None:
                            bdata_b = diff.b_blob.data_stream.read()
                            if len(bdata_b) > 0:
                                yield dict(
                                    fingerprint=self._diff_fingerprint(stats, 'b'),
                                    filename=opath.name,
                                    extension=opath.suffix.strip('. '),
                                    mime_type=Tools.get_mimes(bdata_b),
                                    file_size=diff.b_blob.size,
                                    created=commit.authored_datetime,
                                    last_accessed=commit.authored_datetime,
                                    last_modified=commit.authored_datetime,
                                    indexing_date=datetime.datetime.utcnow(),
                                    path_real=self._git_path.path_real,
                                    path_virtual=f'{self._git_path.path_virtual}/<gitcommit>/{branch.name}/{commit.hexsha}/blob_b/{objpath.strip("/")}',
                                    metadata=json.dumps(stats, default=Tools.json_serial),
                                    content=bdata_b
                                )
                    except Exception as e:
                        from filecrawler.config import Configuration
                        if Configuration.verbose >= 4:
                            Tools.print_error(Exception(f'Error parsing git data from: {self._git_path}', str(e)))

    def _diff_fingerprint(self, stats, salt: str = ''):
        sha1sum = hashlib.sha1()
        sha1sum.update(f'{self._git_path}_{salt}'.encode("utf-8"))
        sha1sum.update(json.dumps(stats, default=Tools.json_serial).encode("utf-8"))

        return sha1sum.hexdigest()

    @classmethod
    def _diff_type(cls, diff):
        """
        Determines the type of the diff by looking at the diff flags.
        """
        if diff.renamed: return 'R'
        if diff.deleted_file: return 'D'
        if diff.new_file: return 'A'
        return 'M'