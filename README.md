# Heru

Home Assistant custom integration for older generation 3 HERU Östberg ventilation systems over Modbus TCP.

## Features

- Config flow setup from Home Assistant UI
- Telemetry and status entities based on `Modbus_Registers_HERU_62_250_v07.pdf`
  - Input register sensors (temperatures, pressure, humidity, CO2, fan stats, etc.).
    Temperatures are reported by the unit in tenths of a degree as signed values
    and are converted accordingly.
  - Discrete-input binary sensors (alarms, switches, run states). `1x00005` -
    `1x00009` are not implemented by the unit, so the inputs are read as two
    blocks either side of that gap.
- Mode switches for the read/write coils:
  - Unit on (`0x00001`), Overpressure (`0x00002`), Boost (`0x00003`), Away (`0x00004`)
- Buttons for the momentary coils, which act on write and always read back 0:
  - Clear alarms (`0x00005`), Reset filter timer (`0x00006`)
- Climate entity for:
  - Temperature setpoint (`4x00002`)
  - User fan speed setpoint (`4x00001`)
- Diagnostic entities (component ID, sensor open/short bit fields, control
  voltages, fan steps, alarms) are categorised as diagnostics so they stay out
  of the main device controls.

## Install with HACS (Custom Repository)

1. Open **HACS** in Home Assistant.
2. Go to **Integrations**.
3. Open the 3-dot menu in the top right and choose **Custom repositories**.
4. Add:
   - **Repository**: `https://github.com/gllmlbrt/Heru`
   - **Category**: `Integration`
5. Click **Add**.
6. Search for **Heru** in HACS Integrations and install it.
7. Restart Home Assistant.

## HACS release requirement

HACS installs integrations from a tagged GitHub version. The version in
`custom_components/heru/manifest.json` must match an existing Git tag or GitHub
release in this repository.

For example, with `"version": "0.1.0"` in the manifest, the repository also
needs a `0.1.0` or `v0.1.0` tag published on GitHub. Without a matching tag,
HACS can fall back to a commit SHA and show an error like:

`The version 9b6fa71 for this integration can not be used with HACS.`

## Configure

1. Go to **Settings → Devices & Services**.
2. Click **Add Integration** and search for **Heru**.
3. Enter:
   - **Name** (default: `Heru`)
   - **Host** (IP address of the Modbus bridge/controller)
   - **Port** (default: `502`)
4. Submit to create the device and entities.

## Register Reference

This integration is based on:

- `Assets/Modbus_Registers_HERU_62_250_v07.pdf`
