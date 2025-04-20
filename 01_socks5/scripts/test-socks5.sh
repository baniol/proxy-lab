#!/bin/sh

# SOCKS5 Protocol Testing Script
# This script demonstrates and inspects SOCKS5 protocol operations

echo "==== SOCKS5 Protocol Inspection Tool ===="
echo ""

# Install necessary tools
apk update
apk add --no-cache curl openssh-client socat netcat-openbsd tcpdump python3 wget

# Variables
SOCKS_SERVER="socks5-server"
SOCKS_PORT="1080"
SOCKS_USER="socksuser"
SOCKS_PASS="sockspass"
TARGET_HOST="web-server"
TARGET_PORT="80"

# Function to print colored output
print_header() {
    echo "\033[1;36m\n=== $1 ===\033[0m\n"
}

# Function to print hex and ASCII representation of data
print_hex_ascii() {
    hexdump -C
}

print_header "Testing SOCKS5 Server Availability"
nc -zv $SOCKS_SERVER $SOCKS_PORT

print_header "SOCKS5 Protocol Handshake Analysis"
echo "STEP 1: Client sends greeting message with supported auth methods"
echo "For raw analysis, the client sends:"
echo "- Version: 0x05 (SOCKS5)"
echo "- Number of auth methods: 0x02"
echo "- Auth methods: 0x00 (No auth), 0x02 (Username/password)"
echo ""

print_header "Manual SOCKS5 Connection - No Authentication"
echo "Sending SOCKS5 init packet (no auth)..."
(printf "\x05\x01\x00" | nc $SOCKS_SERVER $SOCKS_PORT | print_hex_ascii) || echo "Failed to connect"

print_header "Manual SOCKS5 Connection - With Authentication"
echo "Sending SOCKS5 init packet with auth method..."
(printf "\x05\x02\x00\x02" | nc $SOCKS_SERVER $SOCKS_PORT | print_hex_ascii) || echo "Failed to connect"

print_header "Making a real connection to target server via SOCKS5"
# Note: This uses curl's SOCKS5 support to make the connection
curl --socks5 $SOCKS_SERVER:$SOCKS_PORT --socks5-hostname $SOCKS_SERVER:$SOCKS_PORT -U $SOCKS_USER:$SOCKS_PASS -v http://$TARGET_HOST 2>&1 | grep -E '(SOCKS|proxy)'

print_header "Testing TCP/IP Connection Through SOCKS5 with socat"
socat - SOCKS5:$TARGET_HOST:$TARGET_PORT,socksport=$SOCKS_PORT,proxyauth=$SOCKS_USER:$SOCKS_PASS <<< "GET / HTTP/1.0\r\n\r\n" | head -20

print_header "Low-level Protocol Dissection"
echo "A SOCKS5 initial handshake consists of:"
echo "1. Client greeting: \x05\x01\x00 (version, # auth methods, no auth)"
echo "   or with auth:    \x05\x02\x00\x02 (version, # auth methods, no auth, user/pass)"
echo "2. Server response: \x05\x00 (version, chosen auth method)"
echo "   or:              \x05\x02 (version, user/pass auth required)"
echo ""
echo "3. If auth required, client sends: \x01{username}{password}"
echo "4. Server auth response: \x01\x00 (version, success)"
echo ""
echo "5. Client connection request:"
echo "   \x05\x01\x00\x01{IP}{PORT} (for IPv4)"
echo "   or \x05\x01\x00\x03{len}{domain}{port} (for domain names)"
echo ""
echo "6. Server connection response:"
echo "   \x05\x00\x00\x01{bound IP}{bound port} (success)"
echo ""
echo "After this exchange, the SOCKS5 tunnel is established"

# Packet capture with tcpdump
print_header "Capturing SOCKS5 traffic with tcpdump (10 packets max)"
timeout 10 tcpdump -nn -X -i any -c 10 port $SOCKS_PORT 2>/dev/null || echo "Could not capture traffic"

print_header "Testing Complete"
echo "For further analysis, you can use the Wireshark container to capture and inspect full protocol details" 