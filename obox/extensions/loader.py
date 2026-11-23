"""扩展目录的扫描、.oix 安装与清单收集。"""

from __future__ import annotations

import platform

import logging
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

from ..api.errors import ManifestError
from .manifest import Manifest, load_manifest

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExtensionInfo:
    """一个扩展目录的扫描结果。"""

    directory: Path
    manifest: Manifest | None
    error: str | None = None
    origin: str = "source"

    @property
    def ok(self) -> bool:
        return self.manifest is not None


def scan_extensions(root: Path, origin: str = "source") -> list[ExtensionInfo]:
    """目录不存在时返回空列表；非法扩展进入结果但不抛异常。"""
    if not root.exists():
        return []
    infos: list[ExtensionInfo] = []
    for directory in sorted(path for path in root.iterdir() if path.is_dir()):
        if not (directory / "extension.json").exists():
            continue
        try:
            infos.append(
                ExtensionInfo(directory=directory, manifest=load_manifest(directory), origin=origin)
            )
        except ManifestError as exc:
            infos.append(ExtensionInfo(directory=directory, manifest=None, error=str(exc), origin=origin))
    return infos


def install_packages(install_root: Path, package_root: Path | None = None) -> list[Path]:
    """把 package_root 下的 .oix 解压到 install_root/{名称}.{作者}，返回安装目录。"""
    source = package_root or install_root
    if not source.exists():
        return []
    installed: list[Path] = []
    for package in sorted(source.glob("*.oix")):
        try:
            target = install_one(package, install_root)
        except (OSError, zipfile.BadZipFile, ManifestError) as exc:
            LOGGER.warning("安装 %s 失败：%s", package.name, exc)
            continue
        installed.append(target)
    return installed


def package_arch(filename: str) -> str:
    """从包名判断架构：-win-arm64 / -win-x64；无标注视为通用（空串）。"""
    lower = filename.lower()
    if "-win-arm64" in lower:
        return "arm64"
    if "-win-x64" in lower:
        return "x64"
    return ""


def current_arch() -> str:
    machine = platform.machine().lower()
    return "arm64" if machine in ("arm64", "aarch64") else "x64"


def arch_matches(filename: str) -> bool:
    wanted = package_arch(filename)
    return not wanted or wanted == current_arch()


def install_one(package: Path | str, install_root: Path) -> Path:
    """安装单个 .oix 到 install_root/{名称}.{作者}。

    先解压到安装根下的临时目录，校验通过后再替换旧目录；中途失败时旧版本保持可用。
    """
    package = Path(package)
    install_root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(package) as archive:
        manifest_data = _read_manifest(archive, package)
        extension_id = f"{manifest_data['name']}.{manifest_data['publisher']}"
        staging = Path(tempfile.mkdtemp(prefix=".staging-", dir=install_root))
        try:
            for member in archive.namelist():
                _safe_target(staging, member)
            archive.extractall(staging)
            load_manifest(staging)
            target = install_root / extension_id
            backup = install_root / f".{extension_id}.bak"
            if backup.exists():
                shutil.rmtree(backup, ignore_errors=True)
            if target.exists():
                target.rename(backup)
            try:
                staging.rename(target)
            except OSError:
                if backup.exists() and not target.exists():
                    backup.rename(target)
                raise
            if backup.exists():
                shutil.rmtree(backup, ignore_errors=True)
        except BaseException:
            shutil.rmtree(staging, ignore_errors=True)
            raise
    LOGGER.info("已安装扩展 %s -> %s", extension_id, target)
    return target


def remove_one(install_root: Path, extension_id: str) -> bool:
    """删除用户安装目录；目录不存在返回 False。"""
    target = install_root / extension_id
    if not target.is_dir():
        return False
    shutil.rmtree(target)
    LOGGER.info("已卸载扩展 %s", extension_id)
    return True


def _read_manifest(archive: zipfile.ZipFile, package: Path) -> dict:
    try:
        import json

        with archive.open("extension.json") as handle:
            data = json.loads(handle.read().decode("utf-8"))
    except KeyError as exc:
        raise ManifestError(f"{package.name} 缺少 extension.json") from exc
    for key in ("name", "publisher"):
        if not data.get(key):
            raise ManifestError(f"{package.name} 的清单缺少 {key}")
    return data


def _safe_target(target: Path, member: str) -> Path:
    """拒绝越出安装目录的 zip 成员。"""
    resolved = (target / member).resolve()
    base = target.resolve()
    if base != resolved and base not in resolved.parents:
        raise ManifestError(f"压缩包成员越出安装目录：{member}")
    return resolved


def scan_all(roots: list[tuple[Path, str]]) -> list[ExtensionInfo]:
    """按顺序扫描多个根；同名扩展保留先出现者并记录告警。"""
    seen: dict[str, ExtensionInfo] = {}
    seen_roots: set[Path] = set()
    result: list[ExtensionInfo] = []
    for root, origin in roots:
        resolved = root.resolve()
        if resolved in seen_roots:
            continue
        seen_roots.add(resolved)
        for info in scan_extensions(root, origin):
            if info.ok:
                extension_id = info.manifest.extension_id
                if extension_id in seen:
                    LOGGER.warning(
                        "扩展 %s 同时存在于 %s 与 %s，使用前者",
                        extension_id,
                        seen[extension_id].directory,
                        info.directory,
                    )
                    continue
                seen[extension_id] = info
            result.append(info)
    return result


def scan_roots(source_root: Path, install_root: Path) -> list[ExtensionInfo]:
    """扫描两个根；同名扩展以安装目录为准并记录告警。"""
    installed = scan_extensions(install_root, "installed")
    seen = {info.manifest.extension_id: info for info in installed if info.ok}
    infos = list(installed)
    for info in scan_extensions(source_root, "source"):
        if info.ok and info.manifest.extension_id in seen:
            LOGGER.warning("扩展 %s 同时存在于两个根，使用已安装版本", info.manifest.extension_id)
            continue
        infos.append(info)
    return infos