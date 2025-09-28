# Network Stress Tester

> **Python-based network stress testing tool** — generate TCP/UDP/ICMP/DNS/raw packets, run predefined scenarios (SYN flood, UDP flood, HTTP load, DNS stress, mixed floods), or craft custom tests.
> **WARNING:** Only test networks/systems you own or have explicit permission to test. Misuse is illegal and unethical.

---

## Table of Contents

* [Overview](#overview)
* [Features](#features)
* [Prerequisites](#prerequisites)
* [Installation](#installation)
* [Usage](#usage)

  * [Interactive Mode](#interactive-mode)
  * [Command-Line Mode](#command-line-mode)
  * [Predefined Scenarios](#predefined-scenarios)
  * [Examples](#examples)
* [Output & Logging](#output--logging)
* [Rate Control & Implementation Notes](#rate-control--implementation-notes)
* [Ethical & Legal Considerations](#ethical--legal-considerations)
* [Troubleshooting](#troubleshooting)
* [Example Log Output](#example-log-output)
* [Future Improvements](#future-improvements)
* [License](#license)
* [Contact](#contact)

---

## Overview

The **Network Stress Tester** is a Python tool using **Scapy** to craft and send packets for stress and resilience testing. It supports interactive and CLI modes, multiple protocols, rate control (token bucket), multithreading, real-time monitoring, and logging.

---

## Features

* Multiple protocols: **TCP**, **UDP**, **ICMP**, **DNS**, and **raw** packets.
* Predefined test scenarios:

  * SYN Flood (TCP)
  * UDP Flood
  * ICMP Flood (Ping)
  * HTTP Load Test
  * DNS Stress Test
  * Mixed Protocol Flood (TCP + UDP + ICMP)
* Customizable parameters: target, port, protocol, duration, packet rate, threads, payload size.
* Token-bucket rate control for precise PPS (packets per second).
* Multi-threaded sending for higher throughput.
* Real-time monitoring: packets sent, current rate, elapsed time.
* Logging: `network_tester.log` stores test metadata and errors.
* Input validation and clear ethical warnings.

---

## Prerequisites

* **Python 3.6+**

  ```bash
  python3 --version
  ```
* **Scapy**

  ```bash
  pip install scapy
  ```
* **Root privileges** (required for raw sockets / packet crafting): run with `sudo`.
* **Optional:** `tcpreplay` for high-speed `sendpfast` (Debian/Ubuntu example):

  ```bash
  sudo apt-get install tcpreplay
  ```

---

## Installation

1. Save the script as `network_tester.py`.
2. Make executable (optional):

   ```bash
   chmod +x network_tester.py
   ```
3. Run with `sudo` when sending raw packets:

   ```bash
   sudo python3 network_tester.py
   ```

---

## Usage

### Interactive Mode

Run without arguments to open the menu-driven interface:

```bash
sudo python3 network_tester.py
```

Menu options typically include:

* Quick Test (minimal required inputs)
* Advanced Test (choose a predefined scenario)
* Custom Test (full parameter control)
* Stop Test
* Exit

### Command-Line Mode

Run tests directly from CLI:

```bash
sudo python3 network_tester.py [target] [options]
```

**Command-line options**

```
target:                 Target IP address or hostname (required for CLI mode)
-p, --port              Target port (defaults to protocol-specific)
-t, --protocol          Protocol: tcp | udp | icmp | dns | raw  (default: tcp)
-d, --duration          Duration in seconds (default: 10)
-r, --rate              Packets per second (default: 100)
-n, --threads           Number of threads (default: 3)
-s, --size              Payload size in bytes (default: 64)
-a, --advanced          Run predefined scenario: syn-flood, udp-flood, icmp-flood,
                        http-load, dns-test, mixed-flood
--json                  Output results in JSON format
--html                  Generate an HTML report
-o, --output            Output filename prefix (for reports/logs)
```

### Predefined Scenarios (defaults used unless overridden)

* `syn-flood` — TCP SYN flood (example default: **5000 pps**, **60s**)
* `udp-flood` — UDP flood
* `icmp-flood` — ICMP ping flood
* `http-load` — simulate many HTTP requests (requires HTTP payload/method)
* `dns-test` — DNS query stress to port 53
* `mixed-flood` — mixes TCP/UDP/ICMP (example default: **3000 pps**, **60s**)

### Examples

Run a SYN Flood:

```bash
sudo python3 network_tester.py 192.168.1.1 -a syn-flood
# runs: TCP SYN flood at 5000 pps for 60 seconds (default)
```

Custom DNS test:

```bash
sudo python3 network_tester.py 192.168.1.1 -p 53 -t dns -d 60 -r 1000 -n 5 -s 128
# DNS packets to port 53, 1000 pps, 60s, 5 threads, 128B payload
```

Mixed protocol flood:

```bash
sudo python3 network_tester.py 192.168.1.1 -a mixed-flood
# Mix of TCP/UDP/ICMP at 3000 pps for 60s (default)
```

---

## Output & Logging

* **Console**: real-time progress (packets sent, instantaneous/average rate, elapsed time).
* **Log file**: `network_tester.log` — recorded test configuration, start/stop times, totals and errors.
* **Reports**: optional JSON or HTML report generation (if flags provided).

---

## Rate Control & Implementation Notes

* Uses a **token bucket** algorithm to control packet send rate precisely across threads.
* Threads pick from a shared bucket of tokens; token refill aligned to desired PPS.
* High packet rates may be CPU- or NIC-limited; consider `tcpreplay`/`sendpfast` for very high throughput and pcap-based replay.
* Multithreading increases throughput but also increases host load — monitor CPU and NIC utilization during tests.

---

## Ethical & Legal Considerations

**READ BEFORE USING:**

* **Authorized Use Only.** Run tests only on networks/devices you own or have written permission to test.
* Unauthorized testing can cause outages and expose you to legal action (e.g., CFAA in the U.S. or local equivalents).
* Prefer controlled lab or VM environments for development/testing.
* Obtain written permission from stakeholders and schedule tests to minimize impact.

---

## Troubleshooting

**Root Privileges Error**

* Ensure you run the script with `sudo`:

  ```bash
  sudo python3 network_tester.py
  ```

**Scapy Not Found**

* Install Scapy:

  ```bash
  pip install scapy
  ```
* Test import:

  ```bash
  python3 -c "import scapy; print(scapy.__version__)"
  ```

**Invalid IP/Hostname**

* Verify the target is reachable and resolvable:

  ```bash
  ping -c 3 example.com
  ```

**High CPU Usage**

* Reduce `-r` (rate) or `-n` (threads). Use `htop`/`top` to monitor CPU. Consider `tcpreplay` for very high rates.

**Permission / Firewall Issues**

* Ensure local firewall or IDS/IPS doesn't block crafted packets. Use a lab environment to avoid production disruptions.

---

## Example Log Output

```
2025-09-28 18:30:45,123 - INFO - Starting TCP test to 192.168.1.1:80, Duration: 60s, Rate: 5000 pps, Threads: 3, Payload size: 64 bytes
2025-09-28 18:31:45,456 - INFO - Test completed. Sent 299850 packets, Average rate: 4997.5 pps, Duration: 60.02s
```

---

## Future Improvements

* Add **packet capture** and automatic analysis of target responses (pcap + analysis).
* Graphical visualization: packet rate over time, CPU/NIC utilization charts.
* Batch sending using `sendpfast` + `tcpreplay` integration for extreme throughput.
* Support additional application-level protocols and more realistic traffic (e.g., full HTTP(S) transactions with TLS).
* Distributed testing mode (coordinated clients) with centralized result aggregation.

---

## License

Provided **as-is**, without warranty. Use responsibly and at your own risk.This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Contact

If you find bugs, have suggestions, or want to contribute, open an issue or contact the developer listed in the project repository.

---

### Quick reminder

**Always get written permission before testing a target.** Unauthorized testing can have serious legal and ethical consequences.
