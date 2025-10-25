# Cross-Platform Packaging and Distribution Plan

## Overview

This document outlines the strategy for packaging and distributing the Blue Relay Chat laptop client across Windows, macOS, and Linux platforms.

## Packaging Strategy

### Platform-Specific Approaches

#### Windows
- **Format**: Executable (.exe) with installer
- **Tool**: PyInstaller with NSIS installer
- **Distribution**: GitHub Releases and optional Microsoft Store

#### macOS
- **Format**: Application bundle (.app) with DMG installer
- **Tool**: PyInstaller with create-dmg
- **Distribution**: GitHub Releases and optional Mac App Store

#### Linux
- **Format**: AppImage, deb, and rpm packages
- **Tool**: PyInstaller with platform-specific packaging
- **Distribution**: GitHub Releases and repository packages

## Implementation Details

### 1. Build System Setup

#### Build Script (`scripts/build_laptop_client.py`)
```python
#!/usr/bin/env python3
"""
Build script for cross-platform laptop client packaging.
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path
import argparse

class LaptopClientBuilder:
    """Cross-platform builder for laptop client."""
    
    def __init__(self, output_dir="dist"):
        self.project_root = Path(__file__).parent.parent
        self.output_dir = Path(output_dir)
        self.platform = platform.system().lower()
        self.arch = platform.machine().lower()
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True)
    
    def clean_build(self):
        """Clean previous build artifacts."""
        print("Cleaning previous build artifacts...")
        
        # Remove build directories
        for dir_name in ["build", "dist", "spec"]:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                shutil.rmtree(dir_path)
        
        # Remove Python cache
        for cache_dir in self.project_root.rglob("__pycache__"):
            shutil.rmtree(cache_dir)
        
        # Remove .pyc files
        for pyc_file in self.project_root.rglob("*.pyc"):
            pyc_file.unlink()
    
    def install_dependencies(self):
        """Install build dependencies."""
        print("Installing build dependencies...")
        
        dependencies = [
            "pyinstaller>=5.0.0",
            "setuptools>=65.0.0",
            "wheel>=0.37.0"
        ]
        
        if self.platform == "darwin":
            dependencies.extend([
                "create-dmg>=1.0.0",
                "py2app>=0.28.0"
            ])
        elif self.platform == "linux":
            dependencies.extend([
                "appimage-builder>=1.0.0"
            ])
        elif self.platform == "windows":
            dependencies.extend([
                "nsis>=3.0.0",
                "pywin32>=304"
            ])
        
        subprocess.run([sys.executable, "-m", "pip", "install"] + dependencies, check=True)
    
    def build_executable(self):
        """Build the executable using PyInstaller."""
        print(f"Building executable for {self.platform}...")
        
        # PyInstaller spec file
        spec_file = self.create_spec_file()
        
        # Build command
        cmd = [
            "pyinstaller",
            "--clean",
            "--noconfirm",
            str(spec_file)
        ]
        
        subprocess.run(cmd, check=True, cwd=self.project_root)
    
    def create_spec_file(self):
        """Create PyInstaller spec file."""
        spec_content = f'''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ["main_laptop.py"],
    pathex=["{self.project_root}"],
    binaries=[],
    datas=[
        ("config_laptop.ini", "."),
        ("bitchat", "bitchat"),
        ("README.md", "."),
        ("LICENSE", "."),
    ],
    hiddenimports=[
        "tkinter",
        "tkinter.scrolledtext",
        "tkinter.ttk",
        "asyncio",
        "bleak",
        "cryptography",
        "aiosqlite",
        "lz4",
        "structlog",
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="BlueRelayChat",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
'''
        
        if self.platform == "windows":
            spec_content += '''
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="BlueRelayChat",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/icons/blue_relay_chat.ico",
    version="1.0.0",
    description="Blue Relay Chat - Decentralized Bluetooth Messaging",
    company="Blue Relay Chat Project",
    product_name="Blue Relay Chat",
)
'''
        elif self.platform == "darwin":
            spec_content += '''
app = BUNDLE(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="BlueRelayChat.app",
    icon="assets/icons/blue_relay_chat.icns",
    bundle_identifier="com.bluerelaychat.laptop",
    version="1.0.0",
    info_plist={
        "CFBundleName": "Blue Relay Chat",
        "CFBundleDisplayName": "Blue Relay Chat",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleIdentifier": "com.bluerelaychat.laptop",
        "NSRequiresAquaSystemAppearance": False,
        "LSUIElement": False,
    },
)
'''
        elif self.platform == "linux":
            spec_content += '''
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="BlueRelayChat",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/icons/blue_relay_chat.png",
)
'''
        
        spec_file = self.project_root / "BlueRelayChat.spec"
        with open(spec_file, "w") as f:
            f.write(spec_content)
        
        return spec_file
    
    def create_installer(self):
        """Create platform-specific installer."""
        if self.platform == "windows":
            self.create_windows_installer()
        elif self.platform == "darwin":
            self.create_macos_installer()
        elif self.platform == "linux":
            self.create_linux_packages()
    
    def create_windows_installer(self):
        """Create Windows installer using NSIS."""
        print("Creating Windows installer...")
        
        nsis_script = f'''
!define APP_NAME "Blue Relay Chat"
!define APP_VERSION "1.0.0"
!define APP_PUBLISHER "Blue Relay Chat Project"
!define APP_URL "https://github.com/blue-relay-chat/blue-relay-chat"
!define APP_EXECUTABLE "BlueRelayChat.exe"

Name "${{APP_NAME}}"
OutFile "BlueRelayChat-Setup-${{APP_VERSION}}.exe"
InstallDir "$PROGRAMFILES\\${{APP_NAME}}"
InstallDirRegKey "HKCU\\Software\\${{APP_NAME}}" "InstallDir"
RequestExecutionLevel admin

Page directory
Page instfiles

Section "MainSection" SEC01
    SetOutPath "$INSTDIR"
    File /r "dist\\BlueRelayChat\\*"
    
    CreateDirectory "$SMPROGRAMS\\${{APP_NAME}}"
    CreateShortCut "$SMPROGRAMS\\${{APP_NAME}}\\${{APP_NAME}}.lnk" "$INSTDIR\\${{APP_EXECUTABLE}}"
    CreateShortCut "$SMPROGRAMS\\${{APP_NAME}}\\Uninstall.lnk" "$INSTDIR\\uninstall.exe"
    
    WriteRegStr HKCU "Software\\${{APP_NAME}}" "" "$INSTDIR"
    
    WriteUninstaller "$INSTDIR\\uninstall.exe"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\\uninstall.exe"
    RMDir /r "$INSTDIR"
    Delete "$SMPROGRAMS\\${{APP_NAME}}\\*.*"
    RMDir "$SMPROGRAMS\\${{APP_NAME}}"
    DeleteRegKey HKCU "Software\\${{APP_NAME}}"
SectionEnd
'''
        
        nsis_file = self.project_root / "installer.nsi"
        with open(nsis_file, "w") as f:
            f.write(nsis_script)
        
        # Run NSIS
        subprocess.run(["makensis", str(nsis_file)], check=True)
        
        # Move installer to output directory
        installer_path = self.project_root / "BlueRelayChat-Setup-1.0.0.exe"
        if installer_path.exists():
            shutil.move(installer_path, self.output_dir)
    
    def create_macos_installer(self):
        """Create macOS DMG installer."""
        print("Creating macOS DMG installer...")
        
        app_path = self.project_root / "dist" / "BlueRelayChat.app"
        if not app_path.exists():
            raise FileNotFoundError("Built app not found")
        
        # Create DMG using create-dmg
        dmg_name = "BlueRelayChat-1.0.0.dmg"
        dmg_path = self.output_dir / dmg_name
        
        cmd = [
            "create-dmg",
            "--volname", "Blue Relay Chat",
            "--window-pos", "200", "120",
            "--window-size", "600", "300",
            "--icon-size", "100",
            "--icon", str(app_path),
            "--hide-extension", "BlueRelayChat",
            "--app-drop-link", "600", "185",
            str(dmg_path),
            str(app_path.parent)
        ]
        
        subprocess.run(cmd, check=True)
    
    def create_linux_packages(self):
        """Create Linux packages (AppImage, deb, rpm)."""
        print("Creating Linux packages...")
        
        # Create AppImage
        self.create_appimage()
        
        # Create deb package
        self.create_deb_package()
        
        # Create rpm package
        self.create_rpm_package()
    
    def create_appimage(self):
        """Create AppImage package."""
        print("Creating AppImage...")
        
        # AppImage builder script
        appdir = self.project_root / "BlueRelayChat.AppDir"
        if appdir.exists():
            shutil.rmtree(appdir)
        
        appdir.mkdir()
        
        # Copy executable
        exe_path = self.project_root / "dist" / "BlueRelayChat"
        shutil.copy2(exe_path, appdir / "BlueRelayChat")
        
        # Create AppRun script
        apprun_content = '''#!/bin/sh
HERE="$(dirname "$(readlink -f "${0}"))"
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
exec "${HERE}/BlueRelayChat" "$@"
'''
        
        apprun_path = appdir / "AppRun"
        with open(apprun_path, "w") as f:
            f.write(apprun_content)
        apprun_path.chmod(0o755)
        
        # Create desktop file
        desktop_content = '''[Desktop Entry]
Type=Application
Name=Blue Relay Chat
Comment=Decentralized Bluetooth Messaging
Exec=BlueRelayChat
Icon=blue_relay_chat
Categories=Network;Chat;
Terminal=false
'''
        
        desktop_dir = appdir / "usr" / "share" / "applications"
        desktop_dir.mkdir(parents=True, exist_ok=True)
        
        with open(desktop_dir / "BlueRelayChat.desktop", "w") as f:
            f.write(desktop_content)
        
        # Copy icon
        icon_dir = appdir / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps"
        icon_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(
            self.project_root / "assets" / "icons" / "blue_relay_chat.png",
            icon_dir / "blue_relay_chat.png"
        )
        
        # Build AppImage
        appimagetool = shutil.which("appimagetool")
        if not appimagetool:
            print("appimagetool not found, skipping AppImage creation")
            return
        
        appimage_name = "BlueRelayChat-1.0.0-x86_64.AppImage"
        appimage_path = self.output_dir / appimage_name
        
        cmd = [appimagetool, str(appdir), str(appimage_path)]
        subprocess.run(cmd, check=True)
    
    def create_deb_package(self):
        """Create Debian package."""
        print("Creating deb package...")
        
        # Use fpm if available
        fpm = shutil.which("fpm")
        if not fpm:
            print("fpm not found, skipping deb package creation")
            return
        
        cmd = [
            fpm,
            "-s", "dir",
            "-t", "deb",
            "-n", "blue-relay-chat",
            "-v", "1.0.0",
            "--description", "Decentralized Bluetooth Messaging",
            "--url", "https://github.com/blue-relay-chat/blue-relay-chat",
            "--license", "MIT",
            "--maintainer", "Blue Relay Chat Project",
            "-C", str(self.project_root / "dist" / "BlueRelayChat"),
            "-p", str(self.output_dir / "blue-relay-chat_1.0.0_amd64.deb")
        ]
        
        subprocess.run(cmd, check=True)
    
    def create_rpm_package(self):
        """Create RPM package."""
        print("Creating RPM package...")
        
        # Use fpm if available
        fpm = shutil.which("fpm")
        if not fpm:
            print("fpm not found, skipping RPM package creation")
            return
        
        cmd = [
            fpm,
            "-s", "dir",
            "-t", "rpm",
            "-n", "blue-relay-chat",
            "-v", "1.0.0",
            "--description", "Decentralized Bluetooth Messaging",
            "--url", "https://github.com/blue-relay-chat/blue-relay-chat",
            "--license", "MIT",
            "--maintainer", "Blue Relay Chat Project",
            "-C", str(self.project_root / "dist" / "BlueRelayChat"),
            "-p", str(self.output_dir / "blue-relay-chat-1.0.0.x86_64.rpm")
        ]
        
        subprocess.run(cmd, check=True)
    
    def build(self):
        """Build all packages for current platform."""
        print(f"Building Blue Relay Chat laptop client for {self.platform}...")
        
        self.clean_build()
        self.install_dependencies()
        self.build_executable()
        self.create_installer()
        
        print("Build completed successfully!")
    
    def build_all(self):
        """Build packages for all platforms (requires cross-compilation)."""
        print("Building for all platforms...")
        
        # This would require cross-compilation setup
        # For now, just build for current platform
        self.build()

def main():
    parser = argparse.ArgumentParser(description="Build Blue Relay Chat laptop client")
    parser.add_argument("--output", "-o", default="dist", help="Output directory")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts only")
    parser.add_argument("--all", action="store_true", help="Build for all platforms")
    
    args = parser.parse_args()
    
    builder = LaptopClientBuilder(args.output)
    
    if args.clean:
        builder.clean_build()
    elif args.all:
        builder.build_all()
    else:
        builder.build()

if __name__ == "__main__":
    main()
```

