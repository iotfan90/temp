import hashlib
import os

from django.core.files.storage import FileSystemStorage


class OverwriteMixin(object):
    """
    Update get_available_name to remove any previously stored file (if any)
    before returning the name.
    """

    def get_available_name(self, name):
        self.delete(name)
        return name


class MultipleLevelMixin(object):
    """
    Creates a multi-level directory structure for saving files.
    """

    def md5sum(self, input_file):
        """
        Calculate the md5 checksum of a file-like object without reading its
        whole content in memory.
        """
        m = hashlib.md5()
        while True:
            d = input_file.read(8096)
            if not d:
                break
            m.update(d)
        return m.hexdigest()

    def _save(self, name, content):
        original_name = name.split('/')
        key = self.md5sum(content)
        new_name = "%s.%s" % (key, original_name[-1].split('.')[-1])
        name = os.path.join(original_name[0], key[0:2], key[2:4], new_name)
        return super(MultipleLevelMixin, self)._save(name, content)


class MultipleLevelFileSystemStorage(MultipleLevelMixin, FileSystemStorage):
    """
    A file-system based storage that let create multiple level directory for
    saving files.
    """


class OverwriteFileSystemStorage(OverwriteMixin, FileSystemStorage):
    """
    A file-system based storage that let overwrite files with the same name.
    """
