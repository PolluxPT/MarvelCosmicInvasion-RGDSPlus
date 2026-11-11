# Release packaging

The release is a launcher-only update over the privately prepared Alpha 8
standalone installation. Copying an unmodified retail game into this
repository does not produce that installation.

`release/APPS/MarvelCosmicInvasion_RGDSPlus/tools/launcher.py` is the complete
final launcher. The adjacent runtime profile contains hashes/sizes, never
game bytes. `integration-source` preserves the original adapter patch sources
for review; they refer to private assemblies and are not a retail-to-port
build system. A private Alpha 8 build is required to regenerate or validate
the game/native integration. No device-side compilation is required for
installing the Final launcher update.

`python3 scripts/verify_public.py` audits this public tree. The GitHub Actions
workflow runs it automatically. It rejects executable game files, native
binaries, artwork, saves, logs and private installation ZIPs.

Do not add the maintainer's build directory, gamedata, library downloads or
PERSONAL archive. See .gitignore and PUBLISH_GITHUB.txt in the outer kit.
