#!/usr/bin/env python3
"""
SOCKS5 Protocol Analyzer
This script breaks down SOCKS5 protocol messages to help understand the protocol structure.
"""

import sys
import socket
import struct
import binascii
import argparse

# SOCKS5 Constants
AUTH_METHODS = {
    0x00: "NO_AUTH",
    0x01: "GSSAPI",
    0x02: "USERNAME_PASSWORD",
    0xFF: "NO_ACCEPTABLE"
}

COMMANDS = {
    0x01: "CONNECT",
    0x02: "BIND",
    0x03: "UDP_ASSOCIATE"
}

ADDRESS_TYPES = {
    0x01: "IPV4",
    0x03: "DOMAIN_NAME",
    0x04: "IPV6"
}

REPLIES = {
    0x00: "SUCCEEDED",
    0x01: "GENERAL_FAILURE",
    0x02: "CONNECTION_NOT_ALLOWED",
    0x03: "NETWORK_UNREACHABLE",
    0x04: "HOST_UNREACHABLE",
    0x05: "CONNECTION_REFUSED",
    0x06: "TTL_EXPIRED",
    0x07: "COMMAND_NOT_SUPPORTED",
    0x08: "ADDRESS_TYPE_NOT_SUPPORTED"
}

def print_hex(data):
    """Print data in hexadecimal and ASCII format"""
    hex_data = binascii.hexlify(data).decode('ascii')
    print(f"Hex: {hex_data}")
    
    # Print formatted hex and ASCII view
    for i in range(0, len(data), 16):
        chunk = data[i:i+16]
        hex_line = ' '.join(f'{b:02x}' for b in chunk)
        ascii_line = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
        
        # Pad hex line
        hex_line = hex_line.ljust(47)
        print(f"{hex_line}  |  {ascii_line}")

def analyze_client_greeting(data):
    """Analyze SOCKS5 client greeting message"""
    if len(data) < 3:
        print("Invalid client greeting (too short)")
        return
    
    version = data[0]
    nmethods = data[1]
    methods = data[2:2+nmethods]
    
    print("SOCKS5 Client Greeting:")
    print(f"Version: {version} {'(SOCKS5)' if version == 5 else '(INVALID)'}")
    print(f"Number of methods: {nmethods}")
    print("Authentication methods:")
    
    for method in methods:
        method_name = AUTH_METHODS.get(method, "UNKNOWN")
        print(f"  - 0x{method:02x}: {method_name}")

def analyze_server_choice(data):
    """Analyze SOCKS5 server authentication choice"""
    if len(data) < 2:
        print("Invalid server choice (too short)")
        return
    
    version = data[0]
    method = data[1]
    
    print("SOCKS5 Server Authentication Choice:")
    print(f"Version: {version} {'(SOCKS5)' if version == 5 else '(INVALID)'}")
    
    method_name = AUTH_METHODS.get(method, "UNKNOWN")
    print(f"Chosen method: 0x{method:02x} ({method_name})")