### 2. CI/CD Pipeline

#### GitHub Actions Workflow (`.github/workflows/build.yml`)
```yaml
name: Build and Release

on:
  push:
    tags:
      - 'v*'
  pull_request:
    branches: [ main ]

jobs:
  build:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: [3.9]
    
    runs-on: ${{ matrix.os }}
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pyinstaller
    
    - name: Build on Linux
      if: matrix.os == 'ubuntu-latest'
      run: |
        sudo apt-get update
        sudo apt-get install -y libxcb-xinerama0 libxcb-cursor0 libxkbcommon-x11-0 libxss1 libgconf-2-4 libxtst6 libxrandr2 libasound2 libpangocairo-1.0-0 libatk1.0-0 libcairo-gobject2 libgtk-3-0 libgdk-pixbuf2.0-0
        python scripts/build_laptop_client.py --output dist
    
    - name: Build on Windows
      if: matrix.os == 'windows-latest'
      run: |
        python scripts/build_laptop_client.py --output dist
    
    - name: Build on macOS
      if: matrix.os == 'macos-latest'
      run: |
        brew install create-dmg
        python scripts/build_laptop_client.py --output dist
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: ${{ matrix.os }}-build
        path: dist/
    
    - name: Release
      if: startsWith(github.ref, 'refs/tags/')
      uses: softprops/action-gh-release@v1
      with:
        files: dist/*
        draft: false
        prerelease: false
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 3. Distribution Strategy

#### GitHub Releases
- **Automatic releases** on version tags
- **Release assets** for all platforms
- **Release notes** with changelog
- **Checksum verification** for security

#### Package Repositories
- **APT repository** for Debian/Ubuntu
- **RPM repository** for Fedora/CentOS
- **Homebrew formula** for macOS
- **Chocolatey package** for Windows

#### Direct Downloads
- **Website downloads** with platform detection
- **CDN distribution** for fast downloads
- **Mirror sites** for redundancy

## Asset Management

### Icons and Graphics
```python
# scripts/create_assets.py
"""
Create application icons and graphics for all platforms.
"""

