# Installation – Building and Installing the APK on Android

This guide explains how to package Pyrri as an Android APK using [Buildozer](https://buildozer.readthedocs.io/) and install it on an Android device.

## Prerequisites

### Development machine (Linux recommended)

- Python 3.10 or later
- `pip` and `pipx`
- Java Development Kit (JDK) 17

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv openjdk-17-jdk \
    git zip unzip libffi-dev libssl-dev libbz2-dev \
    zlib1g-dev build-essential
```

- **Android SDK/NDK** – Buildozer downloads these automatically on the first build.

### Install Buildozer

```bash
pip install buildozer
```

## 1. Initialize Buildozer

From the root of the repository, run:

```bash
buildozer init
```

This creates a `buildozer.spec` file. Open it and adjust at minimum the following settings to match the project:

```ini
[app]
title = Pyrri
package.name = pyrri
package.domain = org.pyrri
source.dir = .
source.include_exts = py,json
version = 0.1.0

requirements = python3,psutil

android.permissions = INTERNET
```

> **Note:** `pywin32` is a Windows-only library and must be excluded from the Android build. Replace any Windows-specific calls with platform-neutral alternatives before building.

## 2. Build the Debug APK

```bash
buildozer android debug
```

Buildozer will:
1. Download the Android SDK and NDK (first run only – this may take several minutes).
2. Compile the Python source and package it together with a Python interpreter.
3. Produce the APK at `bin/pyrri-0.1.0-debug.apk`.

## 3. Build a Release APK (optional)

To create a signed release APK suitable for distribution:

1. Generate a keystore (run once):

   ```bash
   keytool -genkey -v -keystore pyrri-release.keystore \
       -alias pyrri -keyalg RSA -keysize 2048 -validity 10000
   ```

2. Set the keystore details in `buildozer.spec`. To avoid storing credentials in version control, use environment variables:

   ```ini
   android.release_artifact = apk
   android.keystore = pyrri-release.keystore
   android.keystore_password = %(environ.get("KEYSTORE_PASSWORD", ""))s
   android.keyalias = pyrri
   android.keyalias_password = %(environ.get("KEY_PASSWORD", ""))s
   ```

   Export the passwords in your shell before building:

   ```bash
   export KEYSTORE_PASSWORD=<your-keystore-password>
   export KEY_PASSWORD=<your-key-password>
   ```

3. Build:

   ```bash
   buildozer android release
   ```

   The signed APK will be placed at `bin/pyrri-0.1.0-release.apk`.

## 4. Install the APK on an Android Device

### Enable installation from unknown sources

On the Android device, go to **Settings → Security** (or **Settings → Apps → Special app access → Install unknown apps**) and allow installation from your chosen source (e.g., Files app or ADB).

### Option A – Install via ADB (USB cable)

1. Enable **Developer Options** on the device:  
   Go to **Settings → About phone** and tap **Build number** seven times.

2. Enable **USB Debugging** in **Settings → Developer Options**.

3. Connect the device via USB, then run:

   ```bash
   adb install bin/pyrri-0.1.0-debug.apk
   ```

4. Accept any prompts on the device. The app will appear in the app drawer once installation completes.

### Option B – Install by transferring the APK file

1. Copy the APK to the device (via USB storage, email, cloud storage, etc.).
2. Open the APK file from the **Files** app on the device.
3. Follow the on-screen prompts to complete installation.

## 5. Verify the Installation

Open the **Pyrri** app from the device's app drawer. Check the Android logcat output for any runtime errors:

```bash
adb logcat | grep -i pyrri
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Build fails with SDK/NDK errors | Delete the `.buildozer` cache directory and rebuild |
| `adb: device not found` | Check USB cable, enable USB Debugging, and accept the RSA key prompt on the device |
| App crashes immediately | Run `adb logcat` to inspect the Python traceback |
| `pywin32` import error | Remove or stub out Windows-only imports before building |