def analyze_client_request(data):
    """Analyze SOCKS5 client connection request"""
    if len(data) < 4:
        print("Invalid client request (too short)")
        return
    
    version = data[0]
    cmd = data[1]
    rsv = data[2]  # Reserved, should be 0
    atyp = data[3]
    
    print("SOCKS5 Client Request:")
    print(f"Version: {version} {'(SOCKS5)' if version == 5 else '(INVALID)'}")
    
    cmd_name = COMMANDS.get(cmd, "UNKNOWN")
    print(f"Command: 0x{cmd:02x} ({cmd_name})")
    print(f"Reserved: {rsv} (should be 0)")
    
    atyp_name = ADDRESS_TYPES.get(atyp, "UNKNOWN")
    print(f"Address type: 0x{atyp:02x} ({atyp_name})")
    
    offset = 4
    dst_addr = ""
    
    # Parse address based on type
    if atyp == 0x01:  # IPv4
        if len(data) < offset + 4:
            print("Invalid request (IPv4 address truncated)")
            return
        ip_bytes = data[offset:offset+4]
        dst_addr = socket.inet_ntop(socket.AF_INET, ip_bytes)
        offset += 4
    elif atyp == 0x03:  # Domain name
        if len(data) < offset + 1:
            print("Invalid request (domain name length missing)")
            return
        domain_len = data[offset]
        offset += 1
        if len(data) < offset + domain_len:
            print("Invalid request (domain name truncated)")
            return
        dst_addr = data[offset:offset+domain_len].decode('utf-8', errors='replace')
        offset += domain_len
    elif atyp == 0x04:  # IPv6
        if len(data) < offset + 16:
            print("Invalid request (IPv6 address truncated)")
            return
        ip_bytes = data[offset:offset+16]
        dst_addr = socket.inet_ntop(socket.AF_INET6, ip_bytes)
        offset += 16
    
    if len(data) < offset + 2:
        print("Invalid request (port missing)")
        return
    
    dst_port = struct.unpack('!H', data[offset:offset+2])[0]
    
    print(f"Destination address: {dst_addr}")
    print(f"Destination port: {dst_port}")

def analyze_server_response(data):
    """Analyze SOCKS5 server response"""
    if len(data) < 4:
        print("Invalid server response (too short)")
        return
    
    version = data[0]
    rep = data[1]
    rsv = data[2]  # Reserved, should be 0
    atyp = data[3]
    
    print("SOCKS5 Server Response:")
    print(f"Version: {version} {'(SOCKS5)' if version == 5 else '(INVALID)'}")
    
    rep_name = REPLIES.get(rep, "UNKNOWN")
    print(f"Reply: 0x{rep:02x} ({rep_name})")
    print(f"Reserved: {rsv} (should be 0)")
    
    atyp_name = ADDRESS_TYPES.get(atyp, "UNKNOWN")
    print(f"Address type: 0x{atyp:02x} ({atyp_name})")

def analyze_packet(packet_type, data):
    """Analyze a SOCKS5 packet based on its type"""
    print(f"\nAnalyzing {packet_type}...")
    print_hex(data)
    print()
    
    if packet_type == "client_greeting":
        analyze_client_greeting(data)
    elif packet_type == "server_choice":
        analyze_server_choice(data)
    elif packet_type == "client_request":
        analyze_client_request(data)
    elif packet_type == "server_response":
        analyze_server_response(data)
    else:
        print(f"Unknown packet type: {packet_type}")

def main():
    parser = argparse.ArgumentParser(description="SOCKS5 Protocol Analyzer")
    parser.add_argument("packet_type", choices=[
        "client_greeting", "server_choice", 
        "client_request", "server_response"
    ], help="Type of SOCKS5 packet to analyze")
    parser.add_argument("--hex", type=str, help="Hex string of the packet")
    
    args = parser.parse_args()
    
    if args.hex:
        try:
            data = binascii.unhexlify(args.hex)
            analyze_packet(args.packet_type, data)
        except binascii.Error:
            print("Invalid hex string")
            sys.exit(1)
    else:
        print("Please provide the --hex argument")
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main() 
"""
SOCKS5 Protocol Analyzer
This script breaks down SOCKS5 protocol messages to help understand the protocol structure.
"""

import sys
import socket
import struct
import binascii
import argparse
from enum import Enum

# SOCKS5 Constants
class Auth(Enum):
    NO_AUTH = 0x00
    GSSAPI = 0x01
    USERNAME_PASSWORD = 0x02
    NO_ACCEPTABLE = 0xFF

class Command(Enum):
    CONNECT = 0x01
    BIND = 0x02
    UDP_ASSOCIATE = 0x03

class AddressType(Enum):
    IPV4 = 0x01
    DOMAIN_NAME = 0x03
    IPV6 = 0x04

