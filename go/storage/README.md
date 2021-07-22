# Glazier: Storage Package

<!--* freshness: { exempt: true } *-->

The Glazier Storage package is a wrapper for Microsoft's
[Windows Storage Management API](https://docs.microsoft.com/en-us/previous-versions/windows/desktop/stormgmt/windows-storage-management-api-portal).

## Example Usage

```
// Connect the API
svc, err := storage.Connect()
if err != nil {
  return err
}
defer svc.Close()

// Retrieve a disk
d, err := svc.GetDisks("WHERE Number=1")
if err != nil {
  return err
}
defer d.Close()

if len(d.Disks) < 1 {
  return errors.New("no disks found")
}
disk := d.Disks[0]

// Initialize the disk
if _, err := disk.Initialize(storage.MbrStyle); err != nil {
  return err
}

// Create a partition and assign drive letter D
part, _, err := disk.CreatePartition(0, true, 0, 0, "d", false, &storage.MbrTypes.IFS, nil, false, true)
if err != nil {
  return err
}
defer part.Close()

// Get the new volume
vset, err := svc.GetVolumes("WHERE DriveLetter='D'")
if err != nil {
  return err
}
defer vset.Close()

if len(vset.Volumes) < 1 {
  return errors.New("no volumes found")
}

// Format the volume with NTFS
fv, _, err := vset.Volumes[0].Format("NTFS", "", 0, false, true, false, false, false, false, false)
if err != nil {
  return err
}
defer fv.Close()
```
