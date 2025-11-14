# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions

import os
import sys
from unittest import mock

import he_as
import pytest


def test_parse_args_parses_all_flags(monkeypatch):
    test_args = [
        "prog",
        "kernel.tw",
        "--isa_spec",
        "isa.json",
        "--mem_spec",
        "mem.json",
        "--input_mem_file",
        "custom.mem",
        "--output_dir",
        "out",
        "--output_prefix",
        "pref",
        "--spad_size",
        "32",
        "--hbm_size",
        "64",
        "--no_hbm",
        "--repl_policy",
        he_as.constants.Constants.REPLACEMENT_POLICIES[0],
        "--use_xinstfetch",
        "--suppress_comments",
        "-vv",
    ]
    monkeypatch.setattr(sys, "argv", test_args)
    args = he_as.parse_args()

    assert args.input_file == "kernel.tw"
    assert args.isa_spec_file == "isa.json"
    assert args.mem_spec_file == "mem.json"
    assert args.input_mem_file == "custom.mem"
    assert args.output_dir == "out"
    assert args.output_prefix == "pref"
    assert args.spad_size == 32
    assert args.hbm_size == 64
    assert args.has_hbm is False
    assert args.repl_policy == he_as.constants.Constants.REPLACEMENT_POLICIES[0]
    assert args.use_xinstfetch is True
    assert args.suppress_comments is True
    assert args.debug_verbose == 2


def test_run_config_derives_mem_file(tmp_path):
    input_file = tmp_path / "kernel.tw"
    input_file.write_text("")
    config = he_as.AssemblerRunConfig(input_file=str(input_file))

    assert config.input_file == str(input_file)
    assert config.input_mem_file == str(input_file.with_suffix(".mem"))
    assert config.output_dir == os.path.dirname(os.path.realpath(str(input_file)))
    assert config.input_prefix == "kernel"


def test_main_invokes_assembler_and_creates_outputs(tmp_path, monkeypatch):
    input_file = tmp_path / "kernel.tw"
    input_file.write_text("dummy")
    mem_file = tmp_path / "kernel.mem"
    mem_file.write_text("mem")
    output_dir = tmp_path / "outputs"
    config = he_as.AssemblerRunConfig(
        input_file=str(input_file),
        input_mem_file=str(mem_file),
        output_dir=str(output_dir),
        output_prefix="result",
    )

    asm_mock = mock.Mock(return_value=(1, 2, 3, 4, 5))
    monkeypatch.setattr(he_as, "asmisaAssemble", asm_mock)
    he_as.main(config, verbose=False)

    assert asm_mock.called
    copied_config = asm_mock.call_args.args[0]
    assert copied_config is not config
    for ext in ("minst", "cinst", "xinst"):
        assert (tmp_path / f"outputs/result.{ext}").is_file()


def test_run_config_requires_input_file():
    """Test that AssemblerRunConfig raises TypeError when input_file is missing."""
    with pytest.raises(TypeError, match="Expected value for configuration `input_file`"):
        he_as.AssemblerRunConfig()


def test_run_config_defaults(tmp_path):
    """Test that AssemblerRunConfig sets sensible defaults."""
    input_file = tmp_path / "kernel.tw"
    input_file.write_text("")
    config = he_as.AssemblerRunConfig(input_file=str(input_file))

    assert config.has_hbm is True
    assert config.hbm_size == he_as.AssemblerRunConfig.DEFAULT_HBM_SIZE_KB
    assert config.spad_size == he_as.AssemblerRunConfig.DEFAULT_SPAD_SIZE_KB
    assert config.repl_policy == he_as.AssemblerRunConfig.DEFAULT_REPL_POLICY


def test_run_config_custom_output_dir(tmp_path):
    """Test that custom output_dir is respected."""
    input_file = tmp_path / "kernel.tw"
    input_file.write_text("")
    custom_dir = tmp_path / "custom_output"

    config = he_as.AssemblerRunConfig(
        input_file=str(input_file),
        output_dir=str(custom_dir),
    )

    assert config.output_dir == str(custom_dir)