class Reply(Enum):
    SUCCEEDED = 0x00
    GENERAL_FAILURE = 0x01
    CONNECTION_NOT_ALLOWED = 0x02
    NETWORK_UNREACHABLE = 0x03
    HOST_UNREACHABLE = 0x04
    CONNECTION_REFUSED = 0x05
    TTL_EXPIRED = 0x06
    COMMAND_NOT_SUPPORTED = 0x07
    ADDRESS_TYPE_NOT_SUPPORTED = 0x08

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_hex(data):
    """Print data in hexadecimal and ASCII format"""
    hex_data = binascii.hexlify(data).decode('ascii')
    print(f"{Colors.BLUE}Hex: {hex_data}{Colors.ENDC}")
    
    # Print formatted hex and ASCII view
    hex_lines = []
    ascii_lines = []
    
    for i in range(0, len(data), 16):
        chunk = data[i:i+16]
        hex_line = ' '.join(f'{b:02x}' for b in chunk)
        ascii_line = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
        
        # Pad hex line
        hex_line = hex_line.ljust(47)
        
        hex_lines.append(hex_line)
        ascii_lines.append(ascii_line)
    
    # Print combined view
    for i in range(len(hex_lines)):
        print(f"{hex_lines[i]}  |  {ascii_lines[i]}")

def analyze_client_greeting(data):
    """Analyze SOCKS5 client greeting message"""
    if len(data) < 3:
        print(f"{Colors.FAIL}Invalid client greeting (too short){Colors.ENDC}")
        return
    
    version = data[0]
    nmethods = data[1]
    methods = data[2:2+nmethods]
    
    print(f"{Colors.HEADER}SOCKS5 Client Greeting:{Colors.ENDC}")
    print(f"Version: {version} {'(SOCKS5)' if version == 5 else '(INVALID)'}")
    print(f"Number of methods: {nmethods}")
    print("Authentication methods:")
    
    for method in methods:
        method_name = "UNKNOWN"
        try:
            method_name = Auth(method).name
        except ValueError:
            pass
        print(f"  - 0x{method:02x}: {method_name}")

def analyze_server_choice(data):
    """Analyze SOCKS5 server authentication choice"""
    if len(data) < 2:
        print(f"{Colors.FAIL}Invalid server choice (too short){Colors.ENDC}")
        return
    
    version = data[0]
    method = data[1]
    
    print(f"{Colors.HEADER}SOCKS5 Server Authentication Choice:{Colors.ENDC}")
    print(f"Version: {version} {'(SOCKS5)' if version == 5 else '(INVALID)'}")
    
    method_name = "UNKNOWN"
    try:
        method_name = Auth(method).name
    except ValueError:
        pass
    print(f"Chosen method: 0x{method:02x} ({method_name})")

def analyze_username_password_auth(data):
    """Analyze SOCKS5 username/password authentication"""
    if len(data) < 3:
        print(f"{Colors.FAIL}Invalid auth request (too short){Colors.ENDC}")
        return
    
    version = data[0]  # Should be 1 for username/password auth
    ulen = data[1]
    
    if len(data) < 2 + ulen + 1:
        print(f"{Colors.FAIL}Invalid auth request (username truncated){Colors.ENDC}")
        return
    
    username = data[2:2+ulen].decode('utf-8', errors='replace')
    plen = data[2+ulen]
    
    if len(data) < 2 + ulen + 1 + plen:
        print(f"{Colors.FAIL}Invalid auth request (password truncated){Colors.ENDC}")
        return
    
    # In a real situation, we would never print passwords, this is for educational purposes only
    password = data[2+ulen+1:2+ulen+1+plen].decode('utf-8', errors='replace')
    
    print(f"{Colors.HEADER}SOCKS5 Username/Password Authentication:{Colors.ENDC}")
    print(f"Auth version: {version}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)} (redacted)")

