const vscode = require('vscode');
const { exec, spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

// Extension root directory (where Python files are)
const EXTENSION_ROOT = path.dirname(__dirname);
let serverProcess = null;

/**
 * @param {vscode.ExtensionContext} context
 */
async function activate(context) {
    console.log('Browser Bridge is activating...');

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('browserbridge.setup', runSetupWizard),
        vscode.commands.registerCommand('browserbridge.startServer', startServer),
        vscode.commands.registerCommand('browserbridge.stopServer', stopServer),
        vscode.commands.registerCommand('browserbridge.status', checkStatus)
    );

    // Check if first run
    const config = vscode.workspace.getConfiguration('browserbridge');
    const extensionId = config.get('chromeExtensionId');

    if (!extensionId) {
        // First run - show setup wizard
        const action = await vscode.window.showInformationMessage(
            'Browser Bridge needs to be configured. Would you like to run setup now?',
            'Run Setup',
            'Later'
        );
        if (action === 'Run Setup') {
            await runSetupWizard();
        }
    } else {
        vscode.window.showInformationMessage('Browser Bridge is ready!');
    }
}

/**
 * Main setup wizard
 */
async function runSetupWizard() {
    try {
        // Step 1: Check Python
        vscode.window.showInformationMessage('🔍 Checking Python installation...');
        const pythonPath = await checkPython();
        if (!pythonPath) {
            vscode.window.showErrorMessage('Python 3 is required but not found. Please install Python first.');
            return;
        }

        // Step 2: Install dependencies
        vscode.window.showInformationMessage('📦 Installing Python dependencies...');
        const depsInstalled = await installDependencies(pythonPath);
        if (!depsInstalled) {
            vscode.window.showErrorMessage('Failed to install Python dependencies.');
            return;
        }

        // Step 3: Ask for Chrome Extension ID
        const extensionId = await vscode.window.showInputBox({
            prompt: 'Enter Chrome Extension ID',
            placeHolder: 'e.g., abcdefghijklmnopqrstuvwxyz',
            ignoreFocusOut: true,
            validateInput: (value) => {
                if (!value || value.length < 10) {
                    return 'Please enter a valid Extension ID (found in chrome://extensions)';
                }
                return null;
            }
        });

        if (!extensionId) {
            vscode.window.showWarningMessage('Setup cancelled.');
            return;
        }

        // Save Extension ID to settings
        const config = vscode.workspace.getConfiguration('browserbridge');
        await config.update('chromeExtensionId', extensionId, vscode.ConfigurationTarget.Global);

        // Step 4: Register Native Messaging Host
        vscode.window.showInformationMessage('🔧 Registering native messaging host...');
        const hostRegistered = await registerNativeHost(extensionId);
        if (!hostRegistered) {
            vscode.window.showErrorMessage('Failed to register native messaging host.');
            return;
        }

        // Step 5: Configure MCP
        vscode.window.showInformationMessage('⚙️ Configuring MCP server...');
        await configureMCP(pythonPath);

        // Done!
        vscode.window.showInformationMessage(
            '✅ Browser Bridge setup complete! Please restart Chrome.',
            'OK'
        );

    } catch (error) {
        vscode.window.showErrorMessage(`Setup failed: ${error.message}`);
    }
}

/**
 * Check if Python is installed
 */
function checkPython() {
    return new Promise((resolve) => {
        const config = vscode.workspace.getConfiguration('browserbridge');
        const pythonPath = config.get('pythonPath') || 'python3';

        exec(`${pythonPath} --version`, (error, stdout) => {
            if (error) {
                // Try 'python' as fallback
                exec('python --version', (err2, stdout2) => {
                    if (err2 || !stdout2.includes('Python 3')) {
                        resolve(null);
                    } else {
                        resolve('python');
                    }
                });
            } else if (stdout.includes('Python 3')) {
                resolve(pythonPath);
            } else {
                resolve(null);
            }
        });
    });
}

/**
 * Install Python dependencies
 */
function installDependencies(pythonPath) {
    return new Promise((resolve) => {
        const requirementsPath = path.join(EXTENSION_ROOT, 'requirements.txt');

        exec(`${pythonPath} -m pip install -r "${requirementsPath}"`, (error, stdout, stderr) => {
            if (error) {
                console.error('Pip install error:', stderr);
                resolve(false);
            } else {
                resolve(true);
            }
        });
    });
}

/**
 * Register native messaging host
 */
