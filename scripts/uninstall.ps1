[CmdletBinding(SupportsShouldProcess,ConfirmImpact='High')]
param([switch]$DeleteUserData,[switch]$Confirmed)
. (Join-Path $PSScriptRoot 'lib\Common.ps1')
$log=Initialize-AgentSecLog -Category 'installation' -ScriptName $MyInvocation.MyCommand.Name
try {
    Assert-Windows
    Stop-AgentSecProcesses
    $roots=@('HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*')
    $entry=Get-ItemProperty $roots -ErrorAction SilentlyContinue|Where-Object{$_.DisplayName -eq 'AgentSec Inspector'}|Select-Object -First 1
    if($entry){
        $uninstall=[string]$entry.UninstallString
        if($uninstall -match 'MsiExec(?:\.exe)?\s+/[IX]\s*({[^}]+})'){Invoke-Checked msiexec @('/x',$Matches[1])}
        elseif($uninstall -match '^"([^"]+)"(.*)$'){$exe=$Matches[1];$args=$Matches[2].Trim();if(-not(Test-Path $exe)){throw 'Registered uninstaller is missing.'};& $exe $args;if($LASTEXITCODE){throw "Uninstaller failed: $LASTEXITCODE"}}
        else{throw 'Uninstaller registration format is not safely recognised.'}
    }else{Write-Step 'No installed application registration found.' 'WARN'}
    $data=Get-AgentSecDataDir
    if($DeleteUserData){if(-not $Confirmed){throw 'Data deletion requires both -DeleteUserData and -Confirmed.'};if($PSCmdlet.ShouldProcess($data,'Permanently delete all AgentSec projects, evidence, reports and settings')){if(Test-Path $data){Remove-Item -Recurse -Force $data};Write-Step "User data deleted: $data" 'WARN'}}else{Write-Step "User data preserved: $data" 'OK'}
    $temp=Join-Path $env:TEMP 'AgentSec';if(Test-Path $temp){Remove-Item -Recurse -Force $temp}
    Complete-AgentSecLog 0;exit 0
}catch{Write-Step $_.Exception.Message 'ERROR';Complete-AgentSecLog 1;exit 1}