def analyze_auth_response(data):
    """Analyze SOCKS5 authentication response"""
    if len(data) < 2:
        print(f"{Colors.FAIL}Invalid auth response (too short){Colors.ENDC}")
        return
    
    version = data[0]
    status = data[1]
    
    print(f"{Colors.HEADER}SOCKS5 Authentication Response:{Colors.ENDC}")
    print(f"Auth version: {version}")
    print(f"Status: {status} ({Colors.GREEN}SUCCESS{Colors.ENDC} if 0, {Colors.FAIL}FAILURE{Colors.ENDC} otherwise)")

def analyze_client_request(data):
    """Analyze SOCKS5 client connection request"""
    if len(data) < 4:
        print(f"{Colors.FAIL}Invalid client request (too short){Colors.ENDC}")
        return
    
    version = data[0]
    cmd = data[1]
    rsv = data[2]  # Reserved, should be 0
    atyp = data[3]
    
    print(f"{Colors.HEADER}SOCKS5 Client Request:{Colors.ENDC}")
    print(f"Version: {version} {'(SOCKS5)' if version == 5 else '(INVALID)'}")
    
    cmd_name = "UNKNOWN"
    try:
        cmd_name = Command(cmd).name
    except ValueError:
        pass
    print(f"Command: 0x{cmd:02x} ({cmd_name})")
    print(f"Reserved: {rsv} (should be 0)")
    
    atyp_name = "UNKNOWN"
    try:
        atyp_name = AddressType(atyp).name
    except ValueError:
        pass
    print(f"Address type: 0x{atyp:02x} ({atyp_name})")
    
    offset = 4
    dst_addr = ""
    
    # Parse address based on type
    if atyp == AddressType.IPV4.value:
        if len(data) < offset + 4:
            print(f"{Colors.FAIL}Invalid request (IPv4 address truncated){Colors.ENDC}")
            return
        ip_bytes = data[offset:offset+4]
        dst_addr = socket.inet_ntop(socket.AF_INET, ip_bytes)
        offset += 4
    elif atyp == AddressType.DOMAIN_NAME.value:
        if len(data) < offset + 1:
            print(f"{Colors.FAIL}Invalid request (domain name length missing){Colors.ENDC}")
            return
        domain_len = data[offset]
        offset += 1
        if len(data) < offset + domain_len:
            print(f"{Colors.FAIL}Invalid request (domain name truncated){Colors.ENDC}")
            return
        dst_addr = data[offset:offset+domain_len].decode('utf-8', errors='replace')
        offset += domain_len
    elif atyp == AddressType.IPV6.value:
        if len(data) < offset + 16:
            print(f"{Colors.FAIL}Invalid request (IPv6 address truncated){Colors.ENDC}")
            return
        ip_bytes = data[offset:offset+16]
        dst_addr = socket.inet_ntop(socket.AF_INET6, ip_bytes)
        offset += 16
    
    if len(data) < offset + 2:
        print(f"{Colors.FAIL}Invalid request (port missing){Colors.ENDC}")
        return
    
    dst_port = struct.unpack('!H', data[offset:offset+2])[0]
    
    print(f"Destination address: {dst_addr}")
    print(f"Destination port: {dst_port}")

