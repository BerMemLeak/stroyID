"""Remove retired empty directories; never remove unknown files or follow symlinks."""

import errno
from pathlib import Path


class EmptyDirectoryCleaner:
    def clean(self, root: Path, retired, protected):
        protected = set(protected) | {root}
        for path in list(protected):
            protected.update(p for p in path.parents if p.is_relative_to(root))
        candidates = set()
        for relative in retired:
            candidate = root / relative
            chain = [candidate, *candidate.parents]
            if any(p.is_symlink() for p in chain if p.is_relative_to(root)):
                continue
            folder = candidate.resolve()
            while folder.is_relative_to(root) and folder not in protected:
                candidates.add(folder)
                folder = folder.parent
        roots = []
        for folder in sorted(candidates, key=lambda p: len(p.parts)):
            if not any(folder.is_relative_to(parent) for parent in roots):
                roots.append(folder)
        pending = []

        def prune(folder):
            if folder in protected or folder.is_symlink() or not folder.is_dir():
                return
            try:
                for child in folder.iterdir():
                    if child.is_dir() and not child.is_symlink():
                        prune(child)
                folder.rmdir()
            except OSError as error:
                if error.errno not in (errno.ENOENT, errno.ENOTEMPTY, errno.EEXIST):
                    pending.append(folder.relative_to(root).as_posix())

        for folder in roots:
            prune(folder)
        return pending
