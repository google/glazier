# Glazier Lock Screen UI Manager

<!--* freshness: { owner: '@mjoliver' reviewed: '2026-06-11' } *-->

`lockscreenui` is a robust, reusable Go library for displaying provisioning,
installation, or configuration progress directly on the Windows lock screen
(`LogonUI.exe`).

It is fully configurable, supporting custom background images, solid background
colors, tailored title prefixes, and custom footer messages.

## Features

*   **Seamless Lock Screen Integration**: Dynamically generates progress
    wallpaper frames and applies them via Windows Group Policy registry keys
    (`SOFTWARE\Policies\Microsoft\Windows\Personalization\LockScreenImage`).
*   **Instant Visual Updates**: Safely refreshes the Windows logon screen
    (`taskkill /F /IM LogonUI.exe`) to force immediate redraws without requiring
    a reboot.
*   **Reboot Resilient**: Because Group Policy registry keys persist across
    restarts, Windows Winlogon automatically displays the latest progress screen
    immediately upon bootup.
*   **Flexible Overlay Positioning**: Supports placing the progress box in the
    `center`, `top`, or `bottom` of the screen to avoid overlapping with active
    Windows login credential tiles.
*   **Distinct Error Alerting**: Provides a dedicated `UpdateLockScreenError`
    API that renders a striking translucent dark red alert box to notify users
    of failures and guide them on recovery steps.
*   **Automatic Footprint Cleanup**: Includes a clean `Cleanup()` method to
    remove Group Policy overrides and purge temporary image files once
    provisioning is complete.

## Usage Example

```go
package main

import (
    "context"
    "image/color"
    "log"

    "github.com/google/glazier/go/lockscreenui"
)

func main() {
    ctx := context.Background()

    // 1. Define configuration
    cfg := lockscreenui.Config{
        TempDir:         `C:\Provisioning\TempScreens`,
        BgColor:         color.RGBA{0, 120, 215, 255}, // Solid Windows Blue
        TitlePrefix:     "System Setup: ",
        FooterText:      "Please do not turn off your computer",
        ErrorTitle:      "Setup Error (Step Failed)",
        ErrorFooterText: "Please reboot the machine to retry setup",
        OverlayPosition: lockscreenui.PositionBottom, // Position at the bottom to avoid credential tiles
    }

    // 2. Initialize UI Manager
    ui, err := lockscreenui.NewProvisioningUI(ctx, cfg)
    if err != nil {
        log.Fatalf("Failed to initialize UI: %v", err)
    }
    defer ui.Cleanup(ctx) // Ensures policies and temp files are removed upon exit

    // 3. Update Progress
    if err := ui.UpdateLockScreen(ctx, 1, "Step 1 of 3: Installing system packages..."); err != nil {
        log.Printf("Progress update failed: %v", err)
    }

    // 4. Report Error (if a step fails)
    // ui.UpdateLockScreenError(ctx, 1, "Package download failed: network timeout")
}
```

## Embedding a Custom Background Image

You can bake a custom background image (JPEG or PNG) directly into your compiled
Go binary using Go's native `//go:embed` directive. This ensures your tool
remains a single standalone executable without relying on external asset files
on the host machine.

```go
package main

import (
    "bytes"
    "context"
    "embed"
    "image"
    "log"

    "github.com/google/glazier/go/lockscreenui"

    _ "image/jpeg" // Essential for decoding embedded JPEG images
)

//go:embed assets/wallpaper.jpeg
var embeddedFS embed.FS

func main() {
    ctx := context.Background()

    // 1. Read and decode the embedded image
    data, err := embeddedFS.ReadFile("assets/wallpaper.jpeg")
    if err != nil {
        log.Fatalf("Failed to read embedded image: %v", err)
    }
    img, _, err := image.Decode(bytes.NewReader(data))
    if err != nil {
        log.Fatalf("Failed to decode embedded image: %v", err)
    }

    // 2. Pass the decoded image to the configuration
    cfg := lockscreenui.Config{
        TempDir:         `C:\Provisioning\TempScreens`,
        BaseImage:       img,
        TitlePrefix:     "Setup: ",
        OverlayPosition: lockscreenui.PositionBottom,
    }

    ui, err := lockscreenui.NewProvisioningUI(ctx, cfg)
    if err != nil {
        log.Fatalf("Failed to initialize UI: %v", err)
    }
    defer ui.Cleanup(ctx)

    ui.UpdateLockScreen(ctx, 1, "Applying embedded background...")
}
```
