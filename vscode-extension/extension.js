const vscode = require('vscode');
const { exec, spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');
const http = require('http');

const BRIDGE_URL = 'http://127.0.0.1:8000';

let serverProcess = null;
let statusBarItem = null;
let statusInterval = null;

/**
 * @param {vscode.ExtensionContext} context
 */
async function activate(context) {
    console.log('Browser Bridge is activating...');

    // Create status bar item
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.command = 'browserbridge.showMenu';
    statusBarItem.tooltip = 'Browser Bridge - Click for options';
    context.subscriptions.push(statusBarItem);

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('browserbridge.showMenu', showBrowserMenu),
        vscode.commands.registerCommand('browserbridge.startServer', () => startServer(false)),
        vscode.commands.registerCommand('browserbridge.stopServer', stopServer),
        vscode.commands.registerCommand('browserbridge.restartServer', restartServer),
        vscode.commands.registerCommand('browserbridge.selectBrowser', selectBrowser)
    );

    // Start status polling
    updateStatusBar();
    statusInterval = setInterval(updateStatusBar, 3000);
    context.subscriptions.push({ dispose: () => clearInterval(statusInterval) });

    // Auto-start if enabled
    const config = vscode.workspace.getConfiguration('browserbridge');
    if (config.get('autoStart')) {
        await startServer(true);
    }

    statusBarItem.show();
}

/**
 * Get the path to bridge_server.py
 */
function getServerPath() {
    const config = vscode.workspace.getConfiguration('browserbridge');
    const customPath = config.get('serverPath');

    if (customPath && fs.existsSync(customPath)) {
        return customPath;
    }

    // Try common locations
    const possiblePaths = [
        // Workspace folder
        vscode.workspace.workspaceFolders?.[0]?.uri.fsPath + '/bridge_server.py',
        // Home directory
        path.join(os.homedir(), 'Development/FreeLance/IDEextension/bridge_server.py'),
        // Extension directory (for development)
        path.join(__dirname, '..', 'bridge_server.py'),
        path.join(__dirname, 'bridge_server.py'),
    ];

    for (const p of possiblePaths) {
        if (p && fs.existsSync(p)) {
            return p;
        }
    }

    return null;
}

/**
 * Update status bar
 */
async function updateStatusBar() {
    try {
        const data = await fetchJSON(`${BRIDGE_URL}/clients`);

        if (data && data.count > 0) {
            const active = data.clients.find(c => c.id === data.active);
            const icon = getBrowserIcon(active?.browser || 'Unknown');
            statusBarItem.text = `${icon} ${active?.browser || 'Browser'} (${data.count})`;
            statusBarItem.backgroundColor = undefined;
        } else if (data) {
            statusBarItem.text = '$(globe) No Browser';
            statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
        } else {
            statusBarItem.text = '$(circle-slash) Offline';
            statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
        }
    } catch {
        statusBarItem.text = '$(circle-slash) Offline';
        statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
    }
}

function getBrowserIcon(browser) {
    const icons = {
        'Chrome': '$(browser)',
        'Brave': '$(shield)',
        'Edge': '$(window)',
        'Firefox': '$(flame)',
        'Safari': '$(compass)',
        'Opera': '$(debug-console)',
        'Vivaldi': '$(symbol-color)',
        'Arc': '$(sparkle)'
    };
    return icons[browser] || '$(globe)';
}

/**
 * Show browser menu
 */
async function showBrowserMenu() {
    const data = await fetchJSON(`${BRIDGE_URL}/clients`);
    const items = [];

    if (!data) {
        // Server not running
        items.push({
            label: '$(play) Start Server',
            action: 'start'
        });
    } else {
        // Server running
        items.push({
            label: '$(refresh) Restart Server',
            action: 'restart'
        });
        items.push({
            label: '$(stop) Stop Server',
            action: 'stop'
        });

        // Browser list
        if (data.clients && data.clients.length > 0) {
            items.push({ label: '', kind: vscode.QuickPickItemKind.Separator });
            items.push({ label: 'Switch Browser', kind: vscode.QuickPickItemKind.Separator });

            for (const client of data.clients) {
                const isActive = client.id === data.active;
                const icon = getBrowserIcon(client.browser);
                items.push({
                    label: `${isActive ? '★ ' : ''}${icon} ${client.browser}`,
                    description: client.url.substring(0, 40) + (client.url.length > 40 ? '...' : ''),
                    detail: `ID: ${client.id}`,
                    action: 'select',
                    clientId: client.id
                });
            }
        } else {
            items.push({ label: '', kind: vscode.QuickPickItemKind.Separator });
            items.push({
                label: '$(info) No browsers connected',
                description: 'Open extension in browser and click Connect'
            });
        }
    }

    // Settings
    items.push({ label: '', kind: vscode.QuickPickItemKind.Separator });
    items.push({
        label: '$(gear) Configure Server Path',
        action: 'configure'
    });

    const selected = await vscode.window.showQuickPick(items, {
        placeHolder: 'Browser Bridge',
        title: 'Browser Bridge'
    });

    if (!selected || !selected.action) return;

    switch (selected.action) {
        case 'start':
            await startServer(false);
            break;
        case 'stop':
            await stopServer();
            break;
        case 'restart':
            await restartServer();
            break;
        case 'select':
            await selectBrowserById(selected.clientId);
            break;
        case 'configure':
            await configureServerPath();
            break;
    }
}

