# Simple Bin Day Tracker

Home Assistant custom integration for tracking recurring waste and recycling collection days.

Configure up to 10 bins entirely through the Home Assistant UI. The integration calculates upcoming collection dates, exposes countdown sensors for each bin, and provides an aggregate sensor showing the next collection.

Designed to work cleanly with dashboard cards (e.g. Mushroom) without complex templates.

---

## Features

- Configure bins completely through the Home Assistant UI
- Supports up to **10 recurring bins**
- Per-bin countdown sensors (`today`, `tomorrow`, `X days`)
- Aggregate **Next Collection** sensor
- Primary / secondary bin logic for same-day collections
- Binary sensors for **collection today** and **collection tomorrow**
- Midnight refresh so countdowns update automatically
- Device grouping in Home Assistant
- Dashboard-friendly attributes including colour hex values

---

## Installation

### HACS (recommended)

1. Open **HACS**
2. Go to **Integrations**
3. Click the **⋮ menu (top right)**
4. Choose **Custom repositories**
5. Add: https://github.com/rcb-xxvii/bin-day-tracker


Category: **Integration**

6. Install **Simple Bin Day Tracker**
7. Restart Home Assistant

---

## Setup

After installation:

1. Go to **Settings → Devices & Services**
2. Click **Add Integration**
3. Search for **Bin Day Tracker**
4. Add the integration

You can then:

- Add bins
- Edit bins
- Delete bins
- Enable or disable bins
- Set bins as **Primary** or **Secondary**

---

## Bin Configuration

Each bin has the following properties:

| Setting | Description |
|-------|-------------|
| Name | Friendly bin name |
| Material | Material label |
| Colour | Display colour |
| Enabled | Enables/disables the bin |
| Primary | Preferred bin when multiple collections share the same day |
| Start date | First collection date |
| Repeat interval | Days between collections |

Future collection dates are calculated as:


start_date + (n × repeat_interval)


Where **n** is the smallest value that produces a date today or later.

---

## Entity Overview

### Aggregate Sensors


sensor.bin_day_tracker_next_collection


Attributes include:

- days_until
- next_collection
- selected_bin_label
- selected_bin_colour
- also_due
- display_text

### Per-Bin Sensors

Example:


sensor.bin_paper
sensor.bin_glass


State:


today
tomorrow
X days


Attributes include:

- material
- next_collection
- days_until
- colour
- primary
- enabled

### Binary Sensors


binary_sensor.bin_collection_today
binary_sensor.bin_collection_tomorrow


Useful for automations.

Example automation:


Notify if bin collection tomorrow


---

## Primary / Secondary Logic

When multiple bins share the same collection day:

1. All bins due that day are identified
2. If one or more **Primary** bins exist, the first primary bin is selected
3. Otherwise the first **Secondary** bin is selected

Other bins due that day appear in the `also_due` attribute.

---

## Example Dashboard Card

Example Mushroom template card:

```yaml
type: custom:mushroom-template-card
entity: sensor.bin_day_tracker_next_collection
primary: "{{ state_attr(entity,'selected_bin_label') }}"
secondary: "{{ state_attr(entity,'display_text') }}"
icon: mdi:trash-can-outline
icon_color: "{{ state_attr(entity,'selected_bin_colour') }}"