import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

def create_app_icon():
    """Create application icon in multiple formats."""
    # Create base icon
    size = 512
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw Bluetooth-like icon
    # ... icon drawing code ...
    
    # Save in different formats
    formats = [
        ("assets/icons/blue_relay_chat.ico", (256, 128, 64, 32, 16)),
        ("assets/icons/blue_relay_chat.icns", (512, 256, 128, 64, 32, 16)),
        ("assets/icons/blue_relay_chat.png", (512, 256, 128, 64, 32, 16)),
    ]
    
    for path, sizes in formats:
        if path.endswith('.ico'):
            img.save(path, format='ICO', sizes=[(s, s) for s in sizes])
        elif path.endswith('.icns'):
            img.save(path, format='ICNS', sizes=[(s, s) for s in sizes])
        else:
            for size in sizes:
                resized = img.resize((size, size), Image.LANCZOS)
                resized.save(f"{path.rsplit('.', 1)[0]}_{size}x{size}.png")

def create_splash_screen():
    """Create splash screen for application startup."""
    # Create splash screen
    pass

def create_banners():
    """Create promotional banners and graphics."""
    # Create banners for website
    pass
```

## Security Considerations

### Code Signing
- **Windows**: Code signing certificate
- **macOS**: Developer ID and notarization
- **Linux**: GPG signing for packages

### Checksum Verification
- **SHA256 checksums** for all releases
- **PGP signatures** for verification
- **Automatic verification** in installers

### Dependency Security
- **Vulnerability scanning** of dependencies
- **Regular updates** of build tools
- **Security audit** of build process

## Documentation

### Installation Guides
- **Platform-specific** installation instructions
- **Troubleshooting** guides
- **System requirements** documentation

### User Documentation
- **Getting started** guide
- **Feature documentation**
- **API reference** for developers

## Maintenance and Updates

### Auto-Update Mechanism
- **Update checking** on startup
- **Automatic download** of updates
- **Secure installation** of updates

### Version Management
- **Semantic versioning**
- **Backward compatibility**
- **Migration scripts** for upgrades

This comprehensive packaging and distribution plan ensures that the Blue Relay Chat laptop client can be easily installed and used across all major platforms while maintaining security and providing a smooth user experience.