# Glazier: Bitlocker Package

<!--* freshness: { exempt: true } *-->

The Glazier Bitlocker package is a wrapper for Microsoft's
[BitLocker Drive Encryption Provider](https://docs.microsoft.com/en-us/windows/win32/secprov/bitlocker-drive-encryption-provider).

## Example Usage

```
// Connect to the volume
vol, err := bitlocker.Connect("c:")
if err != nil {
  return err
}
defer vol.Close()
// Prepare for encryption
if err := vol.Prepare(bitlocker.VolumeTypeDefault, bitlocker.EncryptionTypeSoftware); err != nil {
  return err
}
// Add a recovery protector
if err := vol.ProtectWithNumericalPassword(""); err != nil {
  return err
}
// Protect with TPM
if err := vol.ProtectWithTPM(nil); err != nil {
  return err
}
// Start encryption
if err := vol.Encrypt(bitlocker.XtsAES256, bitlocker.EncryptDataOnly); err != nil {
  return err
}
return nil
```
