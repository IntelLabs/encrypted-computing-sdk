# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


# TODO: create also C++ variants of below; given how simple and stable these functions should be just in replicated form, not shared code

import heracles.proto.data_pb2 as hpd
import heracles.proto.common_pb2 as hpc
import heracles.proto.fhe_trace_pb2 as hpf
import google.protobuf.json_format as gpj
import json
import heracles.data.transform as hdt
from google.protobuf.json_format import MessageToJson, MessageToDict
from glob import glob
import re
import sys

# load & store functions
# ===============================


def parse_manifest(filename: str) -> dict:
    manifest = dict()
    with open(filename, "r") as fp:
        cur_field = None
        found_first_field = False
        for linenum, cur_line in enumerate(fp):
            cur_line = cur_line.rstrip()
            if cur_line.startswith("[") and cur_line.endswith("]"):
                cur_field = cur_line[1:-1]
                found_first_field = True
                manifest[cur_field] = dict()
                continue

            if not found_first_field:
                continue
            cur_line_split = cur_line.split("=")
            if len(cur_line_split) != 2:
                print(
                    f"Warning: ignoring incorrect format in line {linenum}",
                    file=sys.stderr,
                )
                continue
            manifest[cur_field][cur_line_split[0]] = cur_line_split[1]

        if not found_first_field:
            raise Exception(f"Incorrect manifest file format: {filename}")

    return manifest


def generate_manifest(filename: str, manifest: dict):
    with open(filename, "w") as fp:
        for field, values in manifest.items():
            fp.write(f"[{field}]\n")
            for key, fn in values.items():
                fp.write(f"{key}={fn}\n")


# re-check
def store_hec_context_json(filename: str, context: hpd.FHEContext):
    print(
        f"Warning: Dumping FHE Context data trace to json can take a long time",
        file=sys.stderr,
    )
    with open(filename, "w") as fp:
        json.dump(MessageToDict(context), fp)


# re-check
def store_testvector_json(filename: str, testvector: hpd.TestVector):
    print(
        f"Warning: Dumping TestVector data trace to json can take a long time",
        file=sys.stderr,
    )
    with open(filename, "w") as fp:
        json.dump(MessageToDict(testvector), fp)


def load_hec_context_from_manifest(manifest: dict) -> hpd.FHEContext:
    context_base_fn = manifest["context"]["main"]
    context_pb = hpd.FHEContext()

    with open(context_base_fn, "rb") as fp:
        context_pb.ParseFromString(fp.read())

    if "rotation_keys" in manifest:
        for ge, gk_fn in manifest["rotation_keys"].items():
            gk_pb = hpd.KeySwitch()
            with open(gk_fn, "rb") as fp:
                gk_pb.ParseFromString(fp.read())
            context_pb.ckks_info.keys.rotation_keys[int(ge)].CopyFrom(gk_pb)

    return context_pb


def store_hec_context(filename: str, context_pb: hpd.FHEContext) -> dict:
    hec_context_manifest = {"context": dict()}
    tmp_context = hpd.FHEContext()
    tmp_context.CopyFrom(context_pb)

    if tmp_context.ByteSize() > 1 << 30:
        hec_context_manifest["rotation_keys"] = dict()
        for gkct, (ge, gk_pb) in enumerate(
            tmp_context.ckks_info.keys.rotation_keys.items()
        ):
            parts_fn = f"{filename}_hec_context_part_{gkct + 1}"
            hec_context_manifest["rotation_keys"][ge] = parts_fn
            with open(parts_fn, "wb") as fp:
                fp.write(gk_pb.SerializeToString())
        tmp_context.ckks_info.keys.ClearField("rotation_keys")

    main_fn = f"{filename}_hec_context_part_0"
    hec_context_manifest["context"]["main"] = main_fn
    with open(main_fn, "wb") as fp:
        fp.write(tmp_context.SerializeToString())

    return hec_context_manifest


def load_testvector_from_manifest(manifest: dict) -> hpd.TestVector:
    # segmented
    testvector_pb = hpd.TestVector()
    if len(manifest["testvector"]) > 1:
        for sym, parts_fn in manifest["testvector"].items():
            data = hpd.Data()
            with open(parts_fn, "rb") as fp:
                data.ParseFromString(fp.read())
            testvector_pb.sym_data_map[sym].CopyFrom(data)
    # whole
    else:
        full_fn = manifest["testvector"]["full"]
        with open(full_fn, "rb") as fp:
            testvector_pb.ParseFromString(fp.read())

    return testvector_pb


def store_testvector(filename: str, testvector_pb: hpd.TestVector) -> dict:
    testvector_manifest = {"testvector": dict()}
    if testvector_pb.ByteSize() > 1 << 30:
        for tvct, (sym, data_pb) in enumerate(testvector_pb.sym_data_map.items()):
            parts_fn = f"{filename}_testvector_part_{tvct}"
            testvector_manifest["testvector"][sym] = parts_fn
            with open(parts_fn, "wb") as fp:
                fp.write(data_pb.SerializeToString())
    else:
        full_fn = f"{filename}_testvector_part_0"
        testvector_manifest["testvector"]["full"] = full_fn
        with open(full_fn, "wb") as fp:
            fp.write(testvector_pb.SerializeToString())

    return testvector_manifest


def load_hec_context(filename: str) -> hpd.FHEContext:
    manifest = parse_manifest(filename)
    return load_hec_context_from_manifest(manifest)


def load_testvector(filename: str) -> hpd.FHEContext:
    manifest = parse_manifest(filename)
    return load_testvector_from_manifest(manifest)


def load_data_trace(filename: str) -> tuple[hpd.FHEContext, hpd.TestVector]:
    manifest = parse_manifest(filename)
    return (
        load_hec_context_from_manifest(manifest),
        load_testvector_from_manifest(manifest),
    )


def store_data_trace(
    filename: str, context_pb: hpd.FHEContext, testvector_pb: hpd.TestVector
):
    generate_manifest(
        filename,
        {
            **store_hec_context(filename, context_pb),
            **store_testvector(filename, testvector_pb),
        },
    )
