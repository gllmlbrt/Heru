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

## Fan control

Two controls, both verified against a HERU 62-250 Gen 3 with EC fans:

- **Supply fan** and **Exhaust fan** entities write `4x00003` / `4x00004`.
  Standard fan entities: a percentage, off at 0%, restoring the previous
  speed when switched back on. This is the direct control.
- **Fan step** select gives the unit's own Off / 1-4 steps.

The climate entity exposes temperature only. Its on/off uses the Unit on coil
(`0x00001`), which works with either fan type.

### The step register cannot be written here

`4x00001` is the documented way to command a step, and the manual marks it
"AC fans only, and used only while no weektimer is active". On this unit a
write is acknowledged - the function code 6 response echoes the value - and
then discarded: reading back returns the previous value and the step sensors
do not move.

So **Fan step** commands the modes instead, which the unit does honour. Each
mode selects one of the per-step speed registers:

| Step | Mode set | Speed the unit runs at |
| --- | --- | --- |
| Off | Unit on = off | - |
| 1 | Away | Min fan speed (`4x00005`) |
| 2 | no mode | the fan entities (`4x00003` / `4x00004`) |
| 3 | Boost, `4x00026` = 3 | Mod fan speed (`4x00006`) |
| 4 | Boost, `4x00026` = 4 | Max fan speed (`4x00007`) |

Two consequences worth knowing:

- **Steps 3 and 4 are not permanent.** They use boost, which the unit ends by
  itself after the boost duration (`4x00027`). The select reads back from
  `3x00023`, the step actually running, so an expired boost shows as the step
  now in effect rather than the one requested.
- **A mode can appear to do nothing.** It only selects between the per-step
  registers, so if Min, Mod and Max hold values close to the speed already
  running, the mode changes and the fans do not. Set them to distinct values.

`Current fan speed` (`3x00022`) mirrors the unwritable `4x00001`, so it stays
at whatever the unit has stored and is a diagnostic only. The readings that
track reality are `Current supply/exhaust fan step`.

### Setpoint vs actual speed

A fan entity's percentage is the commanded base speed, which is what step 2
runs at. Boost, Away and Overpressure do not overwrite it - the unit runs at
their own register while the mode is active and returns to the commanded
value afterwards, so the fan entity stays where you left it throughout.

The speed actually running is on each fan as the `current_power` and
`current_rpm` attributes, and as the **Current supply/exhaust fan power**
sensors (`3x00025`, `3x00026`).

## Summer night cooling

The manual only ever writes "SNC" and never expands it, but the four registers
describe free cooling: ventilate with cool outside air instead of recovering
heat, when doing so will actually cool the house.

| Entity | Register | Decides |
| --- | --- | --- |
| Summer night cooling | `4x00016` | whether the feature runs at all |
| Summer night cooling high limit | `4x00015` | start - extract air above this means the house is too warm |
| Summer night cooling low limit | `4x00014` | stop - do not cool the house below this |
| Summer night cooling difference | `4x00013` | outside must be at least this much cooler than inside |

The difference limit is what stops the unit running its fans for nothing when
the outside air is barely cooler than the house. The register holds tenths of
a degree; the entity shows whole degrees.

Nothing in these registers references a clock, so whether the unit restricts
this to night hours by itself is not visible over Modbus.

## Filter change period

**Filter change period** (`4x00044`) is the filter timer, in months of 30
days. `0` turns the timer off and `6` to `12` set a period. **`1` to `5` are
not shorter periods** - the manual states the unit turns anything of 5 or
less into 0, so those settings disable the timer instead. The slider allows
them because the unit accepts the write; it just reads back as `0` on the
next poll, which is the unit's own behaviour showing through rather than
something the integration hides.

Home Assistant renders the month unit as `m`, which reads like minutes next
to the duration entities. The value is months.

**Filter days left** (`3x00020`) is the countdown that period drives, and it
only moves while the timer is on. With the period at `0` the unit parks the
register at `0`, so the sensor reports nothing rather than a countdown of
zero days that is not running. Its attributes carry
`filter_change_period_months` and `filter_timer_running` so the reason is
visible on the entity itself.

If the sensor still reads `0` with a period of 6 to 12 set, the timer has not
been started: press **Reset filter timer** (`0x00006`) once, which is what
sets the countdown to the configured period. The unit recomputes the days
itself; the integration only reads the register.

## The unit's clock

The unit keeps a weekday and a time of day, but no date, so **System time**
is text such as `Monday 14:32:05` rather than a timestamp. Its
`drift_seconds` attribute is how far the unit has wandered from Home
Assistant, signed and wrapped to the shortest distance so a Sunday to Monday
rollover reads as seconds rather than days.

**Sync clock** writes Home Assistant's local time to the unit. The registers
are a buffer and the order of access is part of the protocol:

- `4x00060` weekday - **reading** it copies the unit's time into the buffer,
  so a read starts here
- `4x00061` hours, `4x00062` minutes - staged in the buffer
- `4x00063` seconds - **writing** it commits the buffer, so a write ends here

## Register Reference

This integration is based on:

- `Assets/Modbus_Registers_HERU_62_250_v07.pdf`
