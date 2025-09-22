# LiveKit CLI Fix for Windows

## Problem
LiveKit CLI installed via winget wasn't accessible from command line.

## Solution
1. **Find CLI location:**
   ```bash
   find /c/Users/Admin -name "lk.exe" 2>/dev/null
   ```
   Found at: `/c/Users/Admin/AppData/Local/Microsoft/WinGet/Packages/LiveKit.LiveKitCLI_Microsoft.Winget.Source_8wekyb3d8bbwe/lk.exe`

2. **Add to PATH permanently:**
   ```bash
   echo 'export PATH="$PATH:/c/Users/Admin/AppData/Local/Microsoft/WinGet/Packages/LiveKit.LiveKitCLI_Microsoft.Winget.Source_8wekyb3d8bbwe"' >> ~/.bashrc
   source ~/.bashrc
   ```

3. **Test CLI:**
   ```bash
   lk --version  # Should work now
   ```

## Now Available Commands:
- `lk agent deploy --subdomain "project" .`
- `lk agent logs --subdomain "project"`
- `lk dispatch create --new-room --agent-name "agent" --metadata "data"`
- `lk room list`
- etc.

## Key Capabilities Restored:
- ✅ Deploy agents from command line
- ✅ View real-time agent logs
- ✅ Create dispatches for testing
- ✅ Monitor room status
- ✅ Kill sessions and manage agents