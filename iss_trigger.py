
import time, math, requests, serial, sys, csv, os

# ---------- SETTINGS ----------
PORT = "/dev/ttyUSB0"   # change if needed (e.g., /dev/ttyACM0)
BAUD = 115200           # must match your Arduino sketch
HOME_LAT = 46.624       # Klagenfurt
HOME_LON = 14.307
NEAR_KM  = 1000         # try 1500 → 1000 → 800
POLL_SEC = 5            # seconds between API polls
HEARTBEAT_SEC = 60      # resend current state every N seconds
API_URL = "https://api.wheretheiss.at/v1/satellites/25544"
# -----------------------------

# ---------- LOG SETUP ----------
log_path = "iss_log.csv"
if not os.path.exists(log_path):
    with open(log_path, "w", newline="") as f:
        csv.writer(f).writerow(["timestamp", "lat", "lon", "dist_km", "state"])
# --------------------------------

# Small requests session (faster + reuses TCP)
_session = requests.Session()

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

def iss_now():
    """Robust ISS fetch with retries/backoff."""
    backoffs = [0.6, 0.9, 1.3, 2.0, 3.0]  # ~5 tries
    for i, pause in enumerate([0.0] + backoffs):
        try:
            if pause: time.sleep(pause)
            r = _session.get(API_URL, timeout=6)
            r.raise_for_status()
            d = r.json()
            return float(d["latitude"]), float(d["longitude"])
        except Exception as e:
            if i == len(backoffs):   # last attempt failed
                raise
            # else loop and retry
    # Should never reach here
    raise RuntimeError("Unexpected ISS fetch failure")

def main():
    print(f"Opening serial {PORT} @ {BAUD} …")
    ser = serial.Serial(PORT, BAUD, timeout=2)
    time.sleep(2)  # allow Arduino reset

    last_state = None
    last_heartbeat = 0

    while True:
        try:
            lat, lon = iss_now()
            dist = haversine_km(HOME_LAT, HOME_LON, lat, lon)
            state = 'S' if dist <= NEAR_KM else 'N'

            now = time.time()
            # Send only on change + periodic heartbeat
            if (state != last_state) or (now - last_heartbeat > HEARTBEAT_SEC):
                ser.write(state.encode('ascii'))
                last_state = state
                last_heartbeat = now
                # Optional loud console line on change:
                # print(">>> ALERT: ISS NEAR — sending S <<<" if state=='S' else ">>> CLEAR: ISS far — sending N <<<")

            # Console output
            print(f"ISS @ ({lat:.2f}, {lon:.2f})  dist={dist:.0f} km  -> {'NEAR[S]' if state=='S' else 'far[N]'}")

            # Append to CSV log
            with open(log_path, "a", newline="") as f:
                csv.writer(f).writerow([
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                    f"{lat:.6f}", f"{lon:.6f}", f"{dist:.0f}", state
                ])

            time.sleep(POLL_SEC)

        except KeyboardInterrupt:
            print("\nExiting… sending N and closing.")
            try: ser.write(b'N')
            except: pass
            break
        except Exception as e:
            # Network/API hiccup or other error — print and keep going
            print("Error:", e)
            time.sleep(3)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Fatal:", e, file=sys.stderr)
        sys.exit(1)

