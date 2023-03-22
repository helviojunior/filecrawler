import datetime
import hashlib
import json
import os
from pathlib import Path
from typing import Iterator

from filecrawler.libs.cpath import CPath
from filecrawler.util.tools import Tools


class GitFinder(object):
    _git_path = None
    _DATE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
    _EMPTY_TREE_SHA = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"

    def __init__(self, git_path: CPath):
        self._git_path = git_path

    def get_diffs(self) -> Iterator[dict]:
        import git
        repo = git.Repo(self._git_path.path_real)
        path = str(Path(self._git_path.path_real).parent)
        # branches = [str(b) for b in repo.heads]

        for branch in repo.heads:
            # Iterate through every commit for the given branch in the repository
            for commit in repo.iter_commits(branch):
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

                    # Update the stats with the additional information
                    opath = Path(os.path.join(self._git_path.path_virtual, objpath))
                    stats.update({
                        'object': str(objpath),
                        'commit': commit.hexsha,
                        'author': commit.author.email,
                        'timestamp': commit.authored_datetime.strftime(self._DATE_TIME_FORMAT),
                        'size': self._diff_size(diff),
                        'type': self._diff_type(diff),
                    })

                    content = ''
                    mime = ''
                    if diff.a_blob is not None:
                        content += f"--- {objpath}\n"
                        content += diff.a_blob.data_stream.read().decode('utf-8')
                        mime = Tools.get_mimes(diff.a_blob.data_stream.read().decode('utf-8'))

                    if diff.b_blob is not None:
                        content += f"\n\n+++ {objpath}\n"
                        content += diff.b_blob.data_stream.read().decode('utf-8')
                        mime = Tools.get_mimes(diff.b_blob.data_stream.read().decode('utf-8'))

                    yield dict(
                        fingerprint=self._diff_fingerprint(stats),
                        filename=opath.name,
                        extension=opath.suffix,
                        mime_type=mime,
                        file_size=self._diff_size(diff),
                        created=commit.authored_datetime,
                        last_accessed=commit.authored_datetime,
                        last_modified=commit.authored_datetime,
                        indexing_date=datetime.datetime.utcnow(),
                        path_real=self._git_path.path_real,
                        path_virtual=f'{self._git_path.path_virtual}/<gitcommit>/{commit.hexsha}/{objpath.strip("/")}',
                        metadata=json.dumps(stats, default=Tools.json_serial),
                        content=content
                    )

    def _diff_fingerprint(self, stats):
        sha1sum = hashlib.sha1()
        sha1sum.update(f'{self._git_path}'.encode("utf-8"))
        sha1sum.update(json.dumps(stats, default=Tools.json_serial).encode("utf-8"))

        return sha1sum.hexdigest()

    @classmethod
    def _diff_size(cls, diff):
        """
        Computes the size of the diff by comparing the size of the blobs.
        """
        if diff.b_blob is None and diff.deleted_file:
            # This is a deletion, so return negative the size of the original.
            return diff.a_blob.size * -1

        if diff.a_blob is None and diff.new_file:
            # This is a new file, so return the size of the new value.
            return diff.b_blob.size

        # Otherwise just return the size a-b
        return diff.a_blob.size - diff.b_blob.size

    @classmethod
    def _diff_type(cls, diff):
        """
        Determines the type of the diff by looking at the diff flags.
        """
        if diff.renamed: return 'R'
        if diff.deleted_file: return 'D'
        if diff.new_file: return 'A'
        return 'M'