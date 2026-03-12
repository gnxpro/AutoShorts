Write-Host "Building GNX Production release..."

pyinstaller main.py `
--name GNX_Production `
--onefile `
--noconsole `
--icon assets/icon.ico

Write-Host "Build completed."