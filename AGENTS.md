# Project instructions

Work on the user's fork at `neusse/openCook`; `upstream` points to `oliexdev/openCook`.
Use Windows-native Python and PowerShell-compatible commands. Prefer PowerShell 7 and
the global `safe-pwsh` runner for nontrivial scripts. Keep owner data and runtime
state under ignored `data/`. Fail clearly when a real export, photo, or favorite
is missing; never substitute sample or synthetic data.

For ChefTap migration, phone installation, or recipe import, read
[`docs/CHEFTAP_MIGRATION_HANDOFF.md`](docs/CHEFTAP_MIGRATION_HANDOFF.md) first.
For ChefTap feature parity or enhancement planning, read
[`docs/CHEFTAP_FEATURE_GAPS.md`](docs/CHEFTAP_FEATURE_GAPS.md) first.

The target is an Android app that works locally without an account or cloud.
The optional openCook server is a separate choice; keep it optional. Before
changing or uninstalling an installed app, preserve any owner data it holds
and verify the saved copy.
