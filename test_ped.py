# -*- coding: utf-8 -*-
import argparse
import pytest
from scripttest import TestFileEnvironment

import ped
from ped.guess_module import guess_module

def test_ped_edits_file(mocker):
    mocker.patch('ped.edit_file')
    ped.ped('pytest')
    path = ped.find_file(pytest)
    ped.edit_file.assert_called_once_with(path, lineno=0, editor=None)

def test_ped_edits_file_with_editor(mocker):
    mocker.patch('ped.edit_file')
    ped.ped('pytest', editor='nano')
    path = ped.find_file(pytest)
    ped.edit_file.assert_called_once_with(path, lineno=0, editor='nano')

def test_import_obj():
    import argparse
    import math
    obj = ped.import_object('argparse')
    assert obj is argparse
    cls = ped.import_object('argparse.ArgumentParser')
    assert cls is argparse.ArgumentParser
    func = ped.import_object('math.acos')
    assert func is math.acos

def test_guess_module():
    assert 'argparse' in guess_module('argpar')
    assert 'argparse.ArgumentParser' in guess_module('argparse.Argu')
    assert guess_module('argparse')[0] == 'argparse'

def test_get_editor_command():
    assert ped.get_editor_command('foo.py', editor='vi') == 'vi "foo.py"'
    assert ped.get_editor_command('foo.py', lineno=2, editor='vi') == 'vi +2 "foo.py"'
    assert ped.get_editor_command('foo.py', lineno=2, editor='gvim') == 'gvim +2 "foo.py"'
    assert ped.get_editor_command('foo.py', lineno=2, editor='kate') == 'kate "foo.py"'
    assert ped.get_editor_command(
        'foo.py', lineno=2, editor='emacs') == 'emacs +2 "foo.py"'

def test_get_info():
    name, fpath, lineno = ped.get_info('argparse.ArgumentPars')
    assert name == 'argparse.ArgumentParser'
    assert fpath == ped.find_file(argparse.ArgumentParser)
    assert lineno == ped.find_source_lines(argparse.ArgumentParser)


# Acceptance tests

import email
import email.mime
from email.mime.message import MIMEMessage

def assert_in_output(s, res, message=None):
    """Assert that a string is in either stdout or std err.
    Included because banners are sometimes outputted to stderr.
    """
    assert any([
        s in res.stdout,
        s in res.stderr
    ]), message or '{0} not in output'.format(s)

class TestAcceptance:

    @pytest.fixture
    def env(self):
        return TestFileEnvironment()

    def test_cli_version(self, env):
        res = env.run('ped', '-v', expect_error=True)
        assert_in_output(ped.__version__ + '\n', res)

    def test_info(self, env):
        res = env.run('ped', '-i', 'email')
        name, path, lineno = res.stdout.split()
        assert name == 'email'
        assert path == ped.find_file(email)
        assert lineno == str(ped.find_source_lines(email))

    def test_info_no_lineno(self, env):
        res = env.run('ped', '-i', 'email.mime')
        name, path = res.stdout.split()
        assert name == 'email.mime'
        assert path == ped.find_file(email.mime)

    def test_info_class(self, env):
        res = env.run('ped', '-i', 'email.mime.message.Mime')
        name, path, lineno = res.stdout.split()
        assert name == 'email.mime.message.MIMEMessage'
        assert path == ped.find_file(MIMEMessage)
        assert lineno == str(ped.find_source_lines(MIMEMessage))

    def test_info_not_found(self, env):
        res = env.run('ped', '-i', 'notfound', expect_error=True)
        assert res.returncode == 1
        expected = 'ERROR: Could not find module in current environment: "notfound"\n'
        assert res.stderr == expected
