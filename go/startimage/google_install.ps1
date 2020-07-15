#Requires -RunAsAdministrator

<#
  .SYNOPSIS
    Install script for go/startimage.

  .DESCRIPTION
    Installs startimage.exe to $env:TEMP, to be used for testing.
#>

[CmdletBinding()]
param (
  [System.IO.FileInfo]$InstallDir = "$env:TEMP\startimage"
)

try {
  if (-not(Test-Path $InstallDir)) {
    New-Item -Type Directory $InstallDir -Force
    Write-Verbose "Successfully created directory: $InstallDir"
  }
}
catch {
  throw "Failed to create startimage directory: $_"
}

try {
  Copy-Item "$PSScriptRoot\startimage.exe" -Destination $InstallDir -Force
  Write-Verbose "Successfully copied '$PSScriptRoot\startimage.exe' to '$InstallDir\startimage.exe'"
}
catch {
  throw "Failed to copy startimage to destination: $_"
}

Write-Host "Successfully installed startimage to: $InstallDir"
exit 0
