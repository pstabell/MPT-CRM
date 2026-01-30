# Fix network profile to allow mobile scanner access
Write-Host "Current network profile:" -ForegroundColor Yellow
Get-NetConnectionProfile | Format-Table Name, InterfaceAlias, NetworkCategory -AutoSize

Write-Host "`nChanging network to Private..." -ForegroundColor Green
Get-NetConnectionProfile | Set-NetConnectionProfile -NetworkCategory Private

Write-Host "`nNew network profile:" -ForegroundColor Yellow
Get-NetConnectionProfile | Format-Table Name, InterfaceAlias, NetworkCategory -AutoSize

Write-Host "`nDone! Try accessing http://192.168.0.21:5000 from your phone now." -ForegroundColor Green
pause
