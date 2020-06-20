from isomodder import (
    UbuntuServerIsoFetcher,
    IsoFile,
    AutoInstallBuilder,
)
from pathlib import Path
import enum
from ruamel import yaml
import pkgutil
from typing import Any
from ruamel.yaml.comments import CommentedSeq, CommentedMap
import logging
import tarfile
import io
import contextlib
import tempfile


class BootMode(enum.Enum):
    MBR = enum.auto()
    EFI = enum.auto()


def _convert_to_mbr_storage(data: Any) -> None:
    config: CommentedSeq = data["storage"]["config"]
    first_part = next(c for c in config if c["type"] == "partition")
    first_part["id"] = "grub_partition"
    first_part["size"] = "1MB"
    first_part["flag"] = "bios_grub"
    del first_part["grub_device"]

    root_part = next(c for c in config if c["id"] == "root_partition")
    root_part["flag"] = "boot"

    efi_configs = [c for c in config if c["id"].startswith("efi")]
    for c in efi_configs:
        config.remove(c)


def create_paranoidnas_autoinstall_yaml(
    boot_mode: BootMode, username: str, hostname: str, locale: str, kb_layout: str
) -> str:
    template_text = pkgutil.get_data(__name__, "user-data.yaml").decode()
    document = yaml.load(template_text, Loader=yaml.RoundTripLoader, preserve_quotes=True)
    data: CommentedMap = document["autoinstall"]

    if boot_mode == BootMode.MBR:
        _convert_to_mbr_storage(data)
    
    data['identity']['username'] = username
    data['identity']['hostname'] = hostname
    data['locale'] = locale
    data['keyboard']['layout'] = kb_layout

    return yaml.dump(document, Dumper=yaml.RoundTripDumper, width=4096)


def create_paranoidnas_iso(working_dir: Path, boot_mode: BootMode, autoinstall_yaml: str, autoinstall_prompt: bool) -> None:
    fetcher = UbuntuServerIsoFetcher(working_dir=working_dir, release="20.04")
    iso_path = fetcher.fetch()
    iso_file = IsoFile(iso_path)
    builder = AutoInstallBuilder(
        source_iso=iso_file,
        autoinstall_yaml=autoinstall_yaml,
        grub_entry_stamp="paranoidNAS AutoInstall",
        autoinstall_prompt=autoinstall_prompt,
        supports_efi=(boot_mode == BootMode.EFI),
        supports_mbr=(boot_mode == BootMode.MBR),
    )
    with _get_media_path(working_dir) as media_path_str:
        media_path = Path(media_path_str)
        builder.add_directory(media_path, Path("/paranoid"))
        builder.build()
        target_path = working_dir / "paranoidNAS.iso"
        if target_path.exists():
            target_path.unlink()
        iso_file.write_iso(target_path)


def _get_media_path(working_dir: Path) -> Path:
    test_path = Path(__file__).parent / "media_content"
    if test_path.is_dir():
        logging.debug(f"Using local filesystem media_content at '{test_path}'.")
        return contextlib.nullcontext(enter_result=str(test_path))

    try:
        tar_data = pkgutil.get_data(__name__, "media_content.tar")
    except OSError:
        tar_data = None

    if tar_data is None:
        raise Exception("Broken packaging. Missing media_content directory or tar file.")

    temp_dir = tempfile.TemporaryDirectory(dir=working_dir)
    temp_path = Path(temp_dir.name)
    tar_file = tarfile.open(fileobj=io.BytesIO(tar_data), mode="r")
    tar_file.extractall(path=temp_path)
    logging.debug(f"Using abstract tar package resource unpacked at '{temp_path}'.")
    return temp_dir

