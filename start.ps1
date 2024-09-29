# Start ngrok and get the URL
Start-Process -NoNewWindow -FilePath "ngrok.exe" -ArgumentList "http 8000" -RedirectStandardOutput ngrok.log

# Wait for ngrok to start and retrieve the URL
$ngrok_url = $null
while (-not $ngrok_url) {
    Start-Sleep -Seconds 1
    try {
        $ngrok_url = (Invoke-RestMethod http://127.0.0.1:4040/api/tunnels | Select-Object -ExpandProperty tunnels | Where-Object {$_.proto -eq 'https'}).public_url
    } catch {
        # Handle the case where the REST method fails (e.g., ngrok not yet started)
        $ngrok_url = $null
    }
}

# Append /login to the ngrok URL
$login_url = "$ngrok_url/login"

# Print the new URL
Write-Output "Ngrok URL: $ngrok_url"

# Update or add the NGROK_URL in the .env file in the desired format
$env_file = ".env"
if (Test-Path $env_file) {
    $env_content = Get-Content $env_file
    if ($env_content -match 'NGROK_URL=') {
        $updated_env_content = $env_content -replace 'NGROK_URL=.*', "NGROK_URL=$ngrok_url"
    } else {
        $updated_env_content = $env_content + "`r`nNGROK_URL=$ngrok_url"
    }
    $updated_env_content | Set-Content $env_file
} else {
    "NGROK_URL=$ngrok_url" | Out-File $env_file
}

# Start the docker-compose services
Start-Process -NoNewWindow -FilePath "docker-compose.exe" -ArgumentList "up"

# Open URL in Microsoft Edge
Start-Process "msedge.exe" -ArgumentList $login_url
Start-Sleep -Seconds 5 # Wait for Edge to start

# Get Edge process ID
$ngrokEdge = Get-Process -Name msedge | Where-Object { $_.MainWindowTitle -match "ngrok" }
$ngrokEdgeId = $ngrokEdge.Id

# Arrange Edge windows
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WindowHelper {
    [DllImport("user32.dll")]
    public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);
}
"@

$SWP_NOSIZE = 0x0001
$SWP_NOMOVE = 0x0002
$HWND_TOP = [IntPtr]::Zero

# Check if $ngrokEdge is not null before calling SetWindowPos
if ($ngrokEdge) {
    [WindowHelper]::SetWindowPos($ngrokEdge.MainWindowHandle, $HWND_TOP, $ngrokX, $ngrokY, $ngrokWidth, $ngrokHeight, $SWP_NOSIZE -bor $SWP_NOMOVE)
} else {
    Write-Output "Ngrok Edge process not found."
}

# Keep the script running to print the ngrok URL periodically
while ($true) {
    Write-Output "Ngrok URL: $ngrok_url"
    Start-Sleep -Seconds 60
}
