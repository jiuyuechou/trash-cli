import os
import unittest
from trashcli.restore import RestoreCmd
from .files import require_empty_dir
from trashcli.fs import remove_file
from .fake_trash_dir import a_trashinfo
from .files import write_file
from unit_tests.myStringIO import StringIO


class TestRestoreTrash(unittest.TestCase):
    def test_it_does_nothing_when_no_file_have_been_found_in_current_dir(self):
        self.user.chdir('/')

        self.user.run_restore()

        self.assertEqual("No files trashed from current dir ('/')\n",
                         self.user.stdout())

    def test_gives_an_error_on_not_a_number_input(self):
        self.user.having_a_trashed_file('/foo/bar')
        self.user.chdir('/foo')

        self.user.run_restore(with_user_typing='-@notanumber')

        self.assertEqual('Invalid entry\n', self.user.stderr())

    def test_it_gives_error_when_user_input_is_too_small(self):
        self.user.having_a_trashed_file('/foo/bar')
        self.user.chdir('/foo')

        self.user.run_restore(with_user_typing='-1')

        self.assertEqual('Invalid entry\n', self.user.stderr())

    def test_it_gives_error_when_user_input_is_too_large(self):
        self.user.having_a_trashed_file('/foo/bar')
        self.user.chdir('/foo')

        self.user.run_restore(with_user_typing='1')

        self.assertEqual('Invalid entry\n', self.user.stderr())

    def test_it_shows_the_file_deleted_from_the_current_dir(self):
        self.user.having_a_trashed_file('/foo/bar')
        self.user.chdir('/foo')

        self.user.run_restore(with_user_typing='')

        self.assertEqual('   0 2000-01-01 00:00:01 /foo/bar\n'
                         'Exiting\n', self.user.stdout())
        self.assertEqual('', self.user.stderr())

    def test_it_restores_the_file_selected_by_the_user(self):
        self.user.having_a_file_trashed_from_current_dir('foo')
        self.user.chdir(os.getcwd())

        self.user.run_restore(with_user_typing='0')

        self.file_should_have_been_restored('foo')

    def test_it_refuses_overwriting_existing_file(self):
        self.user.having_a_file_trashed_from_current_dir('foo')
        self.user.chdir(os.getcwd())
        write_file("foo")

        self.user.run_restore(with_user_typing='0')

        self.assertEqual('Refusing to overwrite existing file "foo".\n',
                         self.user.stderr())

    def setUp(self):
        require_empty_dir('XDG_DATA_HOME')
        self.user = RestoreTrashUser('XDG_DATA_HOME')

    def file_should_have_been_restored(self, filename):
        assert os.path.exists(filename)


class RestoreTrashUser:
    def __init__(self, XDG_DATA_HOME):
        self.XDG_DATA_HOME = XDG_DATA_HOME
        self.out = StringIO()
        self.err = StringIO()

    def chdir(self, dir):
        self.current_dir = dir

    def run_restore(self, with_user_typing=''):
        RestoreCmd(
            stdout  = self.out,
            stderr  = self.err,
            environ = {'XDG_DATA_HOME': self.XDG_DATA_HOME},
            exit    = [].append,
            input   = lambda msg: with_user_typing,
            curdir  = lambda: self.current_dir
        ).run([])

    def having_a_file_trashed_from_current_dir(self, filename):
        self.having_a_trashed_file(os.path.join(os.getcwd(), filename))
        remove_file(filename)
        assert not os.path.exists(filename)

    def having_a_trashed_file(self, path):
        write_file('%s/info/foo.trashinfo' % self._trash_dir(),
                   a_trashinfo(path))
        write_file('%s/files/foo' % self._trash_dir())

    def _trash_dir(self):
        return "%s/Trash" % self.XDG_DATA_HOME

    def stdout(self):
        return self.out.getvalue()

    def stderr(self):
        return self.err.getvalue()
