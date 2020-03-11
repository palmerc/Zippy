import zippy
import tempfile
import unittest
import pathlib
import os


class TestZippy (unittest.TestCase):
    def setUp(self) -> None:
        self.zippy = zippy.Zippy()

    @staticmethod
    def create_hello_file(path):
        f = open(path, 'w')
        f.write('Hello, world!\n')
        f.close()

    def test_add_dir_entry(self):
        directory = 'a/b/c/d'
        self.zippy.add_dir_entry(directory)
        zi = self.zippy.zip.getinfo(directory + '/')
        self.assertTrue(zi.is_dir(), 'Expected a directory')

    def test_add_symlink(self):
        directory = 'a/b/c/d'
        link = 'symlink'
        symlink_attr = 0xA0000000
        self.zippy.add_symlink(link, directory)
        zi = self.zippy.zip.getinfo(link)
        self.assertTrue(zi.external_attr & symlink_attr, 'Expected a valid symlink')

    def test_add_path_with_directory_symlink(self):
        directory = 'a/b/c/d'
        link = 'symlink'
        symlink_attr = 0xA0000000
        with tempfile.TemporaryDirectory() as td:
            fq_dir = os.path.join(os.path.abspath(td), directory)
            fq_link = os.path.join(os.path.abspath(td), link)
            os.makedirs(fq_dir, mode=0o755)
            os.symlink(fq_dir, fq_link, True)
            path = pathlib.Path(fq_link)

            self.zippy.add_path(path)

            zi = self.zippy.zip.getinfo(fq_link)
        self.assertEqual(symlink_attr, zi.external_attr & symlink_attr, 'Expected a valid symlink')

    def test_add_bytes(self):
        filename = 'filename.bin'
        self.zippy.add_bytes(b'ABC', filename)
        zi = self.zippy.zip.getinfo(filename)
        self.assertFalse(zi.is_dir(), 'Expected a file, is a directory')

    def test_add_path_file(self):
        filename = 'filename.txt'
        with tempfile.TemporaryDirectory() as td:
            fq_file = os.path.join(os.path.abspath(td), filename)

            f = open(fq_file, 'w')
            f.write('Hello, world!\n')
            f.close()
            path = pathlib.Path(fq_file)

            self.zippy.add_path(path)

            zip_path = fq_file.lstrip('/')
            zi = self.zippy.zip.getinfo(zip_path)
        self.assertFalse(zi.is_dir(), 'Expected a file, is a directory')
        self.assertEqual(zi.filename, zip_path, 'Expected a file, is not found')

    def test_add_path_file_symlink(self):
        filename = 'filename.txt'
        link = 'filename.symlink'
        symlink_attr = 0xA0000000

        with tempfile.TemporaryDirectory() as td:
            tempdir = os.path.abspath(td)
            fq_file = os.path.join(tempdir, filename)
            fq_link = os.path.join(tempdir, link)

            f = open(fq_file, 'w')
            f.write('Hello, world!\n')
            f.close()
            os.symlink(fq_file, fq_link)
            path = pathlib.Path(fq_link)

            self.zippy.add_path(path)

            zi = self.zippy.zip.getinfo(fq_link)
        self.assertEqual(zi.filename, fq_link, 'Expected a file, is not found')
        self.assertEqual(symlink_attr, zi.external_attr & symlink_attr, 'Expected a valid symlink')

    def test_generate_listing(self):
        directory = 'a/b/c/d'
        filename = 'filename.txt'
        with tempfile.TemporaryDirectory() as td:
            tempdir = os.path.abspath(td)
            fq_dir = os.path.join(tempdir, directory)
            os.makedirs(fq_dir, mode=0o755)

            fq_file = os.path.join(tempdir, filename)
            TestZippy.create_hello_file(fq_file)

            path = pathlib.Path(tempdir)
            globd = sorted(path.glob('**/*'))
            globd.insert(0, path)
            listing = zippy.Zippy.generate_listing(path)
        self.assertCountEqual(globd, listing, 'Unexpected items in generated list')

    def test_generate_listing_with_directory_symlinks(self):
        directory = 'a/b/c/d'
        link = 'symlink'
        filename = 'filename.txt'
        with tempfile.TemporaryDirectory() as td:
            tempdir = os.path.abspath(td)
            fq_dir = os.path.join(tempdir, directory)
            fq_link = os.path.join(tempdir, link)

            os.makedirs(fq_dir, mode=0o755)
            os.symlink(fq_dir, fq_link, True)

            fq_file = os.path.join(tempdir, filename)
            TestZippy.create_hello_file(fq_file)

            path = pathlib.Path(tempdir)
            globd = sorted(path.glob('**/*'))
            globd.insert(0, path)
            listing = zippy.Zippy.generate_listing(path)
        self.assertCountEqual(globd, listing, 'Unexpected items in generated list')

    def test_add_tree(self):
        directory = 'a/b/c/d'
        filename = 'filename.txt'
        with tempfile.TemporaryDirectory() as td:
            tempdir = os.path.abspath(td)
            fq_dir = os.path.join(tempdir, directory)
            os.makedirs(fq_dir, mode=0o755)

            fq_file = os.path.join(tempdir, filename)
            TestZippy.create_hello_file(fq_file)

            path = pathlib.Path(tempdir)
            self.zippy.add_tree(path)


if __name__ == '__main__':
    unittest.main()
