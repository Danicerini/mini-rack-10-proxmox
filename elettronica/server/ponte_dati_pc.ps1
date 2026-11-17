# Ponte provvisorio: quando l'ESP e' attaccato al PC Windows (non a pve1),
# legge lo stato da pve1 (http://IP-DEL-NODO:9101) e lo manda sulla seriale ogni 5 s.
# Uso: powershell -ExecutionPolicy Bypass -File ponte_dati_pc.ps1 [-Porta COM4]
param([string]$Porta = "COM4", [string]$Url = "http://IP-DEL-NODO:9101/")

$p = New-Object System.IO.Ports.SerialPort $Porta, 115200
$p.DtrEnable = $false; $p.RtsEnable = $false; $p.NewLine = "`n"
$p.Open()
Write-Host "Ponte attivo su $Porta (Ctrl+C per fermare)"
try {
  while ($true) {
    try {
      $json = (Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 4).Content.Trim()
      $p.WriteLine($json)
      Write-Host ("{0:HH:mm:ss} inviati {1} byte" -f (Get-Date), $json.Length)
    } catch { Write-Host ("{0:HH:mm:ss} pve1 non risponde" -f (Get-Date)) }
    $r = $p.ReadExisting(); if ($r) { Write-Host $r.Trim() }
    Start-Sleep -Seconds 5
  }
} finally { $p.Close() }
