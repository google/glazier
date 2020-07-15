#Requires -RunAsAdministrator

<#
  .SYNOPSIS
    Uninstall script for go/startimage.

  .DESCRIPTION
    Uninstalls startimage.exe from $env:TEMP.
#>

[CmdletBinding()]
param (
  [System.IO.FileInfo]$InstallDir = "$env:TEMP\startimage"
)

# Delete Binary
if (Test-Path $InstallDir) {
  try {
    Remove-Item -Recurse $InstallDir -Force
    Write-Verbose "Successfully removed directory: $InstallDir"
  }
  catch {
    throw "Error deleting directory '$InstallDir': $_"
  }
}

Write-Host 'Successfully uninstalled startimage!'
exit 0
