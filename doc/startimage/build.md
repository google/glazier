# Startimage Build Documentation

<!--* freshness: { owner: 'dantsek' reviewed: '2020-09-02' } *-->

[TOC]

TODO: Add external build documentation.

## Testing

Testing changes to Startimage

## Common Flags

TODO: Define or link to flags.

## Example Commands

### Standard

Standard image, with debug logs, and write the autobuild config values to
"SOFTWARE\Glazier" in the registry:

```powershell
./startimage.exe --alsologtostderr --debug --registry_root "SOFTWARE\Glazier" trusted --config_server "https://glazier.com/sign"
```

### BeyondCorp

Image [BeyondCorp](https://github.com/google/fresnel), with debug logs, write
the autobuild config values to "SOFTWARE\Glazier", and use a drive labeled
"BeyondCorp" as the source for the hash file and seed.json:

```powershell
./startimage.exe --alsologtostderr --debug --registry_root "SOFTWARE\Glazier" beyondcorp --sign_endpoint "https://glazier.com/sign" --drive_label "BeyondCorp" --hash_path "sources\boot.wim" --seed_path "BeyondCorp\seed.json"
```

NOTE: In this example, assume the drive labeled 'BeyondCorp' mounts at 'D:' ->
hash_path will automatically become `D:\sources\boot.wim` and seed_path will
automatically become `D:\BeyondCorp\seed.json`.
