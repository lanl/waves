"""Test WAVES

Test waves.py
"""
import pathlib
from unittest.mock import patch, mock_open

import pytest

from waves import main
from waves import _settings


@pytest.mark.unittest
def test_main():
    with patch('sys.argv', ['waves.py', 'docs']), \
         patch("waves.main.docs") as mock_docs:
        main.main()
        mock_docs.assert_called()

    target_string = 'dummy.target'
    with patch('sys.argv', ['waves.py', 'build', target_string]), \
         patch("waves.main.build") as mock_build:
        main.main()
        mock_build.assert_called_once()
        mock_build.call_args[0] == [target_string]

    # TODO: deprecate the quickstart subcommand in v1
    project_directory = 'project_directory'
    with patch('sys.argv', ['waves.py', 'quickstart', project_directory]), \
         patch("waves.fetch.recursive_copy") as mock_recursive_copy:
        main.main()
        mock_recursive_copy.assert_called_once()
        assert mock_recursive_copy.call_args[0][2] == pathlib.Path(project_directory)

    requested_paths = ['dummy.file1', 'dummy.file2']
    with patch('sys.argv', ['waves.py', 'fetch'] + requested_paths), \
         patch("waves.fetch.recursive_copy") as mock_recursive_copy:
        main.main()
        mock_recursive_copy.assert_called_once()
        assert mock_recursive_copy.call_args[1]['requested_paths'] == requested_paths


@pytest.mark.unittest
def test_docs():
    with patch('webbrowser.open') as mock_webbrowser_open:
        main.docs()
        # Make sure the correct type is passed to webbrowser.open
        mock_webbrowser_open.assert_called_with(str(_settings._installed_docs_index))

    with patch('webbrowser.open') as mock_webbrowser_open, \
         patch('pathlib.Path.exists', return_value=True):
        return_code = main.docs(print_local_path=True)
        assert return_code == 0
        mock_webbrowser_open.assert_not_called()

    # Test the "unreachable" exit code used as a sign-of-life that the installed package structure assumptions in
    # _settings.py are correct.
    with patch('webbrowser.open') as mock_webbrowser_open, \
         patch('pathlib.Path.exists', return_value=False):
        return_code = main.docs(print_local_path=True)
        assert return_code != 0
        mock_webbrowser_open.assert_not_called()


@pytest.mark.unittest
def test_build():
    with patch('subprocess.check_output', return_value=b"is up to date.") as mock_check_output:
        main.build(['dummy.target'])
        mock_check_output.assert_called_once()

    with patch('subprocess.check_output', return_value=b"is up to date.") as mock_check_output, \
         patch("pathlib.Path.mkdir") as mock_mkdir:
        main.build(['dummy.target'], git_clone_directory='dummy/clone')
        assert mock_check_output.call_count == 2


@pytest.mark.unittest
def test_fetch():
    # Test the "unreachable" exit code used as a sign-of-life that the installed package structure assumptions in
    # _settings.py are correct.
    with patch("waves.fetch.recursive_copy") as mock_recursive_copy:
        return_code = main.fetch("dummy_subcommand", pathlib.Path("/directory/assumptions/are/wrong"),
                                 ["dummy/relative/path"], "/dummy/destination")
        assert return_code != 0
        mock_recursive_copy.assert_not_called()


parameter_study_args = {  #               subcommand,         class_name,                   argument,         option,   argument_value
    'cartesian product':        ('cartesian_product', 'CartesianProduct',                       None,           None,             None),
    'custom study':             (     'custom_study',      'CustomStudy',                       None,           None,             None),
    'latin hypercube':          (  'latin_hypercube',   'LatinHypercube',                       None,           None,             None),
    'sobol sequence':           (   'sobol_sequence',    'SobolSequence',                       None,           None,             None),
    'output file template':     ('cartesian_product', 'CartesianProduct',     'output_file_template',           '-o', 'dummy_template'),
    'output file':              (     'custom_study',      'CustomStudy',              'output_file',           '-f', 'dummy_file.txt'),
    'output file type':         (  'latin_hypercube',   'LatinHypercube',         'output_file_type',           '-t',             'h5'),
    'set name template':        (   'sobol_sequence',    'SobolSequence',        'set_name_template',           '-s',        '@number'),
    'previous parameter study': ('cartesian_product', 'CartesianProduct', 'previous_parameter_study',           '-p', 'dummy_file.txt'),
    'overwrite':                (     'custom_study',      'CustomStudy',                'overwrite',  '--overwrite',             True),
    'dry run':                  (  'latin_hypercube',   'LatinHypercube',                   'dryrun',     '--dryrun',             True),
    'write meta':               (   'sobol_sequence',    'SobolSequence',               'write_meta', '--write-meta',             True)
}


@pytest.mark.integrationtest
@pytest.mark.parametrize('subcommand, class_name, argument, option, argument_value',
                         parameter_study_args.values(),
                         ids=list(parameter_study_args.keys()))
def test_parameter_study(subcommand, class_name, argument, option, argument_value):
    # Help/usage. Should not raise
    with patch('sys.argv', ['main.py', subcommand, '-h']), \
         pytest.raises(SystemExit) as err:
        main.main()
    assert err.value.code == 0

    # Run main code. No SystemExit expected.
    arg_list = ['main.py', subcommand, 'dummy.file']
    if option:
        arg_list.append(option)
    if argument_value:
        # Don't pass boolean values
        if not type(argument_value) == bool:
            arg_list.append(argument_value)
    with patch('sys.argv', arg_list), \
            patch('builtins.open', mock_open()), patch('yaml.safe_load'), \
            patch(f'waves.parameter_generators.{class_name}') as mock_generator:
        exit_code = main.main()
        assert exit_code == 0
        mock_generator.assert_called_once()
        if argument:
            assert mock_generator.call_args.kwargs[argument] == argument_value
