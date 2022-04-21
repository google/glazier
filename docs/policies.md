# Glazier Installer Policies

<!--* freshness: { owner: '@tseknet' reviewed: '2022-01-17' } *-->

Policy modules determine whether or not Autobuild should be allowed to proceed
with an installation.

## Usage

Each module should inherit from `BasePolicy`, and will receive a BuildInfo
instance (`self._build_info`).

If a policy fails, the module should raise `ImagingPolicyException` with a
message explaining the cause of failure. This will abort the build.

If a policy causes a warning, the module should raise `ImagingPolicyWarning`.
This will not abort the build, but may present the warning to the user.

## Modules

### BIOSVersion

*BIOSVersion* checks whether the local bios version is a supported. If
the device is not fully supported (lower than a given version), the build fails.

### DeviceModel

*DeviceModel* checks whether the local device is a supported hardware model. If
the device is not fully supported (outside tier1), the user is prompted whether
or not to abort the build.

### DiskEncryption

*DiskEncryption* checks whether encryption is required of the host, and if so,
whether the host is capable of encryption (TPM is present).

### OperatingSystem

*UnsupportedOS* checks whether the operating system is supported.
