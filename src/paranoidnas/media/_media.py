import enum
import io
import logging
import pkgutil
from pathlib import Path
from typing import Any, BinaryIO, Collection, ContextManager, cast

from ruamel import yaml
from ruamel.yaml.comments import CommentedMap, CommentedSeq

from isomodder import AutoInstallBuilder, IsoFile, ProgressReporter, UbuntuServerIsoFetcher

from ._ui import get_rich


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
    boot_mode: BootMode,
    username: str,
    hostname: str,
    locale: str,
    kb_layout: str,
    authorized_keys: Collection[str],
) -> str:
    template_data = pkgutil.get_data(__name__, "user-data.yaml")
    assert template_data is not None
    template_text = template_data.decode()
    document = yaml.load(template_text, Loader=yaml.RoundTripLoader, preserve_quotes=True)
    data: CommentedMap = document["autoinstall"]

    if boot_mode == BootMode.MBR:
        _convert_to_mbr_storage(data)

    data["identity"]["username"] = username
    data["identity"]["hostname"] = hostname
    data["locale"] = locale
    data["keyboard"]["layout"] = kb_layout

    ssh_keys = data["ssh"]["authorized-keys"]
    if len(authorized_keys) > 0:
        ssh_keys.clear()
        ssh_keys.extend(authorized_keys)
    else:
        del data["ssh"]["authorized-keys"]

    yaml_str = yaml.dump(document, Dumper=yaml.RoundTripDumper, width=4096)
    assert yaml_str is not None
    return yaml_str


def create_paranoidnas_iso(
    working_dir: Path, boot_mode: BootMode, autoinstall_yaml: str, autoinstall_prompt: bool
) -> None:
    fetcher = UbuntuServerIsoFetcher(working_dir=working_dir, release="20.04")
    with get_rich() as progress:
        # Casting because I couldn't get a Protocol to match and mypy doesn't understand ABC register.
        iso_path = fetcher.fetch(cast(ProgressReporter, progress))
    iso_file = IsoFile(iso_path)
    builder = AutoInstallBuilder(
        source_iso=iso_file,
        autoinstall_yaml=autoinstall_yaml,
        grub_entry_stamp="paranoidNAS AutoInstall",
        autoinstall_prompt=autoinstall_prompt,
        supports_efi=(boot_mode == BootMode.EFI),
        supports_mbr=(boot_mode == BootMode.MBR),
    )

    dest_path = Path("/paranoid")
    try:
        source_path = _get_media_content_directory()
        logging.debug(f"Using local filesystem media_content at '{source_path}'.")
        builder.add_from_directory(source_path, dest_path)
    except FileNotFoundError:
        try:
            tar_data = _get_media_content_file()
            builder.add_from_tar(tar_data, dest_path)
            logging.debug("Using media_content.tar from abstract package resource.")
        except FileNotFoundError:
            raise Exception("Broken packaging. Missing media_content directory or tar file.")

    builder.build()
    target_path = working_dir / "paranoidNAS.iso"
    if target_path.exists():
        target_path.unlink()
    with get_rich() as progress:
        iso_file.write_iso(target_path, cast(ProgressReporter, progress))


def _get_media_content_directory() -> Path:
    test_path = Path(__file__).parent / "media_content"
    if not test_path.is_dir():
        raise FileNotFoundError()
    return test_path


class ContextAwareBinaryIO(ContextManager[BinaryIO], BinaryIO):
    ...


def _get_media_content_file() -> ContextAwareBinaryIO:
    try:
        tar_data = pkgutil.get_data(__name__, "media_content.tar")
    except OSError:
        tar_data = None

    if tar_data is None:
        raise FileNotFoundError()

    return cast(ContextAwareBinaryIO, io.BytesIO(tar_data))
