# Damage calculator changelog

## 2.1.0 — current rules

- Adopted the workbook attack-power pipeline.
- Added flat weapon attack and flat attack power parsing.
- Added live engraving-description parsing.
- Added Cursed Doll, current Grudge, current Mass Increase, current
  Adrenaline, and current Raid Captain values.
- Preserved explicit user overrides: final-only flooring, additive
  avatar/pet main-stat percentages, and Sonic Breakthrough 15%/30%
  over-cap coefficients.
- Added versioned filenames, manifests, and CLI selection.

## 2.0.0 — season3 workbook compatibility

- Reproduces the workbook's intermediate flooring at main stat, weapon
  attack, and attack power.
- Uses the workbook's Sonic Breakthrough 10%/20% over-cap coefficients.
- Uses the workbook sample's expedition/potion and feast constants.

## 1.0.0 — conversation example

- Original API parser and single-skill damage model.
- Uses example fallback effect values and final-only flooring.
