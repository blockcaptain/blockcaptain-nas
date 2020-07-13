import enum
import io
import logging
import pkgutil
import re
from pathlib import Path
from typing import Any, BinaryIO, Collection, ContextManager, Optional, cast

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


def detect_timezone() -> Optional[str]:
    local_time_link = Path("/etc/localtime")
    if not local_time_link.is_symlink():
        return None
    match = re.search(r"/zoneinfo/(.+)$", str(local_time_link.resolve()))
    if match:
        return match.group(1)
    return None


def create_paranoidnas_autoinstall_yaml(
    boot_mode: BootMode,
    username: str,
    hostname: str,
    locale: str,
    kb_layout: str,
    timezone: str,
    authorized_keys: Collection[str],
    interactive_storage: bool,
    interactive_network: bool,
) -> str:
    template_data = pkgutil.get_data(__name__, "user-data.yaml")
    assert template_data is not None
    template_text = template_data.decode()
    document = yaml.load(template_text, Loader=yaml.RoundTripLoader, preserve_quotes=True)
    data: CommentedMap = document["autoinstall"]
    user_data: CommentedMap = data["user-data"]

    if boot_mode == BootMode.MBR:
        _convert_to_mbr_storage(data)

    default_user = data["user-data"]["users"][0]
    default_user["name"] = username
    data["late-commands"][1].append(hostname)
    data["locale"] = locale
    data["keyboard"]["layout"] = kb_layout

    ssh_keys = default_user["ssh_authorized_keys"]
    if len(authorized_keys) > 0:
        ssh_keys.clear()
        ssh_keys.extend(authorized_keys)
    else:
        del default_user["ssh_authorized_keys"]

    # Interactivity
    interactive = list(
        filter(None, ["network" if interactive_network else None, "storage" if interactive_storage else None])
    )
    if interactive:
        data["interactive-sections"] = interactive
        logging.info(
            "This ISO is not fully automatic. It has interactive steps that will require console access."
        )
        if interactive_storage:
            logging.warning(
                "Interactive storage configuration is supported, but certain elements must be configured "
                "or installation will fail. See the documentation for more details."
            )

    # Timezone
    detected_timezone = False
    if timezone is None:
        timezone = detect_timezone()
        detected_timezone = timezone is not None

    if timezone:
        logging.info(f"Using {'detected' if detected_timezone else 'provided'} timezone '{timezone}'.")
        user_data["timezone"] = timezone
    else:
        logging.info("Leaving timezone unspecified")

    # Produce new YAML
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