def test_main_creates_output_directory(tmp_path, monkeypatch):
    """Test that main creates output directory if it doesn't exist."""
    input_file = tmp_path / "kernel.tw"
    input_file.write_text("dummy")
    mem_file = tmp_path / "kernel.mem"
    mem_file.write_text("mem")
    output_dir = tmp_path / "new_outputs"

    config = he_as.AssemblerRunConfig(
        input_file=str(input_file),
        input_mem_file=str(mem_file),
        output_dir=str(output_dir),
    )

    asm_mock = mock.Mock(return_value=(1, 2, 3, 4, 5))
    monkeypatch.setattr(he_as, "asmisaAssemble", asm_mock)

    assert not output_dir.exists()
    he_as.main(config, verbose=False)
    assert output_dir.exists()


def test_main_output_not_writable_raises_exception(tmp_path, monkeypatch):
    """Test that main raises exception when output location is not writable."""
    input_file = tmp_path / "kernel.tw"
    input_file.write_text("dummy")
    mem_file = tmp_path / "kernel.mem"
    mem_file.write_text("mem")
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    os.chmod(output_dir, 0o444)  # Read-only

    config = he_as.AssemblerRunConfig(
        input_file=str(input_file),
        input_mem_file=str(mem_file),
        output_dir=str(output_dir),
    )

    with pytest.raises(Exception, match="Failed to write to output location"):
        he_as.main(config, verbose=False)


def test_main_sets_global_config(tmp_path, monkeypatch):
    """Test that main correctly sets GlobalConfig values."""
    input_file = tmp_path / "kernel.tw"
    input_file.write_text("dummy")
    mem_file = tmp_path / "kernel.mem"
    mem_file.write_text("mem")

    config = he_as.AssemblerRunConfig(
        input_file=str(input_file),
        input_mem_file=str(mem_file),
        has_hbm=False,
        use_xinstfetch=True,
        suppress_comments=True,
        debug_verbose=2,
    )

    asm_mock = mock.Mock(return_value=(1, 2, 3, 4, 5))
    monkeypatch.setattr(he_as, "asmisaAssemble", asm_mock)

    he_as.main(config, verbose=False)

    assert he_as.GlobalConfig.hasHBM is False
    assert he_as.GlobalConfig.useXInstFetch is True
    assert he_as.GlobalConfig.suppress_comments is True
    assert he_as.GlobalConfig.debugVerbose == 2


def test_main_verbose_output(tmp_path, monkeypatch, capsys):
    """Test that main prints verbose output when enabled."""
    input_file = tmp_path / "kernel.tw"
    input_file.write_text("dummy")
    mem_file = tmp_path / "kernel.mem"
    mem_file.write_text("mem")

    config = he_as.AssemblerRunConfig(
        input_file=str(input_file),
        input_mem_file=str(mem_file),
    )

    asm_mock = mock.Mock(return_value=(10, 2, 5, 1.5, 2.5))
    monkeypatch.setattr(he_as, "asmisaAssemble", asm_mock)

    he_as.main(config, verbose=True)

    captured = capsys.readouterr()
    assert "Output:" in captured.out
    assert "Total XInstructions: 10" in captured.out
    assert "Deps time: 1.5" in captured.out
    assert "Scheduling time: 2.5" in captured.out
    assert "Minimum idle cycles: 5" in captured.out
    assert "Minimum nops required: 2" in captured.out


def test_config_as_dict(tmp_path):
    """Test that AssemblerRunConfig.as_dict returns all config values."""
    input_file = tmp_path / "kernel.tw"
    input_file.write_text("")

    config = he_as.AssemblerRunConfig(
        input_file=str(input_file),
        has_hbm=False,
        hbm_size=128,
    )

    config_dict = config.as_dict()
    assert "input_file" in config_dict
    assert "has_hbm" in config_dict
    assert config_dict["has_hbm"] is False
    assert config_dict["hbm_size"] == 128


def test_config_str_representation(tmp_path):
    """Test that AssemblerRunConfig has a string representation."""
    input_file = tmp_path / "kernel.tw"
    input_file.write_text("")

    config = he_as.AssemblerRunConfig(input_file=str(input_file))
    config_str = str(config)

    assert "input_file" in config_str
    assert str(input_file) in config_str
