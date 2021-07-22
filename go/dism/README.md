# Glazier: DISM Package

<!--* freshness: { exempt: true } *-->

The Glazier DISM package is a wrapper for Microsoft's
[Deployment Image Servicing and Management (DISM) API](https://docs.microsoft.com/en-us/windows-hardware/manufacture/desktop/dism/deployment-image-servicing-and-management--dism--api).

## Example Usage

```
// Connect to DISM
s, err := dism.OpenSession(dism.DISM_ONLINE_IMAGE, "", "", dism.DismLogErrorsWarningsInfo, "", "")
if err != nil {
  return err
}
defer s.Close()

// Disable Features
for _, f := range []string{
  "SMB1Protocol",
}{
  if err := s.DisableFeature(f, "", nil, nil); err != nil && !errors.Is(err, windows.ERROR_SUCCESS_REBOOT_REQUIRED) {
    return err
  }
}
```
