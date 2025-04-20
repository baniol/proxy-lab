#!/bin/sh

# SOCKS5 Protocol Analyzer Usage Script
# This script demonstrates how to use the protocol_analyzer.py alongside Wireshark

# Function to print colored headers
print_header() {
    echo "\033[1;36m\n=== $1 ===\033[0m\n"
}

# ANSI color codes
BLUE="\033[0;34m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
NC="\033[0m" # No Color

print_header "SOCKS5 Protocol Analyzer Demo"
echo "This script shows how to use the SOCKS5 protocol analyzer with captured packets"

# Check if analyzer is available
if [ ! -f /usr/local/bin/socks5-analyzer.py ]; then
    echo "${YELLOW}Protocol analyzer not found. Make sure Docker is running and containers are up.${NC}"
    exit 1
fi

# Python should already be installed in the container initialization
# We'll just check to confirm it's there
if ! command -v python3 >/dev/null 2>&1; then
    echo "${YELLOW}Python3 not found! The container may not have initialized correctly.${NC}"
    exit 1
fi

print_header "Example 1: Analyzing Client Greeting"
echo "${BLUE}A typical SOCKS5 client greeting message:${NC}"
echo "- Version: 5 (SOCKS5)"
echo "- Number of auth methods: 2"
echo "- Auth methods: 0 (No Auth), 2 (Username/Password)"
echo ""
echo "${GREEN}Running analyzer:${NC}"
python3 /usr/local/bin/socks5-analyzer.py client_greeting --hex "05020002"

print_header "Example 2: Analyzing Server Authentication Choice"
echo "${BLUE}A typical SOCKS5 server auth choice message:${NC}"
echo "- Version: 5 (SOCKS5)"
echo "- Selected method: 2 (Username/Password)"
echo ""
echo "${GREEN}Running analyzer:${NC}"
python3 /usr/local/bin/socks5-analyzer.py server_choice --hex "0502"

print_header "Example 3: Analyzing Client Connection Request"
echo "${BLUE}A SOCKS5 client connection request:${NC}"
echo "- Version: 5 (SOCKS5)"
echo "- Command: 1 (CONNECT)"
echo "- Reserved: 0"
echo "- Address type: 3 (Domain name)"
echo "- Domain length: 9 (web-server)"
echo "- Domain: web-server"
echo "- Port: 80"
echo ""
echo "${GREEN}Running analyzer:${NC}"
python3 /usr/local/bin/socks5-analyzer.py client_request --hex "0501000309776562"$"-736572766572"$"005000"

print_header "Example 4: Analyzing Server Response"
echo "${BLUE}A SOCKS5 server response:${NC}"
echo "- Version: 5 (SOCKS5)"
echo "- Reply: 0 (Success)"
echo "- Reserved: 0"
echo "- Address type: 1 (IPv4)"
echo "- Server bound address: 172.17.0.4"
echo "- Server bound port: 80"
echo ""
echo "${GREEN}Running analyzer:${NC}"
python3 /usr/local/bin/socks5-analyzer.py server_response --hex "05000001ac110004005000"

print_header "Integration with Wireshark"
echo "To use this analyzer with Wireshark captures:"
echo ""
echo "1. Capture SOCKS5 traffic using Wireshark (http://localhost:3000)"
echo "2. Find a SOCKS5 packet you want to analyze"
echo "3. Right-click on the packet -> Copy -> Bytes (Hex Stream)"
echo "4. Use the copied hex data with this analyzer tool"

echo ""
echo "Example command:"
echo "${YELLOW}python3 /usr/local/bin/socks5-analyzer.py client_greeting --hex \"<paste-hex-here>\"${NC}"
echo ""
echo "This allows you to get detailed field-by-field explanations of any SOCKS5 packet"
echo "from your Wireshark captures."

print_header "Analyzing a Live Connection"
echo "Now making a live connection to generate real SOCKS5 traffic..."
echo "You can observe this in Wireshark and then analyze the packets"

# Variables for the connection
SOCKS_SERVER="socks5-server"
SOCKS_PORT="1080"
SOCKS_USER="socksuser"
SOCKS_PASS="sockspass"
TARGET_HOST="web-server"

# Install curl if needed
if ! command -v curl >/dev/null 2>&1; then
    echo "${YELLOW}curl not installed. Installing...${NC}"
    apk add --no-cache curl
fi

# Make a simple request through the SOCKS proxy
echo "${GREEN}Making a request through SOCKS5...${NC}"
curl --socks5 $SOCKS_SERVER:$SOCKS_PORT -U $SOCKS_USER:$SOCKS_PASS -s http://$TARGET_HOST > /dev/null

echo ""
echo "${YELLOW}Traffic generated! Now you can:${NC}"
echo "1. Check Wireshark at http://localhost:3000"
echo "2. Filter for 'socks' in the display filter"
echo "3. Find interesting SOCKS5 packets to analyze"
echo "4. Copy their hex data and use with this tool"

print_header "Happy Protocol Analysis!" 