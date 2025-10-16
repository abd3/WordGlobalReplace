#!/usr/bin/env python3
"""
Distribution creator for WordGlobalReplace application
Creates a lightweight, distributable package for macOS
"""

import os
import sys
import shutil
import subprocess
import zipfile
from pathlib import Path
import logging
import sysconfig
import json
import tempfile
import textwrap
from typing import Optional

from config import DEFAULT_LOCAL_URL, DEFAULT_REPO_URL, CF_BUNDLE_IDENTIFIER

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DistributionCreator:
    def __init__(self, source_dir=None, output_dir="dist", python_executable=None):
        self.source_dir = source_dir or os.path.dirname(os.path.abspath(__file__))
        self.output_dir = output_dir
        self.app_name = "WordGlobalReplace"
        self.requested_python = python_executable or os.environ.get("WORD_GLOBAL_REPLACE_BUILD_PYTHON")
        self.python_context = None
        
    def create_distribution(self, repo_url=None):
        """Create a distributable package"""
        try:
            # Create output directory
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Create app directory
            app_dir = os.path.join(self.output_dir, f"{self.app_name}.app")
            if os.path.exists(app_dir):
                shutil.rmtree(app_dir)

            contents_dir = os.path.join(app_dir, "Contents")
            macos_dir = os.path.join(contents_dir, "MacOS")
            resources_dir = os.path.join(contents_dir, "Resources")

            os.makedirs(macos_dir, exist_ok=True)
            os.makedirs(resources_dir, exist_ok=True)

            # Copy application files
            self._copy_application_files(resources_dir)
            self._prepare_app_icon(resources_dir)

            # Create Info.plist metadata
            self._create_info_plist(contents_dir)

            # Create launcher scripts
            self._create_launcher_script(macos_dir, resources_dir, repo_url)

            # Create requirements file
            self._create_requirements_file(resources_dir)

            # Create bundled virtual environment
            self._create_virtual_environment(resources_dir)

            # Create README for distribution
            self._create_distribution_readme(resources_dir, repo_url)

            # Create installer script
            self._create_installer_script(resources_dir)
            self._create_cli_launcher_script(resources_dir)

            # Apply ad-hoc code signature so executables survive Gatekeeper checks
            self._codesign_app(app_dir)

            # Create zip package
            self._create_zip_package(app_dir)
            
            logger.info(f"Distribution created successfully in {self.output_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating distribution: {e}")
            return False
    
    def _copy_application_files(self, resources_dir):
        """Copy essential application files"""
        essential_files = [
            'app.py',
            'word_processor.py', 
            'advanced_word_processor.py',
            'auto_updater.py',
            'launcher.py',
            'config.py',
            'templates/',
            'static/',
            'Samples/'
        ]
        
        for item in essential_files:
            src = os.path.join(self.source_dir, item)
            dst = os.path.join(resources_dir, item)
            
            if os.path.exists(src):
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
                logger.info(f"Copied {item}")

    def _prepare_app_icon(self, resources_dir: str):
        """Ensure the application icon (.icns) is available in the bundle."""
        icon_name = "AppIcon.icns"
        destination = Path(resources_dir) / icon_name
        assets_dir = Path(self.source_dir) / "assets"
        iconset = assets_dir / "AppIcon.iconset"
        existing_icns = assets_dir / icon_name

        if destination.exists():
            destination.unlink()

        if iconset.exists():
            iconutil = shutil.which("iconutil")
            if iconutil:
                try:
                    subprocess.run(
                        [
                            iconutil,
                            "--convert",
                            "icns",
                            "--output",
                            str(destination),
                            str(iconset),
                        ],
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                    logger.info("Converted iconset to AppIcon.icns")
                    return
                except subprocess.CalledProcessError as exc:
                    logger.warning("iconutil failed to convert iconset: %s", exc)

        if existing_icns.exists():
            shutil.copy2(existing_icns, destination)
            logger.info("Copied existing AppIcon.icns")
            return

        fallback_png = assets_dir / "AppIcon-1024.png"
        if fallback_png.exists():
            shutil.copy2(fallback_png, destination)
            logger.warning("Using PNG icon as fallback; consider generating AppIcon.icns")
        else:
            logger.warning("Application icon assets not found; Dock icon may be generic.")

    def _create_info_plist(self, contents_dir):
        """Create the macOS Info.plist metadata file"""
        plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>{self.app_name}</string>
    <key>CFBundleIdentifier</key>
    <string>{CF_BUNDLE_IDENTIFIER}</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon.icns</string>
    <key>LSApplicationCategoryType</key>
    <string>public.app-category.productivity</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>CFBundleExecutable</key>
    <string>{self.app_name}</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.9</string>
</dict>
</plist>
'''

        plist_path = os.path.join(contents_dir, "Info.plist")
        with open(plist_path, 'w') as f:
            f.write(plist_content)
        logger.info("Created Info.plist")
    
    def _create_launcher_script(self, macos_dir, resources_dir, repo_url):
        """Create the main launcher scripts for the bundle"""
        run_launcher_content = f'''#!/usr/bin/env python3
"""WordGlobalReplace - Auto-updating launcher"""

import os
import sys
import subprocess
from pathlib import Path
import logging


def main():
    app_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(app_dir)

    # Ensure bundled resources are importable
    sys.path.insert(0, app_dir)

    log_dir = Path.home() / "Library" / "Logs" / "WordGlobalReplace"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "application.log"

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clear existing handlers to avoid duplicate logging if run multiple times
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    file_handler = logging.FileHandler(log_file, mode="a")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    if sys.stdout is not None:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        root_logger.addHandler(stream_handler)

    root_logger.info("Launcher started; log file: %s", log_file)

    try:
        from launcher import WordGlobalReplaceLauncher
        from config import DEFAULT_REPO_URL

        launcher = WordGlobalReplaceLauncher()
        distribution_repo_url = "{repo_url or ''}"
        launcher.run(repo_url=distribution_repo_url or DEFAULT_REPO_URL, auto_update=True)

    except ImportError as exc:
        print(f"Error importing launcher: {{exc}}")
        print("Please ensure all files are present in the application directory.")
        return 1
    except Exception as exc:
        print(f"Error running application: {{exc}}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

        python_launcher_path = os.path.join(resources_dir, "run.py")
        with open(python_launcher_path, 'w') as f:
            f.write(run_launcher_content)
        os.chmod(python_launcher_path, 0o755)
        logger.info("Created Python launcher script")

        if self._create_swift_launcher(macos_dir, resources_dir, repo_url):
            logger.info("Created native Swift launcher executable")
            return

        mac_launcher_content = """#!/bin/bash
APP_DIR=\"$(cd \"$(dirname \"$0\")/..\" && pwd)\"
RESOURCE_DIR=\"$APP_DIR/Resources\"
LOG_DIR=\"${HOME}/Library/Logs/WordGlobalReplace\"
LOG_FILE=\"$LOG_DIR/launcher.log\"
VENV_PY=\"$RESOURCE_DIR/venv/bin/python3\"
FALLBACK_PY=\"$RESOURCE_DIR/venv/bin/python\"

mkdir -p \"$LOG_DIR\"

if [ ! -t 1 ]; then
    exec >>\"$LOG_FILE\" 2>&1
fi

timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

echo \"[$(timestamp)] Starting WordGlobalReplace launcher\"

export PYTHONUNBUFFERED=1
export PYTHONPATH=\"$RESOURCE_DIR:${PYTHONPATH:-}\"
export DYLD_FRAMEWORK_PATH=\"$RESOURCE_DIR:${DYLD_FRAMEWORK_PATH:-}\"

cd \"$RESOURCE_DIR\"

run_with_interpreter() {
    local interpreter=\"$1\"
    shift
    if [ ! -x \"$interpreter\" ]; then
        return 127
    fi

    echo \"[$(timestamp)] Launching with interpreter: $interpreter\"
    PYTHONEXECUTABLE=\"$interpreter\" \"$interpreter\" run.py \"$@\"
}

if run_with_interpreter \"$VENV_PY\" \"$@\"; then
    exit 0
fi

if run_with_interpreter \"$FALLBACK_PY\" \"$@\"; then
    exit 0
fi

echo \"[$(timestamp)] Bundled interpreter failed; falling back to system python\" 1>&2
unset DYLD_FRAMEWORK_PATH
unset PYTHONEXECUTABLE

exec /usr/bin/env python3 run.py \"$@\"
"""

        mac_launcher_path = os.path.join(macos_dir, self.app_name)
        with open(mac_launcher_path, 'w') as f:
            f.write(mac_launcher_content)
        os.chmod(mac_launcher_path, 0o755)
        logger.info("Created macOS launcher executable")

    def _create_swift_launcher(self, macos_dir: str, resources_dir: str, repo_url: Optional[str]) -> bool:
        """Attempt to build a Swift-based launcher for a richer macOS experience."""
        if sys.platform != "darwin":
            return False

        swiftc = shutil.which("swiftc")
        if not swiftc:
            logger.debug("swiftc compiler not available; falling back to shell launcher")
            return False

        swift_source = textwrap.dedent(
            f"""\
            import Cocoa
            import Darwin

            @main
            class AppDelegate: NSObject, NSApplicationDelegate {{
                var task: Process?
                var logHandle: FileHandle?
                let defaultURL = "{DEFAULT_LOCAL_URL}"
                let repoURL = "{repo_url or ''}"
                var isShuttingDown = false

                static func main() {{
                    let app = NSApplication.shared
                    let delegate = AppDelegate()
                    app.delegate = delegate
                    app.run()
                }}

                func applicationDidFinishLaunching(_ notification: Notification) {{
                    NSApp.setActivationPolicy(.regular)
                    setupMenus()
                    setupLogging()
                    launchServer()
                    NSApp.activate(ignoringOtherApps: true)
                    DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {{
                        self.openWebApp(nil)
                    }}
                }}

                func applicationWillTerminate(_ notification: Notification) {{
                    isShuttingDown = true
                    stopServer(forceKill: true)
                    try? logHandle?.close()
                    logHandle = nil
                }}

                func setupMenus() {{
                    let mainMenu = NSMenu()
                    let appMenuItem = NSMenuItem()
                    mainMenu.addItem(appMenuItem)

                    let appMenu = NSMenu(title: "WordGlobalReplace")
                    let openItem = NSMenuItem(title: "Open Web App", action: #selector(openWebApp(_:)), keyEquivalent: "o")
                    openItem.target = self
                    appMenu.addItem(openItem)
                    appMenu.addItem(NSMenuItem.separator())
                    let quitItem = NSMenuItem(title: "Quit WordGlobalReplace", action: #selector(quitApp(_:)), keyEquivalent: "q")
                    quitItem.target = self
                    appMenu.addItem(quitItem)
                    appMenuItem.submenu = appMenu

                    NSApp.mainMenu = mainMenu
                }}

                func setupLogging() {{
                    let fm = FileManager.default
                    let logDir = fm.homeDirectoryForCurrentUser.appendingPathComponent("Library/Logs/WordGlobalReplace", isDirectory: true)
                    try? fm.createDirectory(at: logDir, withIntermediateDirectories: true)
                    let logURL = logDir.appendingPathComponent("launcher.log")
                    if !fm.fileExists(atPath: logURL.path) {{
                        fm.createFile(atPath: logURL.path, contents: nil, attributes: nil)
                    }}
                    logHandle = try? FileHandle(forWritingTo: logURL)
                    logHandle?.seekToEndOfFile()
                    log("Launcher started")
                }}

                func log(_ message: String) {{
                    let formatter = ISO8601DateFormatter()
                    let timestamp = formatter.string(from: Date())
                    let line = "[\\(timestamp)] \\(message)\\n"
                    if let data = line.data(using: .utf8) {{
                        logHandle?.write(data)
                    }}
                    fputs(line, stderr)
                }}

                func launchServer() {{
                    guard let resourcePath = Bundle.main.resourcePath else {{
                        log("Missing resources path")
                        showCriticalAlert(title: "Launcher Error", message: "Unable to locate application resources.")
                        NSApp.terminate(nil)
                        return
                    }}

                    let pythonPath = (resourcePath as NSString).appendingPathComponent("venv/bin/python3")
                    let runScriptPath = (resourcePath as NSString).appendingPathComponent("run.py")
                    if !FileManager.default.isExecutableFile(atPath: pythonPath) {{
                        log("Bundled interpreter not found at \\(pythonPath)")
                        showCriticalAlert(title: "Launcher Error", message: "Bundled Python interpreter is missing.")
                        NSApp.terminate(nil)
                        return
                    }}

                    let process = Process()
                    process.executableURL = URL(fileURLWithPath: pythonPath)
                    process.arguments = [runScriptPath]
                    process.currentDirectoryURL = URL(fileURLWithPath: resourcePath)

                    var environment = ProcessInfo.processInfo.environment
                    environment["PYTHONUNBUFFERED"] = "1"
                    environment["WORD_GLOBAL_REPLACE_PARENT_PID"] = String(ProcessInfo.processInfo.processIdentifier)
                    if !repoURL.isEmpty {{
                        environment["WORD_GLOBAL_REPLACE_REPO_URL"] = repoURL
                    }}
                    process.environment = environment

                    if let handle = logHandle {{
                        process.standardOutput = handle
                        process.standardError = handle
                    }}

                    do {{
                        try process.run()
                        log("Launched Python backend (pid: \\(process.processIdentifier))")
                        task = process
                        process.terminationHandler = {{ [weak self] proc in
                            DispatchQueue.main.async {{
                                self?.handleTermination(status: proc.terminationStatus)
                            }}
                        }}
                    }} catch {{
                        log("Failed to launch backend: \\(error.localizedDescription)")
                        showCriticalAlert(title: "Unable to start application", message: error.localizedDescription)
                        NSApp.terminate(nil)
                    }}
                }}

                func stopServer(forceKill: Bool) {{
                    guard let process = task else {{
                        task = nil
                        return
                    }}

                    if !process.isRunning {{
                        task = nil
                        return
                    }}

                    log("Stopping backend (forceKill: \\(forceKill))")
                    process.terminate()
                    if !waitForExit(process, timeout: 2.0) || forceKill {{
                        if process.isRunning {{
                            log("Backend still running; sending SIGKILL")
                            kill(process.processIdentifier, SIGKILL)
                            _ = waitForExit(process, timeout: 1.0)
                        }}
                    }}
                    task = nil
                }}

                func waitForExit(_ process: Process, timeout: TimeInterval) -> Bool {{
                    let deadline = Date().addingTimeInterval(timeout)
                    while process.isRunning && Date() < deadline {{
                        Thread.sleep(forTimeInterval: 0.1)
                    }}
                    return !process.isRunning
                }}

                func handleTermination(status: Int32) {{
                    task = nil
                    if isShuttingDown {{
                        log("Backend exited with status \\(status) during shutdown")
                        return
                    }}
                    log("Backend exited unexpectedly with status \\(status)")
                    let alert = NSAlert()
                    alert.alertStyle = .warning
                    alert.messageText = "WordGlobalReplace backend stopped"
                    alert.informativeText = "The embedded server exited with status code \\(status)."
                    alert.addButton(withTitle: "Quit")
                    alert.runModal()
                    NSApp.terminate(nil)
                }}

                func showCriticalAlert(title: String, message: String) {{
                    let alert = NSAlert()
                    alert.alertStyle = .critical
                    alert.messageText = title
                    alert.informativeText = message
                    alert.addButton(withTitle: "Quit")
                    alert.runModal()
                }}

                @objc func openWebApp(_ sender: Any?) {{
                    guard let url = URL(string: defaultURL) else {{
                        log("Invalid URL: \\(defaultURL)")
                        return
                    }}
                    NSWorkspace.shared.open(url)
                }}

                @objc func quitApp(_ sender: Any?) {{
                    isShuttingDown = true
                    stopServer(forceKill: true)
                    NSApp.terminate(nil)
                }}
            }}
            """
        )

        launcher_path = Path(macos_dir) / self.app_name
        module_cache = Path(resources_dir) / "SwiftModuleCache"
        module_cache.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env["SWIFT_MODULE_CACHE_PATH"] = str(module_cache)

        with tempfile.NamedTemporaryFile('w', suffix='.swift', delete=False) as temp_file:
            temp_file.write(swift_source)
            temp_path = Path(temp_file.name)

        try:
            subprocess.run(
                [
                    swiftc,
                    "-O",
                    "-parse-as-library",
                    "-module-cache-path",
                    str(module_cache),
                    "-o",
                    str(launcher_path),
                    str(temp_path),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
            )
            launcher_path.chmod(0o755)
            return True
        except subprocess.CalledProcessError as exc:
            logger.warning("Swift launcher compilation failed: %s", exc.stderr.strip() if exc.stderr else exc)
            if launcher_path.exists():
                launcher_path.unlink()
            return False
        finally:
            try:
                temp_path.unlink()
            except Exception:
                pass
    
    def _create_requirements_file(self, resources_dir):
        """Create a requirements file for the distribution"""
        requirements_content = '''# WordGlobalReplace - Python Dependencies
# Core web framework
Flask==2.3.3

# Word document processing
python-docx==0.8.11

# Additional utilities
pathlib2==2.3.7; python_version < "3.4"
'''
        
        req_path = os.path.join(resources_dir, "requirements.txt")
        with open(req_path, 'w') as f:
            f.write(requirements_content)
        logger.info("Created requirements file")

    def _ensure_python_context(self):
        if self.python_context is None:
            self.python_context = self._prepare_python_context()
        return self.python_context

    def _prepare_python_context(self) -> dict:
        """Select a Python interpreter (prefer universal) and gather metadata."""
        best_target = None
        for candidate in self._iter_python_candidates():
            details = self._inspect_python(candidate)
            if not details:
                continue

            rating = self._rank_python_candidate(details)
            if best_target is None or rating < best_target[0]:
                best_target = (rating, details)

        if not best_target:
            raise RuntimeError("Could not locate a usable Python interpreter for distribution bundling")

        rating, selected = best_target
        self._log_python_choice(selected, rating)
        return selected

    def _rank_python_candidate(self, details: dict):
        """Return a sortable tuple ranking interpreters (lower is better)."""
        archs = details.get('architectures', set())
        is_universal = {'arm64', 'x86_64'}.issubset(archs)

        deployment = details.get('deployment_target')
        deployment_tuple = (99, 0)
        if deployment:
            try:
                parts = [int(part) for part in str(deployment).split('.')]
                if len(parts) == 1:
                    parts.append(0)
                deployment_tuple = (parts[0], parts[1])
            except ValueError:
                pass

        # Prefer universal interpreters, then lowest deployment target, then newest version.
        version = details.get('version', [0, 0, 0])
        version_tuple = (version[0], version[1], version[2])

        universal_score = 0 if is_universal else 1
        return (universal_score, deployment_tuple, version_tuple, details.get('invocation_path', 'zzzz'))

    def _log_python_choice(self, details: dict, rating):
        archs = details.get('architectures', set())
        deployment = details.get('deployment_target') or "unknown"
        logger.info(
            "Selected Python interpreter %s (architectures: %s, deployment target: %s)",
            details.get('executable'),
            ", ".join(sorted(archs)) if archs else "unknown",
            deployment,
        )
        if not {'arm64', 'x86_64'}.issubset(archs):
            logger.warning("Selected interpreter is not universal; Intel Macs may not be supported.")
        try:
            dep_major = int(str(deployment).split('.')[0])
        except (ValueError, AttributeError):
            dep_major = None
        if dep_major and dep_major >= 14:
            logger.warning(
                "Selected interpreter requires macOS %s or newer. Older systems may fail to launch.",
                deployment,
            )

    def _iter_python_candidates(self):
        """Generate possible Python interpreter paths in order of preference."""
        candidates = []
        if self.requested_python:
            candidates.append(Path(self.requested_python))

        candidates.append(Path(sys.executable))
        candidates.extend([
            Path("/Library/Developer/CommandLineTools/usr/bin/python3"),
            Path("/usr/bin/python3"),
            Path("/Library/Frameworks/Python.framework/Versions/Current/bin/python3"),
            Path("/Library/Frameworks/Python.framework/Versions/3.11/bin/python3"),
        ])

        seen = set()
        for candidate in candidates:
            try:
                resolved = candidate.resolve(strict=False)
            except (OSError, RuntimeError):
                continue
            key = str(resolved)
            if key in seen:
                continue
            seen.add(key)
            if candidate.exists():
                yield candidate

    def _inspect_python(self, path: Path) -> Optional[dict]:
        """Collect interpreter metadata needed for bundling."""
        try:
            if not path.exists() or not os.access(path, os.X_OK):
                return None

            architectures = self._mach_architectures(path)

            script = (
                "import sys, sysconfig, json, os\n"
                "info = {\n"
                "  'executable': sys.executable,\n"
                "  'real_executable': os.path.realpath(sys.executable),\n"
                "  'version': [sys.version_info.major, sys.version_info.minor, sys.version_info.micro],\n"
                "  'framework_name': sysconfig.get_config_var('PYTHONFRAMEWORK'),\n"
                "  'framework_prefix': sysconfig.get_config_var('PYTHONFRAMEWORKPREFIX'),\n"
                "  'base_prefix': getattr(sys, 'base_prefix', ''),\n"
                "  'prefix': sys.prefix,\n"
                "  'deployment_target': sysconfig.get_config_var('MACOSX_DEPLOYMENT_TARGET'),\n"
                "}\n"
                "print(json.dumps(info))\n"
            )

            output = subprocess.check_output([str(path), "-c", script], text=True)
            metadata = json.loads(output)

            version_major, version_minor, _ = metadata['version']
            metadata['version_str'] = f"{version_major}.{version_minor}"
            metadata['major'] = version_major
            metadata['minor'] = version_minor
            metadata['architectures'] = architectures
            metadata['invocation_path'] = str(path)
            return metadata
        except subprocess.CalledProcessError as exc:
            logger.debug("Failed to query Python interpreter %s: %s", path, exc)
        except Exception as exc:
            logger.debug("Error inspecting Python interpreter %s: %s", path, exc)
        return None

    def _mach_architectures(self, path: Path) -> set:
        """Return the set of CPU architectures supported by a Mach-O binary."""
        try:
            output = subprocess.check_output(["file", str(path)], text=True).lower()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return set()

        archs = set()
        if "arm64" in output:
            archs.add("arm64")
        if "x86_64" in output or "x86-64" in output:
            archs.add("x86_64")
        return archs

    def _resolve_framework_info(self, resources_dir: str, python_info: dict) -> Optional[dict]:
        configured_name = python_info.get('framework_name')
        candidate_names = [name for name in [configured_name, "Python", "Python3"] if name]

        framework_dir = None
        framework_name = None
        for name in candidate_names:
            candidate = Path(resources_dir) / f"{name}.framework"
            if candidate.exists():
                framework_dir = candidate
                framework_name = name
                break

        if framework_dir is None or framework_name is None:
            logger.warning("Bundled Python framework not found; skipping framework-dependent steps")
            return None

        framework_version = python_info.get('version_str')
        versions_dir = framework_dir / "Versions"
        if versions_dir.exists():
            for entry in versions_dir.iterdir():
                name = entry.name
                if name.lower() == "current":
                    continue
                framework_version = name
                break

        if not framework_version:
            framework_version = python_info.get('version_str', f"{sys.version_info.major}.{sys.version_info.minor}")

        version_dir = framework_dir / "Versions" / framework_version
        candidate_binaries = ["Python", "Python3"]
        framework_binary = None
        for candidate in candidate_binaries:
            if (version_dir / candidate).exists():
                framework_binary = candidate
                break

        if framework_binary is None:
            logger.warning("Framework executable missing in %s; skipping framework-dependent steps", version_dir)
            return None

        return {
            "name": framework_name,
            "dir": framework_dir,
            "version": framework_version,
            "version_dir": version_dir,
            "binary_name": framework_binary,
            "binary_path": version_dir / framework_binary,
        }

    def _create_virtual_environment(self, resources_dir):
        """Create a self-contained virtual environment with dependencies"""
        venv_path = Path(resources_dir) / 'venv'
        if venv_path.exists():
            shutil.rmtree(venv_path)

        logger.info("Creating bundled virtual environment")
        python_info = self._ensure_python_context()
        python_executable = python_info['executable']
        architectures = python_info.get('architectures', [])
        if architectures:
            logger.info(
                "Using Python interpreter %s for bundling (architectures: %s)",
                python_executable,
                ", ".join(sorted(architectures)),
            )
        else:
            logger.info("Using Python interpreter %s for bundling", python_executable)
        created_with_copies = True
        try:
            try:
                subprocess.run(
                    [python_executable, '-m', 'venv', '--copies', str(venv_path)],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            except subprocess.CalledProcessError as exc:
                err_output = exc.stderr
                logger.warning(
                    "Creating venv with --copies failed; attempting standard venv. Details: %s",
                    err_output.strip() if err_output else exc
                )
                subprocess.run(
                    [python_executable, '-m', 'venv', str(venv_path)],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                created_with_copies = False
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"Failed to create virtual environment: {exc}") from exc

        if os.name == 'nt':
            scripts_dir = venv_path / 'Scripts'
            python_bin = scripts_dir / 'python.exe'
            pip_bin = scripts_dir / 'pip.exe'
        else:
            scripts_dir = venv_path / 'bin'
            python_bin = scripts_dir / 'python'
            pip_bin = scripts_dir / 'pip'

        try:
            subprocess.run([str(python_bin), '-m', 'pip', 'install', '--upgrade', 'pip'], check=True)
            subprocess.run(
                [str(pip_bin), 'install', '--no-cache-dir', '-r', str(Path(resources_dir) / 'requirements.txt')],
                check=True
            )
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"Failed to install dependencies into bundled environment: {exc}")

        if not created_with_copies:
            logger.info("Ensuring interpreter binaries are copied after symlink-based venv creation")
        self._solidify_python_binaries(venv_path)

        self._bundle_python_runtime(venv_path, resources_dir, python_info)
        self._relink_python_binaries(venv_path, resources_dir, python_info)
        self._normalize_deployment_targets(venv_path, resources_dir, python_info)
        logger.info("Bundled virtual environment ready")

    def _bundle_python_runtime(self, venv_path: Path, resources_dir: str, python_info: dict):
        """Copy the Python framework into the bundle so the app runs without a system Python"""
        if sys.platform != "darwin":
            logger.debug("Non-macOS platform detected; skipping Python framework bundling")
            return

        framework_name = python_info.get('framework_name') or "Python"

        candidate_paths = []

        cfg_prefix = python_info.get('framework_prefix')
        if cfg_prefix:
            candidate_paths.append(Path(cfg_prefix) / f"{framework_name}.framework")

        base_prefix = python_info.get('base_prefix') or python_info.get('prefix')
        if base_prefix:
            bp = Path(base_prefix)
            candidate_paths.append(bp.parent.parent)

        real_executable = python_info.get('real_executable')
        if real_executable:
            resolved = Path(real_executable)
            for parent in resolved.parents:
                if parent.name.endswith(".framework"):
                    candidate_paths.append(parent)
                    framework_name = parent.name.replace(".framework", "")
                    break

        source_framework = None
        seen = set()
        for candidate in candidate_paths:
            key = str(candidate)
            if key in seen:
                continue
            seen.add(key)
            if candidate.exists():
                source_framework = candidate
                if candidate.name.endswith(".framework"):
                    framework_name = candidate.name.replace(".framework", "")
                break
        if source_framework is None:
            logger.warning(
                "Unable to locate Python framework (checked: %s); bundled interpreter may require system Python",
                ", ".join(str(p) for p in candidate_paths) or "none"
            )
            return

        destination = Path(resources_dir) / f"{framework_name}.framework"
        if destination.exists():
            shutil.rmtree(destination)

        logger.info(f"Copying Python framework to bundle: {source_framework} -> {destination}")
        shutil.copytree(source_framework, destination, symlinks=False)

        # Ensure site-packages directory exists so relative symlinks remain valid even if source omitted it
        version_dir = destination / "Versions" / python_info.get('version_str', f"{sys.version_info.major}.{sys.version_info.minor}")
        site_packages = version_dir / "lib" / f"python{python_info.get('version_str', f'{sys.version_info.major}.{sys.version_info.minor}')}" / "site-packages"
        site_packages.mkdir(parents=True, exist_ok=True)

    def _solidify_python_binaries(self, venv_path: Path):
        """Replace symlinked python binaries with physical copies for relocation safety"""
        if os.name == 'nt':
            return  # Windows virtualenv already copies executables

        bin_dir = venv_path / 'bin'
        if not bin_dir.exists():
            return

        binaries = ['python', 'python3']
        for name in binaries:
            bin_path = bin_dir / name
            if not bin_path.exists() or not bin_path.is_symlink():
                continue

            target = bin_path.resolve()
            try:
                bin_path.unlink()
                shutil.copy2(target, bin_path)
                bin_path.chmod(0o755)
                logger.info(f"Replaced symlinked interpreter with copy: {bin_path}")
            except Exception as exc:
                logger.warning(f"Failed to solidify interpreter {bin_path}: {exc}")

    def _relink_python_binaries(self, venv_path: Path, resources_dir: str, python_info: dict):
        """Retarget Python interpreter binaries to the bundled framework so no system Python is required."""
        if sys.platform != "darwin":
            return
        framework_info = self._resolve_framework_info(resources_dir, python_info)
        if not framework_info:
            return
        framework_name = framework_info['name']
        framework_version = framework_info['version']
        framework_binary = framework_info['binary_name']
        relative_target = f"@loader_path/../../{framework_name}.framework/Versions/{framework_version}/{framework_binary}"

        bin_dir = venv_path / "bin"
        if not bin_dir.exists():
            logger.warning("Virtual environment bin directory missing; skipping interpreter relink step")
            return

        binaries = [
            "python",
            "python3",
            f"python{framework_version}",
            f"python{python_info.get('major', sys.version_info.major)}",
            f"python{python_info.get('major', sys.version_info.major)}.{python_info.get('minor', sys.version_info.minor)}",
        ]
        for name in binaries:
            bin_path = bin_dir / name
            if not bin_path.exists():
                continue

            try:
                output = subprocess.check_output(["otool", "-L", str(bin_path)], text=True)
            except (subprocess.CalledProcessError, FileNotFoundError) as exc:
                logger.warning(f"Unable to inspect interpreter {bin_path}: {exc}")
                continue

            framework_refs = []
            for line in output.splitlines()[1:]:
                candidate = line.strip().split(" ", 1)[0]
                if framework_name in candidate:
                    framework_refs.append(candidate)

            if not framework_refs:
                continue

            for original_ref in framework_refs:
                if original_ref == relative_target:
                    continue
                try:
                    subprocess.run(
                        ["install_name_tool", "-change", original_ref, relative_target, str(bin_path)],
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                    logger.info(f"Relinked {bin_path.name} to use bundled framework ({original_ref} -> {relative_target})")
                except subprocess.CalledProcessError as exc:
                    logger.warning(f"Failed to relink interpreter {bin_path}: {exc.stderr.strip() if exc.stderr else exc}")

    def _normalize_deployment_targets(self, venv_path: Path, resources_dir: str, python_info: dict):
        """Ensure bundled binaries declare a deployment target compatible with older macOS versions."""
        if sys.platform != "darwin":
            return

        desired = (10, 9)
        framework_info = self._resolve_framework_info(resources_dir, python_info)
        binaries = [
            venv_path / "bin" / "python3",
            venv_path / "bin" / "python",
        ]
        if framework_info:
            binaries.append(framework_info['binary_path'])

        for binary in binaries:
            if binary.exists():
                self._ensure_binary_deployment_target(binary, desired)
            else:
                logger.debug("Skipping deployment target normalization; %s not found", binary)

    def _ensure_binary_deployment_target(self, binary_path: Path, desired: tuple[int, int]):
        """Lower the declared macOS deployment target if needed."""
        info = self._read_binary_build_info(binary_path)
        if not info:
            return

        current = info.get('minos')
        sdk = info.get('sdk') or f"{desired[0]}.{desired[1]}"

        if current and self._compare_versions(self._parse_version(current), desired) <= 0:
            return

        desired_str = f"{desired[0]}.{desired[1]}"
        logger.info(
            "Adjusting deployment target for %s: %s -> %s",
            binary_path,
            current or "unknown",
            desired_str,
        )

        try:
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp_path = Path(tmp.name)
            subprocess.run(
                [
                    "vtool",
                    "-set-build-version",
                    "macos",
                    desired_str,
                    sdk,
                    "-output",
                    str(tmp_path),
                    str(binary_path),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            shutil.move(tmp_path, binary_path)
            binary_path.chmod(0o755)
        except subprocess.CalledProcessError as exc:
            logger.warning(
                "Failed to adjust deployment target for %s: %s",
                binary_path,
                exc.stderr.strip() if exc.stderr else exc,
            )
        finally:
            if 'tmp_path' in locals() and tmp_path.exists():
                tmp_path.unlink(missing_ok=True)

    def _read_binary_build_info(self, binary_path: Path) -> Optional[dict]:
        try:
            output = subprocess.check_output(
                ["vtool", "-show-build", str(binary_path)],
                text=True,
                stderr=subprocess.PIPE,
            )
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            logger.warning("Unable to read build info for %s: %s", binary_path, exc)
            return None

        minos = None
        sdk = None
        for line in output.splitlines():
            stripped = line.strip()
            if stripped.startswith("minos "):
                minos = stripped.split()[1]
            elif stripped.startswith("sdk "):
                sdk = stripped.split()[1]
                if minos:
                    break
        return {"minos": minos, "sdk": sdk}

    def _parse_version(self, version_str: str) -> tuple[int, int]:
        parts = version_str.split(".")
        major = int(parts[0]) if parts and parts[0].isdigit() else 0
        minor = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        return (major, minor)

    def _compare_versions(self, a: tuple[int, int], b: tuple[int, int]) -> int:
        if a == b:
            return 0
        return -1 if a < b else 1
    
    def _create_distribution_readme(self, resources_dir, repo_url):
        """Create README for the distribution"""
        readme_content = f'''# WordGlobalReplace

A lightweight application for finding and replacing text across multiple Word documents.

## Features

- Web-based interface for easy use
- Support for multiple Word document formats (.doc, .docx)
- Advanced search with context preview
- Batch replacement capabilities
- Auto-updating from GitHub (if repository URL is configured)
- Backup creation before replacements

## Installation

1. Extract the archive and copy `WordGlobalReplace.app` to your Applications folder (or preferred location)
2. Double-click the app to launch it
3. Optionally run `./install.sh` for quick usage instructions

## Usage

1. Launch the application by opening `WordGlobalReplace.app`
2. Open your browser to: {DEFAULT_LOCAL_URL}
3. Select a directory containing Word documents
4. Enter search and replacement text
5. Review matches and apply replacements

## Auto-Updates

{f"Auto-updates are configured from: {repo_url}" if repo_url else "Auto-updates are not configured. To enable, run with --repo-url parameter."}

The application will automatically check for updates when launched and update itself if new versions are available.

## Requirements

- macOS (tested on macOS 10.14+)
- Internet connection (for auto-updates)

## Troubleshooting

If you encounter issues:

1. Verify the app bundle has write permissions (needed for backups/updates)
2. Check the console output for error messages (`open -a Terminal WordGlobalReplace.app`)
3. Ensure you have an active internet connection for auto-updates

## Support

For issues and support, please check the GitHub repository or contact the developer.
'''
        
        readme_path = os.path.join(resources_dir, "README.md")
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        logger.info("Created distribution README")
    
    def _create_installer_script(self, resources_dir):
        """Create an installer script for easy setup"""
        installer_content = f'''#!/bin/bash
# WordGlobalReplace Quick Launch Script

echo "WordGlobalReplace"
echo "=================="

cd "$(dirname "$0")"

echo "All dependencies are bundled with the application."
echo ""
echo "To launch the app now, run:"
echo "  open ../.."
echo ""
echo "When running, open your browser to: {DEFAULT_LOCAL_URL}"
echo ""
echo "Tip: You can place WordGlobalReplace.app in /Applications for easy access."
'''
        
        installer_path = os.path.join(resources_dir, "install.sh")
        with open(installer_path, 'w') as f:
            f.write(installer_content)
        
        # Make it executable
        os.chmod(installer_path, 0o755)
        logger.info("Created installer script")
    
    def _create_cli_launcher_script(self, resources_dir: str):
        """Create a CLI helper script that runs the bundled Python interpreter directly."""
        script_content = """#!/bin/bash
# WordGlobalReplace CLI launcher

set -e

RESOURCE_DIR=\"$(cd \"$(dirname \"$0\")\" && pwd)\"
PYTHON_BIN=\"$RESOURCE_DIR/venv/bin/python3\"
RUN_SCRIPT=\"$RESOURCE_DIR/run.py\"

if [ ! -x \"$PYTHON_BIN\" ]; then
    echo \"Bundled Python interpreter not found; falling back to system python\" >&2
    exec /usr/bin/env python3 \"$RUN_SCRIPT\" \"$@\"
fi

exec \"$PYTHON_BIN\" \"$RUN_SCRIPT\" \"$@\"
"""

        script_path = Path(resources_dir) / "run_cli.sh"
        script_path.write_text(script_content, encoding="utf-8")
        script_path.chmod(0o755)
        logger.info("Created CLI launcher script")
    
    def _create_zip_package(self, app_dir):
        """Create a zip package for distribution"""
        zip_path = os.path.join(self.output_dir, f"{self.app_name}.zip")
        
        app_basename = os.path.basename(app_dir.rstrip(os.sep))

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(app_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_path = os.path.join(app_basename, os.path.relpath(file_path, app_dir))
                    zipf.write(file_path, arc_path)
        
        logger.info(f"Created zip package: {zip_path}")

    def _codesign_app(self, app_dir: str):
        """Apply ad-hoc signatures so bundled binaries run on other Macs."""
        if sys.platform != "darwin":
            return

        try:
            resources_dir = Path(app_dir) / "Contents" / "Resources"
            python_info = self._ensure_python_context()
            framework_info = self._resolve_framework_info(str(resources_dir), python_info)

            self._remove_existing_signatures(Path(app_dir))

            if framework_info:
                self._codesign_path(framework_info['binary_path'])
                self._codesign_path(framework_info['version_dir'], deep=True)

            venv_bin = Path(resources_dir) / "venv" / "bin"
            binaries = [
                "python",
                "python3",
                f"python{python_info.get('major', sys.version_info.major)}",
                f"python{python_info.get('major', sys.version_info.major)}.{python_info.get('minor', sys.version_info.minor)}",
            ]
            for name in binaries:
                candidate = venv_bin / name
                if candidate.exists():
                    self._codesign_path(candidate)

            self._codesign_path(Path(app_dir), deep=True)
            logger.info("Applied ad-hoc code signatures to bundled binaries")
        except FileNotFoundError:
            logger.warning("codesign tool not available; app will run unsigned")
        except subprocess.CalledProcessError as exc:
            logger.warning(
                "Failed to sign app bundle; unsigned executables may be blocked. Details: %s",
                exc.stderr.strip() if exc.stderr else exc,
            )

    def _remove_existing_signatures(self, root: Path):
        for signature_dir in root.glob("**/_CodeSignature"):
            try:
                shutil.rmtree(signature_dir)
            except Exception as exc:
                logger.debug("Failed to remove old signature directory %s: %s", signature_dir, exc)

    def _codesign_path(self, target: Path, deep: bool = False):
        args = ["codesign", "--force"]
        if deep:
            args.append("--deep")
        args.extend(["--sign", "-", str(target)])
        try:
            subprocess.run(
                args,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            logger.debug("Code-signed %s", target)
        except subprocess.CalledProcessError as exc:
            logger.warning(
                "Failed to sign %s: %s",
                target,
                exc.stderr.strip() if exc.stderr else exc,
            )

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Create WordGlobalReplace distribution')
    parser.add_argument('--repo-url', help='GitHub repository URL for auto-updates')
    parser.add_argument('--output-dir', default='dist', help='Output directory for distribution')
    parser.add_argument('--python', dest='python_path', help='Python interpreter to use for building the bundle')
    
    args = parser.parse_args()
    
    creator = DistributionCreator(output_dir=args.output_dir, python_executable=args.python_path)
    success = creator.create_distribution(repo_url=args.repo_url)
    
    if success:
        print(f"\\nDistribution created successfully!")
        print(f"Output directory: {args.output_dir}")
        print(f"\\nTo distribute:")
        print(f"1. Share the {args.output_dir}/WordGlobalReplace.zip file")
        print("2. Recipients should extract and copy WordGlobalReplace.app to their Applications folder (or another preferred location)")
        print("3. Optional: run ./WordGlobalReplace.app/Contents/Resources/install.sh for quick launch instructions")
        print("4. Launch the app by double-clicking WordGlobalReplace.app or running: open WordGlobalReplace.app")
    else:
        print("Failed to create distribution")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
