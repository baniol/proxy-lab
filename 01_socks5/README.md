# SOCKS5 Protocol Lab

## Table of Contents
- [Introduction to SOCKS5](#introduction-to-socks5)
- [Lab Setup](#lab-setup)
- [Lab Architecture](#lab-architecture)
- [How SOCKS5 Works](#how-socks5-works)
- [Using the Lab](#using-the-lab)
- [Analysis Tools](#analysis-tools)
- [Protocol Details](#protocol-details)
- [Security and Encryption](#security-and-encryption)
- [SSH Dynamic Port Forwarding](#ssh-dynamic-port-forwarding)
- [Use Cases and Applications](#use-cases-and-applications)

## Introduction to SOCKS5

SOCKS5 (Socket Secure version 5) is a versatile internet protocol that establishes a TCP connection to another server on behalf of a client, then routes all traffic between them. As the successor to SOCKS4, it provides a framework for clients behind a firewall to securely connect to servers outside of their network perimeter.

### What is SOCKS5?

SOCKS5 is an **internet protocol** that exchanges network packets between a client and server through a proxy server. Unlike application-specific proxies, SOCKS operates at **Layer 5 (Session Layer)** of the OSI model, making it protocol-agnostic.

Key characteristics:
- Established in RFC 1928
- Supports both TCP and UDP protocols
- Provides authentication mechanisms
- Supports IPv6 and domain name resolution
- Works with any application protocol (HTTP, FTP, SMTP, etc.)

### SOCKS5 vs. Other Proxy Types

#### Compared to HTTP Proxies
- **Protocol Support**: SOCKS5 works with any protocol while HTTP proxies are limited to HTTP/HTTPS
- **Application Layer**: HTTP proxies operate at Layer 7 (Application) while SOCKS5 operates at Layer 5 (Session)
- **Traffic Interpretation**: HTTP proxies understand and can modify HTTP traffic; SOCKS5 simply forwards packets without interpreting them
- **Performance**: SOCKS5 generally has less overhead since it doesn't examine packet contents

#### Compared to VPNs
- **Encryption**: SOCKS5 doesn't encrypt traffic by default (though it can be tunneled through SSH or other encrypted channels), while VPNs provide encryption
- **Scope**: SOCKS5 is application-specific configuration; VPNs typically route all system traffic
- **Overhead**: SOCKS5 has lower overhead due to lack of built-in encryption
- **Network Layer**: VPNs operate at Layer 3 (Network), affecting the entire networking stack

#### Compared to SOCKS4
- **Authentication**: SOCKS5 supports multiple authentication methods; SOCKS4 has none
- **Protocol Support**: SOCKS5 supports both TCP and UDP; SOCKS4 only supports TCP
- **Addressing**: SOCKS5 supports IPv6 and domain name resolution; SOCKS4 only supports IPv4
- **Flexibility**: SOCKS5 offers a negotiation phase for features; SOCKS4 has a fixed feature set

### Limitations

- No encryption by default (data is transmitted in plaintext)
- Requires application-level support or configuration
- No content filtering or caching capabilities
- Authentication methods can be weak without additional security layers

## Lab Setup

This lab provides a controlled environment to explore and understand the SOCKS5 protocol through practical experimentation.

### Quick Start
```bash
docker-compose up -d
```

### Components
- SOCKS5 proxy server (port 1080, auth: socksuser/sockspass)
- Client container for testing
- Wireshark for packet analysis
- Target web server

## Lab Architecture

This lab creates a controlled environment to examine SOCKS5 protocol operations through four interconnected containers:

### 1. SOCKS5 Proxy Server (`socks5-server`)
- **Image**: `serjs/go-socks5-proxy`
- **Purpose**: Implements the SOCKS5 proxy protocol
- **Configuration**:
  - Listens on port 1080
  - Requires username/password authentication (socksuser/sockspass)
  - Handles client connections and proxies them to target destinations
- **Responsibilities**:
  - Authenticates connecting clients
  - Processes SOCKS5 protocol commands (primarily CONNECT)
  - Establishes connections to requested target servers
  - Relays data between clients and target servers
  - Implements the complete SOCKS5 protocol as described in RFC 1928

### 2. Client Container (`socks-client`)
- **Image**: Alpine Linux
- **Purpose**: Acts as the client that connects through the SOCKS5 proxy
- **Configuration**:
  - Contains testing tools and scripts
  - Connected to same network as the proxy server
  - Has access to test scripts for exploring the protocol
- **Responsibilities**:
  - Initiates SOCKS5 connections to the proxy
  - Sends properly formatted SOCKS5 protocol messages
  - Demonstrates both manual protocol interactions and application-level usage
  - Allows connection to target services through the proxy

### 3. Packet Analyzer (`socks-analyzer`)
- **Image**: `linuxserver/wireshark`
- **Purpose**: Provides real-time traffic inspection and protocol analysis
- **Configuration**:
  - Shares network namespace with the SOCKS5 server
  - Web interface accessible at http://localhost:3000
  - Has necessary capabilities for packet capture
- **Responsibilities**:
  - Captures all network traffic passing through the SOCKS5 server
  - Provides tools to inspect and analyze protocol messages
  - Visualizes the complete communication flow
  - Helps understand protocol structure and timing
  - Allows export of packet captures for documentation

### 4. Target Web Server (`web-server`)
- **Image**: Nginx Alpine
- **Purpose**: Serves as a destination server for proxied connections
- **Configuration**:
  - Serves a simple HTTP site
  - Connected to the same network
  - Accessible via port 8080 from the host
- **Responsibilities**:
  - Provides a real service to connect to through the proxy
  - Helps demonstrate complete connection flow
  - Serves a web page confirming successful proxy connection

## How SOCKS5 Works

### General Protocol Flow

1. **Connection Establishment**: Client initiates connection to the SOCKS5 server
2. **Authentication**: Client authenticates using one of the supported methods
3. **Request Processing**: Client sends connection request with destination address
4. **Proxying**: SOCKS server establishes connection to destination, then relays data between client and destination

### Detailed Protocol Flow in This Lab

The lab demonstrates the complete SOCKS5 protocol flow:

1. **Connection Initiation**:
   - The client (`socks-client`) establishes a TCP connection to the SOCKS5 server on port 1080
   - This is a standard TCP handshake (SYN, SYN-ACK, ACK)

2. **Method Negotiation**:
   - Client sends available authentication methods (`05 02 00 02`)
   - Server responds with chosen method (`05 02` for username/password)

3. **Authentication**:
   - Client sends credentials in the format required by RFC 1929
   - Server verifies credentials and responds with success/failure

4. **Connection Request**:
   - Client sends a CONNECT command with the target address (web-server)
   - The format follows RFC 1928 with address type, destination address, and port

5. **Proxy Connection**:
   - SOCKS5 server establishes a connection to the target server
   - Server responds to client indicating connection success

6. **Data Transfer Phase**:
   - After successful handshake, the SOCKS5 server becomes a bidirectional relay
   - **Important**: Application data (like HTTP) is NOT encapsulated within SOCKS5
   - Once the SOCKS5 handshake completes, the SOCKS5 protocol itself disappears
   - The TCP connection becomes a "clean pipe" that passes raw application data
   - HTTP requests/responses flow through this pipe without any SOCKS5 headers or wrappers
   - The client sends regular HTTP directly, the proxy forwards it unchanged
   - From the target server's perspective, it's receiving standard HTTP requests
   - This contrasts with VPN protocols that encapsulate all traffic with additional headers

   Visual representation:
   ```
   Before handshake:
   [TCP][SOCKS5 Protocol Messages]

   After handshake:
   [TCP][Raw HTTP Data] → No SOCKS5 encapsulation
   ```

### Protocol Position in the Network Stack

SOCKS5 operates at the Session Layer (Layer 5) of the OSI model, but in practical implementation, it's encapsulated within the following protocol layers:

```
┌─────────────────────────────┐
│ Application Data            │ Layer 7 - Application (e.g., HTTP)
├─────────────────────────────┤
│ SOCKS5 Protocol             │ Layer 5 - Session
├─────────────────────────────┤
│ TCP                         │ Layer 4 - Transport
├─────────────────────────────┤
│ IP (v4 or v6)               │ Layer 3 - Network
├─────────────────────────────┤
│ Ethernet Header             │ Layer 2 - Data Link
├─────────────────────────────┤
│ Ethernet Preamble + SFD     │ Layer 1 - Physical
└─────────────────────────────┘
```

### TCP Connection Handling

SOCKS5 is a connection-oriented protocol that leverages persistent TCP connections:

1. **Persistent TCP Connection**:
   - Once established, the TCP connection between client and SOCKS5 server remains open
   - This single connection is used for the entire session, including handshake and data transfer
   - The connection persists until explicitly closed by either the client or server

2. **Connection Flow**:
   - Client establishes TCP connection to SOCKS5 server
   - After successful handshake, the SOCKS5 server establishes a second TCP connection to the destination
   - SOCKS5 server maintains both connections simultaneously:
     ```
     [Client] <--- TCP Connection #1 ---> [SOCKS5 Server] <--- TCP Connection #2 ---> [Destination]
     ```
   - The server relays data between these two TCP connections without modifying the payload

3. **Bidirectional Data Transfer**:
   - The established TCP channels allow for continuous bidirectional communication
   - The SOCKS5 server forwards data in both directions:
     - Client to destination (requests)
     - Destination to client (responses)
   - As a circuit-level proxy, it maintains state about the connection but doesn't inspect application data

4. **Connection Termination**:
   - If the client closes its TCP connection to the SOCKS5 server, the server closes its connection to the destination
   - If the destination server closes its connection, the SOCKS5 server closes its connection to the client
   - TCP's standard teardown mechanism (FIN, FIN-ACK sequences) can be observed in both cases

This persistent connection model is what makes SOCKS5 efficient for ongoing data transfers and distinguishes it from connectionless protocols. In the lab, you can observe this behavior in Wireshark by following TCP streams - you'll see that after the initial SOCKS5 handshake, the same TCP connection continues to carry all application data throughout the session.

## Using the Lab

### Basic Tests
```bash
# Start the lab environment
docker-compose up -d

# Test proxy connection
docker exec -it socks-client sh
curl --socks5 socks5-server:1080 -U socksuser:sockspass http://web-server

# Analyze with Wireshark
# Visit http://localhost:3000
```

### Running the Test Script
```bash
# Connect to the client container
docker exec -it socks-client sh

# Run the test script
sh /scripts/test-socks5.sh
```

When you run the test script (`/scripts/test-socks5.sh`), it:

1. Tests basic connectivity to the SOCKS5 server
2. Sends raw SOCKS5 protocol bytes using netcat to demonstrate handshake
3. Uses curl with SOCKS5 support to make a complete connection
4. Shows the full protocol exchange with verbose output

This allows you to see both the low-level protocol details and practical application usage.

## Analysis Tools

### Wireshark Analysis Guide

The lab includes browser-based Wireshark that can be accessed at http://localhost:3000. Here's how to analyze SOCKS5 protocol in detail:

#### Useful Filters

1. **Basic SOCKS5 traffic filter**:
   ```
   tcp.port == 1080
   ```

2. **SOCKS5 connection establishment**:
   ```
   tcp.port == 1080 and tcp.flags.syn == 1
   ```

3. **Follow complete SOCKS5 conversations**:
   - Right-click a packet → "Follow" → "TCP Stream"

#### What to Look For

**SOCKS5 Protocol Handshake**

1. **Client Greeting** (First packet from client to server):
   - Look for bytes: `05 01 00` or `05 02 00 02`
   - `05` = SOCKS5 version
   - Next byte = number of authentication methods
   - Following bytes = authentication methods (00=No auth, 02=Username/password)

2. **Server Authentication Choice** (First response from server):
   - Look for bytes: `05 00` or `05 02`
   - `05` = SOCKS5 version
   - Second byte = chosen authentication method
    
3. **Authentication Exchange** (if method 02 was chosen):
   - Client sends: `01` (auth version) + username + password
   - Server replies: `01 00` (success) or `01 01` (failure)

4. **Connection Request** (Client requesting target connection):
   - Format: `05 01 00 03 [len] [hostname] [port]`
   - `05` = SOCKS5 version
   - `01` = CONNECT command
   - `00` = Reserved byte
   - `03` = Domain name address type (01=IPv4, 04=IPv6)
   - `[len]` = Length of hostname
   - `[hostname]` = Target hostname bytes
   - `[port]` = 2-byte port number (big-endian)

5. **Server Response** (Server confirms connection):
   - Format: `05 00 00 01 [ip] [port]`
   - `05` = SOCKS5 version
   - First `00` = Success code
   - Second `00` = Reserved
   - `01` = IPv4 address type
   - `[ip]` = 4 bytes of IP address
   - `[port]` = 2-byte port number

6. **Data Transfer Phase**:
   - After successful handshake, all subsequent packets carry tunneled application data
   - In our lab, this will be HTTP traffic to the web-server

**Note on Wireshark Display Behavior**:
- In Wireshark, you might still see "SOCKS Protocol" listed for data transfer packets
- This is due to Wireshark's protocol tracking and correlation, not actual encapsulation
- Wireshark associates all packets in the TCP stream with SOCKS5 because:
  1. The connection began with SOCKS5 protocol
  2. The connection is on the SOCKS5 port (1080)
  3. Wireshark tracks TCP state and associates related packets
- When you select "SOCKS Protocol" in these packets, Wireshark highlights the entire data section
- This is misleading - the data is not actually encapsulated in SOCKS5 headers
- If you examine the raw bytes, you'll see pure HTTP data with no SOCKS5 framing

### Protocol Analyzer Tool

This lab includes a specialized SOCKS5 protocol analyzer tool (`protocol_analyzer.py`) that complements Wireshark by providing detailed field-by-field explanations of SOCKS5 protocol messages. While Wireshark offers comprehensive packet capture and visualization, this tool focuses exclusively on SOCKS5 protocol structure.

#### Key Features

- **Detailed Protocol Dissection**: Breaks down each field in SOCKS5 messages
- **Field-by-Field Explanations**: Explains the meaning and purpose of each byte
- **Command-Line Interface**: Easy to use with captured packet data
- **Educational Focus**: Designed to help understand protocol structure

#### Using the Protocol Analyzer

The analyzer is mounted in both the client and analyzer containers and can be accessed at `/usr/local/bin/socks5-analyzer.py`. It accepts hex data representing SOCKS5 protocol messages and provides detailed explanations.

##### Basic Usage:

```bash
# From inside the client container
python3 /usr/local/bin/socks5-analyzer.py <packet_type> --hex <hex_data>
```

Where:
- `<packet_type>` is one of:
  - `client_greeting`: Initial client connection message
  - `server_choice`: Server authentication method selection
  - `client_request`: Client connection request
  - `server_response`: Server connection response
- `<hex_data>` is the hexadecimal representation of the packet

##### Example Usage:

```bash
# Analyze a client greeting packet
python3 /usr/local/bin/socks5-analyzer.py client_greeting --hex "05020002"
```

##### Demonstration Script:

The lab includes a demonstration script to show how the analyzer works:

```bash
# From inside the client container
sh /scripts/use-protocol-analyzer.sh
```

This script:
- Shows examples of analyzing different SOCKS5 packet types
- Demonstrates how to extract packet data from Wireshark
- Makes a live connection to generate real SOCKS5 traffic for analysis
- Provides a workflow for combining Wireshark and the analyzer

#### How to Run the Protocol Analyzer in the Lab:

1. **Start the lab environment** if not already running:
   ```bash
   docker-compose up -d
   ```

2. **Access the client container**:
   ```bash
   docker exec -it socks-client sh
   ```

3. **Run the demonstration script**:
   ```bash
   sh /scripts/use-protocol-analyzer.sh
   ```

4. **To analyze your own captured packets**:
   - Open Wireshark at http://localhost:3000
   - Capture some SOCKS5 traffic (use filter: `tcp.port == 1080`)
   - Find an interesting packet in the handshake
   - Right-click → Copy → Bytes (Hex Stream)
   - In the client container, run:
     ```bash
     python3 /usr/local/bin/socks5-analyzer.py client_greeting --hex "PASTE_HEX_HERE"
     ```
   - Adjust the packet type based on what you're analyzing

5. **Test with different packet types**:
   ```bash
   # Client greeting
   python3 /usr/local/bin/socks5-analyzer.py client_greeting --hex "05020002"
   
   # Server choice
   python3 /usr/local/bin/socks5-analyzer.py server_choice --hex "0502"
   
   # Client request (connecting to web-server)
   python3 /usr/local/bin/socks5-analyzer.py client_request --hex "0501000309776562"$"-736572766572"$"005000"
   
   # Server response (success)
   python3 /usr/local/bin/socks5-analyzer.py server_response --hex "05000001ac110004005000"
   ```

6. **Generate real traffic for analysis**:
   ```bash
   # Install curl if needed
   apk add --no-cache curl
   
   # Make a request through the SOCKS5 proxy
   curl --socks5 socks5-server:1080 -U socksuser:sockspass http://web-server
   ```

## Security and Encryption

### SOCKS5 and Data Encryption

SOCKS5 itself **does not provide any encryption** for the data transferred through the proxy. This has important security implications:

1. **No Built-in Encryption**:
   - The SOCKS5 protocol only handles proxy connection establishment
   - Once established, data passes through unmodified and unencrypted
   - All traffic between proxy and destination server is in plaintext
   - This is visible in Wireshark captures - you can see full HTTP contents

2. **Adding Encryption Options**:
   - To secure SOCKS5 connections, encryption must be added separately
   - Common approaches include:

#### Option 1: SSH Tunneling (SSH + SOCKS5)
```bash
# Create encrypted SSH tunnel with SOCKS5 proxy
ssh -D 1080 -C -q -N username@remote-server

# Then use local SOCKS5 proxy
curl --socks5 localhost:1080 http://web-server
```
- This encrypts all traffic between client and SSH server
- The SSH server then forwards traffic to final destinations
- In this setup, SSH provides the encryption layer

#### Option 2: SOCKS5 over TLS/SSL
- Wrap the SOCKS5 connection in a TLS tunnel
- Requires a TLS wrapper like stunnel on both client and server
```bash
# Server side
stunnel -c -d 1080 -r socks5-server:1080

# Client side
curl --socks5 localhost:1080 http://web-server
```

#### Option 3: Use Application-level Encryption
- Use protocols that have built-in encryption (HTTPS, FTPS, etc.)
- The application data is encrypted before reaching SOCKS5
```bash
# Example: HTTPS through SOCKS5
curl --socks5 socks5-server:1080 https://secure-website.com
```
- In this case, even though SOCKS5 doesn't encrypt the tunnel, the HTTP data itself is encrypted

### Encryption Visualization

1. **Standard SOCKS5 (Unencrypted)**:
```
[Client] ---- SOCKS5 Handshake ----> [SOCKS5 Proxy] ---- Plaintext HTTP ----> [Web Server]
      \                                                                      /
       \__________________ Plaintext Data Visible to Observers _____________/
```

2. **SSH + SOCKS5 (Encrypted)**:
```
[Client] ==== Encrypted SSH Tunnel ==== [SSH Server+SOCKS5] ---- Plaintext HTTP ----> [Web Server]
      \                                                                              /
       \__ Encrypted __/   \__________ Plaintext Data Visible to Observers _________/
```

3. **HTTPS through SOCKS5 (End-to-end Encrypted)**:
```
[Client] ---- SOCKS5 Handshake ----> [SOCKS5 Proxy] ---- HTTPS ----> [Web Server]
      \                                                              /
       \__________________ End-to-End Encrypted Data _______________/
```

### Security Considerations

- **Traffic Analysis**: Even with encryption, an observer can still determine:
  - That you're connecting to a SOCKS5 proxy
  - Connection timing and data volume
  
- **Authentication**: SOCKS5 authentication (username/password) is transmitted in plaintext
  - Use additional encryption layer to protect credentials
  - SSH tunneling addresses this issue

- **Trust**: The SOCKS5 proxy server can see all unencrypted traffic
  - The proxy operator could potentially monitor your communications
  - Using end-to-end encrypted protocols (HTTPS) mitigates this risk

In this lab environment, all traffic is unencrypted for educational purposes to allow packet inspection. In production environments, you should always add encryption when using SOCKS5.

## SSH Dynamic Port Forwarding

SSH (Secure Shell) includes built-in functionality to create SOCKS5 proxies through what's called "dynamic port forwarding." This integration provides a convenient way to establish secure, encrypted SOCKS5 tunnels without installing additional proxy software.

### How SSH Dynamic Port Forwarding Works

When you use the SSH `-D` option, the SSH client creates a local SOCKS5 proxy server that tunnels all traffic through your encrypted SSH connection:

```
ssh -D 1080 username@remote-server
```

This command:
1. Establishes an encrypted SSH connection to the remote server
2. Creates a SOCKS5 proxy server listening on port 1080 of your local machine
3. Tunnels all applications' traffic configured to use this proxy through the encrypted SSH connection

### Implementation Example

1. **Establish the tunnel**:
   ```
   ssh -D 1080 -C -q -N username@remote-server
   ```
   - `-D 1080`: Create a SOCKS proxy on local port 1080
   - `-C`: Enable compression
   - `-q`: Quiet mode (no output)
   - `-N`: Do not execute remote commands (tunnel only)

2. **Configure applications** (e.g., browser) to use SOCKS5 proxy at `localhost:1080`

3. **All application traffic** now routes through the encrypted SSH tunnel

### Comparison with Dedicated SOCKS5 Server

This entire lab scenario can be replicated in a simpler manner using SSH's built-in SOCKS5 proxy feature:

| Feature | Our Docker Lab | SSH -D |
|---------|---------------|--------|
| SOCKS5 Implementation | Dedicated SOCKS5 server | Built into SSH client |
| Protocol Support | Full SOCKS5 (RFC 1928) | Full SOCKS5 (RFC 1928) |
| Encryption | None (plaintext) | Built-in SSH encryption |
| Authentication | SOCKS5 username/password | SSH authentication |
| Components | 4 containers | 1 SSH command |
| Protocol Analysis | Full visibility (unencrypted) | Limited visibility (encrypted) |
| Usage | Educational / Protocol inspection | Practical / Production use |

### SSH vs. Dedicated SOCKS5: Stability and Implementation Considerations

When choosing between SSH dynamic port forwarding and a dedicated SOCKS5 server, several practical factors should be considered:

#### Implementation Approach

1. **SSH's SOCKS5 Implementation**:
   - SSH **doesn't encapsulate** an existing SOCKS5 implementation - it **implements** the SOCKS5 protocol directly
   - The SOCKS5 proxy functionality is built into the SSH client program
   - When you use `-D`, the SSH client itself acts as a SOCKS5 server on the specified port
   - SSH client handles all SOCKS5 protocol details (handshake, authentication, connection requests)
   - The remote SSH server has no knowledge it's being used for SOCKS5 - it just forwards traffic

2. **Dedicated SOCKS5 Server**:
   - Purpose-built to implement the SOCKS5 protocol
   - Focus exclusively on proxying functionality
   - May offer more SOCKS5-specific configuration options
   - Typically runs as a standalone service

#### Stability Considerations

| Factor | SSH Dynamic Port Forwarding | Dedicated SOCKS5 Server |
|--------|----------------------------|-------------------------|
| **Connection Stability** | Dependent on SSH connection stability; if SSH connection drops, SOCKS proxy fails | Independent service; can be more resilient to network issues |
| **Idle Timeout** | SSH connections may time out after periods of inactivity | Dedicated servers typically handle idle connections better |
| **Connection Persistence** | Tools like `autossh` needed for auto-reconnection | Can implement its own reconnection logic |
| **Performance** | Overhead from encryption may impact throughput | May offer better performance without encryption |
| **Resource Usage** | Runs as part of SSH client process | Runs as a separate optimized service |
| **Load Handling** | Not optimized for high-volume traffic | Can be designed for high load scenarios |
| **Failure Recovery** | If SSH client crashes, proxy is lost | May have better crash recovery options |

#### When to Use Each Approach

**SSH Dynamic Port Forwarding is better when**:
- You need quick, temporary secure proxy access
- You already have SSH access to a remote server
- Security is a priority over maximum performance
- You're behind restrictive firewalls (SSH on port 22 is often allowed)
- You need a simple solution with minimal setup

**Dedicated SOCKS5 Server is better when**:
- You need a permanent proxy solution
- High traffic volume is expected
- You need specific SOCKS5 features not in SSH implementation
- Maximum performance is required
- You want to fine-tune proxy behavior
- You need to handle many concurrent connections

## Use Cases and Applications

### Common SOCKS5 Use Cases

- **Bypassing Geographical Restrictions**: Accessing region-restricted content by routing through proxies in permitted locations
- **Enhanced Privacy**: Hiding original IP address from destination servers
- **Firewall Circumvention**: Allowing connections through restrictive firewall policies
- **SSH Tunneling**: Often combined with SSH for secure port forwarding
- **Tor Network**: Used as part of the Tor anonymization network
- **Gaming**: Reducing latency by optimizing routing paths

### Using SOCKS5 for Origin Protection

SOCKS5 can be used as part of a security architecture to protect web servers and hide their origin IP addresses:

```
Internet <---> SOCKS5 Proxy <---> [Firewall] <---> Origin Web Server
```

In this setup:
1. Public users connect to your SOCKS5 proxy
2. Only the SOCKS5 proxy can communicate with your origin web server
3. The origin server's direct IP address is never exposed to the public

#### Implementation Steps

1. **Firewall Configuration**:
   - **CRITICAL**: Block all direct external access to your web server
   - Allow only connections from the SOCKS5 proxy server's IP address
   - Example iptables rules for the web server:
     ```bash
     # Allow only SOCKS5 proxy to connect to web port
     iptables -A INPUT -p tcp --dport 80 -s [SOCKS5_PROXY_IP] -j ACCEPT
     iptables -A INPUT -p tcp --dport 80 -j DROP
     
     # Same for HTTPS if needed
     iptables -A INPUT -p tcp --dport 443 -s [SOCKS5_PROXY_IP] -j ACCEPT
     iptables -A INPUT -p tcp --dport 443 -j DROP
     ```

2. **Reverse Proxy Consideration**:
   - While SOCKS5 can provide this protection, a reverse proxy (like Nginx) is typically better for HTTP services
   - SOCKS5 is protocol-agnostic but has no caching, load balancing, or HTTP-specific features

### SOCKS5 for End Users: Browser Configuration

For non-technical users who need to access protected web services, configuring their browsers to use SOCKS5 proxies is a viable option:

#### Firefox Configuration
1. Open Settings/Preferences
2. Search for "proxy" or go to Network Settings
3. Choose "Manual proxy configuration"
4. Enter SOCKS Host and Port (e.g., socks5-server:1080)
5. Select "SOCKS v5"
6. Check "Proxy DNS when using SOCKS v5" to prevent DNS leaks

#### Chrome Configuration
1. Open Settings
2. Search for "proxy" or navigate to System → Open your computer's proxy settings
3. In system settings, configure the SOCKS proxy
4. Set hostname and port for the SOCKS server

#### Safari (macOS)
1. Open System Preferences → Network
2. Select active connection → Advanced → Proxies
3. Check "SOCKS Proxy"
4. Enter SOCKS proxy server and port

### Enterprise Solutions: IT-Managed Proxy Access

For organizations where users shouldn't or can't run SSH commands directly, IT teams can implement several alternative approaches:

1. **Centralized Proxy Server Solutions**
2. **Pre-Configured VPN Solutions**
3. **Pre-Configured SSH Client Packages**
4. **Remote Browser Isolation**
5. **Pre-Configured Browser Distributions**
6. **Jump Server / Bastion Host Approach**

The best approach often combines multiple solutions - for example, a centralized proxy for general users and SSH tunneling for power users or administrators.
