import zipfile
import os
import io
import pathlib


class Zippy:
    verbose = False

    def __init__(self, path=None):
        if isinstance(path, str):
            path = pathlib.Path(path)

        self.path = path
        ### Do we need this instance variable?
        self.in_memory_zip = io.BytesIO()
        self.zip = zipfile.ZipFile(self.in_memory_zip,
                                   mode='w',
                                   compression=zipfile.ZIP_DEFLATED)

    def __enter__(self):
        return self

    def __exit__(self, t, v, tb):
        self.close()

    def close(self):
        try:
            self.zip.close()
            if self.path:
                with open(self.path, 'wb') as f:
                    self.in_memory_zip.seek(0)
                    f.write(self.in_memory_zip.read())

        except IOError:
            pass

    def content(self):
        return self.in_memory_zip

    def log(self, *string):
        if self.verbose:
            print(' '.join(string))

    @staticmethod
    def _to_path(path):
        if isinstance(path, str):
            path = pathlib.Path(path)
        return path

    @staticmethod
    def _clean_path(path):
        return Zippy._to_path(path).as_posix()

    def add_symlink(self, link, target, permissions=0o777):
        link = Zippy._clean_path(link)

        self.log('Adding a symlink: {} => {}'.format(link, target))
        permissions |= 0xA000

        zi = zipfile.ZipInfo(link)
        zi.create_system = 3
        zi.external_attr = permissions << 16
        self.zip.writestr(zi, target)

    def add_dir_entry(self, path):
        zip_path = Zippy._clean_path(path)

        self.log("Adding directory:", zip_path)
        zip_dir = zip_path + '/'
        if zip_dir in self.zip.namelist():
            raise FileExistsError('{} already exists in Zip'.format(zip_dir))
        self.add_bytes('', zip_dir)

    def add_file(self, path, zip_path=None):
        path = Zippy._to_path(path)

        if not zip_path:
            zip_path = Zippy._clean_path(path)

        if not path.is_file():
            raise Exception('Not a regular file: ' + str(path))
        self.log("Adding file:", zip_path)

        if zip_path in self.zip.namelist():
            raise FileExistsError('{} already exists in Zip'.format(zip_path))
        self.zip.write(path, arcname=zip_path)

    def add_path(self, path, zip_path=None):
        path = Zippy._to_path(path)

        if not zip_path:
            zip_path = Zippy._clean_path(path)

        if path.is_symlink():
            linked_to = os.readlink(path)
            permissions = os.lstat(path).st_mode & 0o0777
            self.add_symlink(zip_path, linked_to, permissions)
        elif path.is_file():
            self.add_file(path, zip_path)
        elif path.is_dir():
            if not zip_path == '.':
                self.add_dir_entry(pathlib.Path(zip_path))
        else:
            raise Exception('Bad path: ' + str(path))

    def add_tree(self, path):
        if isinstance(path, str):
            path = pathlib.Path(path)

        if not path.exists():
            raise FileNotFoundError('Path does not exist: ' + str(path))
        self.log("Adding tree:", path.as_posix())

        items = Zippy.generate_listing(path)
        for item in items:
            zip_path = os.path.relpath(item, path)
            self.add_path(item, zip_path)

    def add_bytes(self, data, zip_path):
        self.log("Adding bytes:", zip_path)
        if zip_path in self.zip.namelist():
            raise FileExistsError('{} already exists in Zip'.format(zip_path))

        self.zip.writestr(zip_path, data)

    def add_zip_contents(self, zip_file):
        with zipfile.ZipFile(zip_file, mode='r') as z:
            for item_name in z.namelist():
                item_bytes = z.read(item_name)
                self.add_bytes(item_bytes, item_name)

    @staticmethod
    def generate_listing(path, abspath=True):
        if isinstance(path, str):
            path = pathlib.Path(path)

        if path.is_file():
            return [path]

        listing = []
        for root, directories, files in os.walk(path):
            root_path = pathlib.Path(root)
            if abspath:
                root_path = root_path.absolute()
            listing.append(root_path)
            for directory in directories:
                directory_path = root_path.joinpath(directory)
                if directory_path.is_symlink():
                    listing.append(directory_path)
            for file in files:
                listing.append(root_path.joinpath(file))
        return listing