def analyze_server_response(data):
    """Analyze SOCKS5 server response"""
    if len(data) < 4:
        print(f"{Colors.FAIL}Invalid server response (too short){Colors.ENDC}")
        return
    
    version = data[0]
    rep = data[1]
    rsv = data[2]  # Reserved, should be 0
    atyp = data[3]
    
    print(f"{Colors.HEADER}SOCKS5 Server Response:{Colors.ENDC}")
    print(f"Version: {version} {'(SOCKS5)' if version == 5 else '(INVALID)'}")
    
    rep_name = "UNKNOWN"
    try:
        rep_name = Reply(rep).name
    except ValueError:
        pass
    print(f"Reply: 0x{rep:02x} ({rep_name})")
    print(f"Reserved: {rsv} (should be 0)")
    
    atyp_name = "UNKNOWN"
    try:
        atyp_name = AddressType(atyp).name
    except ValueError:
        pass
    print(f"Address type: 0x{atyp:02x} ({atyp_name})")
    
    offset = 4
    bnd_addr = ""
    
    # Parse address based on type
    if atyp == AddressType.IPV4.value:
        if len(data) < offset + 4:
            print(f"{Colors.FAIL}Invalid response (IPv4 address truncated){Colors.ENDC}")
            return
        ip_bytes = data[offset:offset+4]
        bnd_addr = socket.inet_ntop(socket.AF_INET, ip_bytes)
        offset += 4
    elif atyp == AddressType.DOMAIN_NAME.value:
        if len(data) < offset + 1:
            print(f"{Colors.FAIL}Invalid response (domain name length missing){Colors.ENDC}")
            return
        domain_len = data[offset]
        offset += 1
        if len(data) < offset + domain_len:
            print(f"{Colors.FAIL}Invalid response (domain name truncated){Colors.ENDC}")
            return
        bnd_addr = data[offset:offset+domain_len].decode('utf-8', errors='replace')
        offset += domain_len
    elif atyp == AddressType.IPV6.value:
        if len(data) < offset + 16:
            print(f"{Colors.FAIL}Invalid response (IPv6 address truncated){Colors.ENDC}")
            return
        ip_bytes = data[offset:offset+16]
        bnd_addr = socket.inet_ntop(socket.AF_INET6, ip_bytes)
        offset += 16
    
    if len(data) < offset + 2:
        print(f"{Colors.FAIL}Invalid response (port missing){Colors.ENDC}")
        return
    
    bnd_port = struct.unpack('!H', data[offset:offset+2])[0]
    
    print(f"Bound address: {bnd_addr}")
    print(f"Bound port: {bnd_port}")

def analyze_packet(packet_type, data):
    """Analyze a SOCKS5 packet based on its type"""
    print(f"\n{Colors.BOLD}Analyzing {packet_type}...{Colors.ENDC}")
    print_hex(data)
    print()
    
    if packet_type == "client_greeting":
        analyze_client_greeting(data)
    elif packet_type == "server_choice":
        analyze_server_choice(data)
    elif packet_type == "username_password_auth":
        analyze_username_password_auth(data)
    elif packet_type == "auth_response":
        analyze_auth_response(data)
    elif packet_type == "client_request":
        analyze_client_request(data)
    elif packet_type == "server_response":
        analyze_server_response(data)
    else:
        print(f"{Colors.FAIL}Unknown packet type: {packet_type}{Colors.ENDC}")

def main():
    parser = argparse.ArgumentParser(description="SOCKS5 Protocol Analyzer")
    parser.add_argument("packet_type", choices=[
        "client_greeting", "server_choice", 
        "username_password_auth", "auth_response",
        "client_request", "server_response"
    ], help="Type of SOCKS5 packet to analyze")
    parser.add_argument("--hex", type=str, help="Hex string of the packet")
    parser.add_argument("--file", type=str, help="File containing the raw packet")
    
    args = parser.parse_args()
    
    if args.hex:
        try:
            data = binascii.unhexlify(args.hex)
            analyze_packet(args.packet_type, data)
        except binascii.Error:
            print(f"{Colors.FAIL}Invalid hex string{Colors.ENDC}")
            sys.exit(1)
    elif args.file:
        try:
            with open(args.file, 'rb') as f:
                data = f.read()
                analyze_packet(args.packet_type, data)
        except FileNotFoundError:
            print(f"{Colors.FAIL}File not found: {args.file}{Colors.ENDC}")
            sys.exit(1)
    else:
        print(f"{Colors.WARNING}Please provide either --hex or --file argument{Colors.ENDC}")
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main() 
 