/**
 * Configure server path
 */
async function configureServerPath() {
    const config = vscode.workspace.getConfiguration('browserbridge');
    const current = config.get('serverPath') || '';

    const result = await vscode.window.showInputBox({
        prompt: 'Enter path to bridge_server.py',
        value: current || getServerPath() || '',
        placeHolder: '/path/to/bridge_server.py'
    });

    if (result !== undefined) {
        await config.update('serverPath', result, vscode.ConfigurationTarget.Global);
        vscode.window.showInformationMessage('Server path updated!');
    }
}

/**
 * Select browser
 */
async function selectBrowser() {
    const data = await fetchJSON(`${BRIDGE_URL}/clients`);

    if (!data || data.count === 0) {
        vscode.window.showWarningMessage('No browsers connected.');
        return;
    }

    const items = data.clients.map(client => ({
        label: `${getBrowserIcon(client.browser)} ${client.browser}`,
        description: client.url.substring(0, 50),
        detail: client.id === data.active ? '★ Active' : `ID: ${client.id}`,
        clientId: client.id
    }));

    const selected = await vscode.window.showQuickPick(items, {
        placeHolder: 'Select a browser'
    });

    if (selected) {
        await selectBrowserById(selected.clientId);
    }
}

async function selectBrowserById(clientId) {
    try {
        const result = await fetchJSON(`${BRIDGE_URL}/select/${clientId}`, 'POST');
        if (result?.success) {
            vscode.window.showInformationMessage(`✅ Switched to: ${clientId}`);
            await updateStatusBar();
        } else {
            vscode.window.showErrorMessage(`Failed: ${result?.error || 'Unknown error'}`);
        }
    } catch (e) {
        vscode.window.showErrorMessage(`Error: ${e.message}`);
    }
}

/**
 * Fetch JSON
 */
function fetchJSON(url, method = 'GET') {
    return new Promise((resolve) => {
        const req = http.request(url, { method, timeout: 2000 }, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    resolve(JSON.parse(data));
                } catch {
                    resolve(null);
                }
            });
        });
        req.on('error', () => resolve(null));
        req.on('timeout', () => { req.destroy(); resolve(null); });
        req.end();
    });
}

/**
 * Start server
 */
async function startServer(silent = false) {
    // Check if already running
    const health = await fetchJSON(`${BRIDGE_URL}/health`);
    if (health) {
        if (!silent) vscode.window.showInformationMessage('Server is already running.');
        return;
    }

    const serverPath = getServerPath();

    if (!serverPath) {
        const action = await vscode.window.showErrorMessage(
            'bridge_server.py not found. Configure the path?',
            'Configure'
        );
        if (action === 'Configure') {
            await configureServerPath();
        }
        return;
    }

    const config = vscode.workspace.getConfiguration('browserbridge');
    const pythonPath = config.get('pythonPath') || 'python3';

    serverProcess = spawn(pythonPath, [serverPath], {
        cwd: path.dirname(serverPath),
        detached: true,
        stdio: 'ignore'
    });

    serverProcess.unref();

    serverProcess.on('error', (err) => {
        if (!silent) vscode.window.showErrorMessage(`Server error: ${err.message}`);
        serverProcess = null;
    });

    // Wait for startup
    await new Promise(r => setTimeout(r, 2000));
    await updateStatusBar();

    if (!silent) {
        vscode.window.showInformationMessage('🚀 Bridge Server started!');
    }
}

/**
 * Stop server
 */
async function stopServer() {
    // Kill any process on port 8000
    exec("lsof -ti :8000 | xargs kill -9 2>/dev/null", async () => {
        serverProcess = null;
        await updateStatusBar();
        vscode.window.showInformationMessage('Server stopped.');
    });
}

/**
 * Restart server
 */
async function restartServer() {
    await stopServer();
    await new Promise(r => setTimeout(r, 1000));
    await startServer(false);
}

function deactivate() {
    if (statusInterval) {
        clearInterval(statusInterval);
    }
}

module.exports = {
    activate,
    deactivate
};
