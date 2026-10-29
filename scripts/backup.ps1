[CmdletBinding()]
param([string]$Destination)
. (Join-Path $PSScriptRoot 'lib\Common.ps1')
$log=Initialize-AgentSecLog -Category 'updates' -ScriptName $MyInvocation.MyCommand.Name
try {
    $data=Get-AgentSecDataDir;if(-not $Destination){$Destination=Join-Path $data 'backups'};$db=Join-Path $data 'agentsec.db';if(-not(Test-Path $db)){throw "Database not found: $db"}
    Stop-AgentSecProcesses
    New-Item -ItemType Directory -Force $Destination|Out-Null;$stamp=Get-Date -Format 'yyyyMMdd-HHmmss';$stage=Join-Path $env:TEMP "agentsec-backup-$stamp";New-Item -ItemType Directory $stage|Out-Null
    try{Copy-Item $db $stage;if(Test-Path (Join-Path $data '.secret-key')){Copy-Item (Join-Path $data '.secret-key') $stage};foreach($name in @('reports','evidence')){if(Test-Path (Join-Path $data $name)){Copy-Item -Recurse (Join-Path $data $name) $stage}};$manifest=@{created_at=(Get-Date -Format o);version=$script:AgentSecVersion;database_sha256=(Get-FileHash (Join-Path $stage 'agentsec.db') -Algorithm SHA256).Hash;contains_secret_key=(Test-Path (Join-Path $stage '.secret-key'))}|ConvertTo-Json;$manifest|Set-Content -Encoding UTF8 (Join-Path $stage 'manifest.json');$zip=Join-Path $Destination "agentsec-backup-$stamp.zip";Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $zip;Write-Step "Backup created: $zip" 'OK';Write-Step 'The archive may contain the connector encryption key; protect it as sensitive data.' 'WARN'}finally{if(Test-Path $stage){Remove-Item -Recurse -Force $stage}}
    Complete-AgentSecLog 0;exit 0
}catch{Write-Step $_.Exception.Message 'ERROR';Complete-AgentSecLog 1;exit 1}