function registerNativeHost(extensionId) {
    return new Promise((resolve) => {
        const nativeHostPath = path.join(EXTENSION_ROOT, 'native_host.py');
        const hostName = 'com.browserbridge.host';

        // Determine Chrome native messaging directory
        let chromeDir;
        if (process.platform === 'darwin') {
            chromeDir = path.join(os.homedir(), 'Library/Application Support/Google/Chrome/NativeMessagingHosts');
        } else if (process.platform === 'linux') {
            chromeDir = path.join(os.homedir(), '.config/google-chrome/NativeMessagingHosts');
        } else {
            // Windows
            chromeDir = path.join(os.homedir(), 'AppData/Local/Google/Chrome/User Data/NativeMessagingHosts');
        }

        // Create directory if needed
        if (!fs.existsSync(chromeDir)) {
            fs.mkdirSync(chromeDir, { recursive: true });
        }

        // Create manifest
        const manifest = {
            name: hostName,
            description: 'Browser Bridge - Native Messaging Host',
            path: nativeHostPath,
            type: 'stdio',
            allowed_origins: [`chrome-extension://${extensionId}/`]
        };

        const manifestPath = path.join(chromeDir, `${hostName}.json`);
        fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));

        // Make native_host.py executable (Unix)
        if (process.platform !== 'win32') {
            fs.chmodSync(nativeHostPath, '755');
        }

        resolve(true);
    });
}

/**
 * Configure MCP server
 */
function configureMCP(pythonPath) {
    return new Promise((resolve) => {
        const mcpServerPath = path.join(EXTENSION_ROOT, 'mcp_server.py');
        const geminiConfigDir = path.join(os.homedir(), '.gemini', 'antigravity');
        const mcpConfigPath = path.join(geminiConfigDir, 'mcp_config.json');

        // Create directory if needed
        if (!fs.existsSync(geminiConfigDir)) {
            fs.mkdirSync(geminiConfigDir, { recursive: true });
        }

        // Create MCP config
        const mcpConfig = {
            mcpServers: {
                'browser-bridge': {
                    command: pythonPath,
                    args: [mcpServerPath],
                    env: {}
                }
            }
        };

        fs.writeFileSync(mcpConfigPath, JSON.stringify(mcpConfig, null, 2));
        resolve(true);
    });
}

/**
 * Start the bridge server
 */
async function startServer() {
    if (serverProcess) {
        vscode.window.showWarningMessage('Server is already running.');
        return;
    }

    const config = vscode.workspace.getConfiguration('browserbridge');
    const pythonPath = config.get('pythonPath') || 'python3';
    const serverScript = path.join(EXTENSION_ROOT, 'bridge_server.py');

    serverProcess = spawn(pythonPath, [serverScript], {
        cwd: EXTENSION_ROOT,
        detached: true
    });

    serverProcess.on('error', (err) => {
        vscode.window.showErrorMessage(`Server error: ${err.message}`);
        serverProcess = null;
    });

    serverProcess.on('exit', (code) => {
        if (code !== 0) {
            vscode.window.showWarningMessage(`Server exited with code ${code}`);
        }
        serverProcess = null;
    });

    vscode.window.showInformationMessage('🚀 Bridge Server started on ws://127.0.0.1:8000/ws');
}

/**
 * Stop the bridge server
 */
async function stopServer() {
    if (serverProcess) {
        serverProcess.kill();
        serverProcess = null;
        vscode.window.showInformationMessage('Server stopped.');
    } else {
        // Try to kill any server on port 8000
        exec("lsof -ti :8000 | xargs kill 2>/dev/null", () => {
            vscode.window.showInformationMessage('Server stopped.');
        });
    }
}

/**
 * Check connection status
 */
async function checkStatus() {
    try {
        const http = require('http');

        const req = http.get('http://127.0.0.1:8000/health', (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    const status = JSON.parse(data);
                    if (status.browser_connected) {
                        vscode.window.showInformationMessage('✅ Server running, Browser connected!');
                    } else {
                        vscode.window.showInformationMessage('🟡 Server running, Browser not connected.');
                    }
                } catch {
                    vscode.window.showInformationMessage('🟡 Server running.');
                }
            });
        });

        req.on('error', () => {
            vscode.window.showWarningMessage('🔴 Server is not running. Use "Browser Bridge: Start Server"');
        });

        req.end();
    } catch {
        vscode.window.showWarningMessage('🔴 Server is not running.');
    }
}

function deactivate() {
    if (serverProcess) {
        serverProcess.kill();
    }
}

module.exports = {
    activate,
    deactivate
};
