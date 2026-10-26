# Bullet-hole shirt prop

A Halloween prop that looks like you've been shot clean through the chest.
A 7" DSI screen on the front shows the camera on your back, through a torn
wound. The screen shows what's behind you, so the hole looks see-through, with
blood pulsing around the edge and dripping down.

## How the illusion works

The screen is a window. The camera on the back sees what's behind you, and
the screen shows that picture in the same place on your chest, so the viewer
sees the scene through you. The wound area is the only part that shows the
camera. Everything around it is gore rendered by the Pi.

## Parts

- Raspberry Pi with a DSI connector (Pi 4 uses the 15-pin ribbon; Pi 5 needs
  the 22-to-15-pin adapter cable for the official 7" display)
- Official Raspberry Pi 7" touchscreen (800x480, DSI)
- Raspberry Pi Camera Module (any CSI module with picamera2 support)
- 5V USB power bank rated for 3A or more (a Pi 4 with the 7" display can draw
  around 2A)
- Two thin plates (foam board or 3 mm ABS) to hold the screen front and the
  Pi and camera back, with a ribbon cable running around the side
- Fake blood, a torn-edge latex or silicone wound piece around the bezel,
  and a T-shirt you're happy to ruin

## Software setup (Raspberry Pi OS)

```bash
sudo apt install -y python3-picamera2 python3-venv
git clone <this repo> ~/Bulletholeprop
cd ~/Bulletholeprop
python3 -m venv --system-site-packages .venv
.venv/bin/pip install -r requirements.txt

.venv/bin/python -m bullethole            # full screen
```

Desktop test without the Pi or camera:

```bash
python3 -m pip install -r requirements.txt
python3 -m bullethole --fake-camera --windowed
python3 -m unittest tests/test_gore.py
```

To see a single rendered frame as a PNG:

```bash
python3 -m bullethole.gore --out preview.png --seed 7
```

### Options

| Flag | What it does |
| --- | --- |
| `--mirror` | Flip the camera image left to right, if the illusion looks reversed |
| `--no-swap-rgb` | Turn off the channel swap, if colours look blue or orange |
| `--hole-radius 105` | Size of the wound in pixels |
| `--bpm 72` | Heartbeat speed of the pulsing rim |
| `--seed 7` | Same wound shape every run |
| `--fps 20` | Lower this if the Pi can't keep up |

Esc or Q quits.

## Auto-start on boot

Edit `User=` and `WorkingDirectory=` in `systemd/bullethole.service` to match
your Pi, then:

```bash
sudo cp systemd/bullethole.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now bullethole
```

If the screen is rotated, set `lcd_rotate=2` in `/boot/firmware/config.txt`.
Check that the camera is enabled with `rpicam-hello`.

## Costume build notes

- Mount the screen through a hole in the front of the shirt, with the plate
  behind it. The camera lens comes out through a second hole on the back.
  Leave the ribbon cable slack so the shirt can move.
- Put the Pi and power bank in a pocket or bag on the back, with the camera
  pointing straight out. The window illusion only works if the camera is
  roughly level with the screen.
- Blood: corn syrup with red food colouring and a little cocoa for depth.
  Seal the electronics first, since blood and a live Pi don't mix.

## Status

The software is tested headlessly: the rendering and the composite are
checked by `tests/test_gore.py`. The DSI display, camera colour order and
the systemd service have not been run on real hardware yet. Check the colour
and mirror options on the first power-up.
