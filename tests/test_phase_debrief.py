import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scripts.phase_debrief as pd


def test_argparse_init():
    args = pd.build_parser().parse_args(
        ['--role', 'TestRole', '--stage', 'hiring_manager', '--init']
    )
    assert args.role == 'TestRole'
    assert args.stage == 'hiring_manager'
    assert args.init is True
    assert args.convert is False
    assert args.interactive is False


def test_argparse_convert():
    args = pd.build_parser().parse_args(
        ['--role', 'TestRole', '--stage', 'hiring_manager', '--convert']
    )
    assert args.convert is True
    assert args.init is False


def test_argparse_interactive():
    args = pd.build_parser().parse_args(
        ['--role', 'TestRole', '--stage', 'hiring_manager', '--interactive']
    )
    assert args.interactive is True
    assert args.init is False


def test_argparse_mutually_exclusive():
    with pytest.raises(SystemExit):
        pd.build_parser().parse_args(
            ['--role', 'R', '--stage', 'hiring_manager', '--init', '--convert']
        )


def test_argparse_invalid_stage():
    with pytest.raises(SystemExit):
        pd.build_parser().parse_args(
            ['--role', 'R', '--stage', 'bad_stage', '--init']
        )
