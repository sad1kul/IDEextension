# Change Log

All notable changes to the Browser Bridge extension are documented in this file.

## [1.3.2] - 2026-07-06
### Fixed
- Removed hardcoded local development path from server discovery
- Improved server start/stop behavior for Windows
- Added safer cross-platform process handling for stopping the bridge server
- Cleaned up marketplace-facing packaging metadata
- Updated project documentation to match the current setup flow

### Changed
- Improved compatibility across macOS, Windows, and Linux
- Refined extension configuration descriptions

## [1.3.1] - 2026-02-09
### Changed
- Improved browser connection flow
- Added better multi-browser handling inside the IDE
- Refined project structure and extension packaging

### Fixed
- General stability fixes for the bridge workflow

## [1.0.0] - 2026-02-07
### Added
- Initial release
- Auto-setup wizard on first activation
- Python dependency auto-installation
- Native messaging host auto-registration
- MCP server auto-configuration
- Commands: Setup, Start Server, Stop Server, Check Status
- Real-time browser state streaming
- Console error capture
- Network failure detection
- Remote browser control (click, type)
- CORS diagnostics tool

