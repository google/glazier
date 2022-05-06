$Host.UI.RawUI.WindowTitle = 'Glazier'
$env:LOCALAPPDATA = 'X:\'
$env:PYTHONPATH = 'X:\path\to\glazier\src'
Write-Output 'Starting Glazier imaging process...'

# For a full list of Glazier flags, execute `python autobuild.py --helpfull`
$py_args = @(
  'X:\path\to\glazier\src\autobuild.py',
  '--config_root_path=/sub/path/on/your/web/server',
  '--resource_path=X:\path\to\glazier\resources',
  '--ca_certs_resource=X:\path\to\glazier\resources\ca_certs.crt',
  '--glazier_spec_os=windows10-stable',
  '--preserve_tasks=true'
)

& X:\Python37\python.exe $py_args
