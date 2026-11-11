# MARVEL Cosmic Invasion — RGDS+ Final 1.0

Standalone Linux ARM64 adapter for Anbernic RGDS+ stock Linux firmware.
No PortMaster is used during play.

## Public release scope

**This public package is an update for an existing privately prepared Alpha 8
standalone installation.** The public ZIP contains only the final launcher and
its runtime checksum metadata. The player supplies the prepared game,
runtime and native libraries from their own working installation.

A fresh retail Steam/GOG/Linux game folder requires additional preparation
and is not an automatically supported input to this public update. A complete
retail-to-handheld preparation tool is outside this release. This is stated
explicitly so a download is not mistaken for a complete fresh-install port.

The maintainer's PERSONAL clean-install archive contains commercial files
and must stay private. It must never be uploaded to this repository or Releases.

## Install the Final update

1. Download `MARVELCosmicInvasion_RGDSPlus_v1.0.0_Final_Update.zip` from Releases.
2. Extract it on your computer.
3. Copy `APPS` into `Roms` on your RGDS+ SD card. Merge and replace files.
4. Keep the existing game folder and `savedata`.
5. Open **APPS > MarvelCosmicInvasion** on the handheld.

Install location: `Roms/APPS/MarvelCosmicInvasion_RGDSPlus/`.
Launcher: `Roms/APPS/MarvelCosmicInvasion.sh` from the existing installation.

## Controls

A/B and X/Y retain the user-tested swaps from Alpha 7b. D-pad and left stick
provide movement. Shoulder/trigger controls, START and SELECT retain their
measured mappings. Hold START + SELECT for 1.5 seconds as an exit backup.
Menu Exit also notifies the launcher and mutes game audio during shutdown.
Physical volume buttons retain the quadratic volume curve; the session
restores menu volume, bottom-screen settings and governors on exit.

## Final changes

Automatic `MARVELCosmicInvasion_TestLogs.zip` creation has been removed.
Local diagnostic files remain inside the game's `logs` folder for failures;
no diagnostic application is installed. Existing ZIPs can be removed manually.
The tested Alpha 8 gameplay, graphics, audio and controller code is retained.

## Known limits

Heavy battles can still drop frames. The latest supplied test contained a
19 presents/s sample. A fixed 60 FPS experience is not claimed. Loading can
still pause while assets initialize. Mono heap and private swap/early-exit
safeguards reduce memory pressure but cannot guarantee zero crashes.

The latest Alpha 8 handheld session returned normally with exit code 0;
launcher menu return followed the exit request by about 1.2 seconds.
Final 1.0 changes only the launcher and its checksum metadata; the new
no-ZIP behavior passed local static and archive checks.

## Ownership and attribution

Users must own the game and supply its files privately. No game code,
textures, music, banks, screenshots, logos, proprietary native libraries or
prepared game binaries are distributed in this public release.

This is an unofficial community adaptation, not affiliated with Marvel,
Tribute Games, Dotemu, Anbernic or upstream runtime authors. Names identify
the game and supported device; no trademark rights are granted.
See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [BUILDING.md](BUILDING.md).
