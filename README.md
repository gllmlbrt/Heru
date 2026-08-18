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

## Fan control: AC vs EC

Which entity actually moves the fans depends on the fan type fitted. The unit
does not report this over Modbus without the service password (`4x01001`), so
try both:

| Entity | Register | Applies to |
| --- | --- | --- |
| **Supply fan speed**, **Exhaust fan speed** (%) | `4x00003`, `4x00004` | **EC fans** |
| Fan step (dropdown) | `4x00001` | AC fans only, and only while no weektimer program is active |

If the percentage sliders change the RPM and the step dropdown does nothing,
the unit has EC fans and `4x00001` is stored but ignored.

The **Fan step** select is disabled by default for that reason - on an EC unit
it would accept selections the unit ignores. Enable it from the entity settings
on an AC unit. The climate entity exposes temperature only, and its on/off uses
the Unit on coil (`0x00001`), which works with either fan type.

### Setpoint vs actual speed

The **Supply/Exhaust fan speed setpoint** numbers are the commanded base
speed. Boost, Away and Overpressure do not overwrite them - the unit overlays
its own speed while the mode is active and returns to the setpoint afterwards,
so the numbers stay where you left them throughout.

The speed actually running is reported by the **Current supply/exhaust fan
power** sensors (`3x00025`, `3x00026`).

### Why the mode switches can appear to do nothing

On EC fans the Boost, Away and Overpressure coils do not set a speed. They
select which per-step register the unit runs at:

- Away uses **Min fan speed** (`4x00005`)
- Boost uses **Mod** (`4x00006`) or **Max** (`4x00007`), chosen by
  **Boost speed step** (`4x00026`: 3 = Mod, 4 = Max)

The coil write succeeds and the mode switch stays on, but if those registers
hold values close to the speed already running, nothing visibly changes. Set
them to distinct values to make the modes take effect.

## Register Reference

This integration is based on:

- `Assets/Modbus_Registers_HERU_62_250_v07.pdf`
