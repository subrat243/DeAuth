# Advanced Network Stress Tester

## Overview

A lightweight yet powerful network stress testing tool built with Scapy that allows for comprehensive network testing with various protocols and traffic patterns. Designed for both quick assessments and in-depth network analysis while maintaining low resource usage.

## Features

- **Multiple Protocol Support**: TCP (SYN flood), UDP flood, ICMP (ping) flood
- **Predefined Test Scenarios**: Common attack simulations (SYN flood, UDP flood, etc.)
- **Customizable Tests**: Full control over packet rate, size, duration, and threads
- **Efficient Operation**: Optimized for low-end devices with minimal resource usage
- **Dual Interface**: Interactive menu and command-line operation
- **Real-time Monitoring**: Live statistics during test execution
- **IP Spoofing**: Random source IP generation capability

## Installation

1. **Requirements**:
   - Python 3.6+
   - Root/Administrator privileges
   - Scapy library

2. **Install Scapy**:
   ```bash
   pip install scapy
   ```

3. **Download the tool**:
   ```bash
   git clone https://github.com/subrat243/DeAuth.git
   cd DeAuth
   ```

## Usage

### Interactive Mode (Recommended)
```bash
sudo python3 deauth.py
```

Follow the on-screen menu to configure and run tests.

### Command-Line Mode

**Basic Syntax**:
```bash
sudo python3 deauth.py <target> [options]
```

**Examples**:

1. Run a SYN flood test:
   ```bash
   sudo python3 deauth.py 192.168.1.100 -a syn-flood
   ```

2. Custom UDP test:
   ```bash
   sudo python3 deauth.py 192.168.1.100 -t udp -p 53 -r 500 -d 30 -s 128
   ```

3. ICMP ping flood:
   ```bash
   sudo python3 deauth.py 192.168.1.100 -t icmp -r 200 -d 20
   ```

### Command-Line Options

| Option        | Description                              | Default Value |
|---------------|------------------------------------------|---------------|
| `-p`, `--port` | Target port number                      | Protocol default |
| `-t`, `--protocol` | Protocol (tcp, udp, icmp, raw)       | tcp           |
| `-d`, `--duration` | Test duration in seconds              | 10            |
| `-r`, `--rate`    | Packets per second                    | 100           |
| `-n`, `--threads` | Number of threads                     | 3             |
| `-s`, `--size`    | Payload size in bytes                 | 64            |
| `-a`, `--advanced` | Predefined test scenario              | None          |

## Predefined Test Scenarios

1. **SYN Flood**: TCP connection flood (half-open)
2. **UDP Flood**: High-volume UDP traffic
3. **ICMP Flood**: Ping flood
4. **HTTP Load Test**: Web server stress test
5. **DNS Stress Test**: DNS server evaluation

## Best Practices

1. **Test Responsibly**: Only test networks you own or have permission to test
2. **Start Small**: Begin with low packet rates and increase gradually
3. **Monitor Systems**: Watch both target and source system resources
4. **Use in Controlled Environments**: Avoid production networks without approval
5. **Consider Network Impact**: Tests may affect other devices on the same network

## Legal Disclaimer

This tool is intended for legitimate network testing and educational purposes only. Unauthorized use against networks you don't own or have explicit permission to test may violate local laws and regulations. The developers assume no liability for misuse of this software.

## License

MIT License - See LICENSE file for details

## Support

For issues or feature requests, please open an issue on our GitHub repository.
