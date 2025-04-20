# SOCKS5 Protocol Lab

## Quick Start
```bash
docker-compose up -d
```

## Components
- SOCKS5 proxy server (port 1080, auth: socksuser/sockspass)
- Client container for testing
- Wireshark for packet analysis
- Target web server

## Lab Architecture and Component Roles

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
  - Has access to the test script for exploring the protocol
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

## How SOCKS5 Works in This Lab

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
   - To verify this, compare the same HTTP request directly to a server vs. through SOCKS5:
     - Only the TCP/IP addressing changes
     - The HTTP payload is identical with no additional SOCKS5 bytes

7. **Protocol Analysis**:
   - Wireshark container captures all this traffic in real-time
   - All stages of the protocol can be inspected and analyzed

### Key Protocol Interactions

When you run the test script (`/scripts/test-socks5.sh`), it:

1. Tests basic connectivity to the SOCKS5 server
2. Sends raw SOCKS5 protocol bytes using netcat to demonstrate handshake
3. Uses curl with SOCKS5 support to make a complete connection
4. Shows the full protocol exchange with verbose output

This allows you to see both the low-level protocol details and practical application usage.

## Basic Tests
```bash
# Test proxy connection
docker exec -it socks-client sh
curl --socks5 socks5-server:1080 -U socksuser:sockspass http://web-server

# Analyze with Wireshark
# Visit http://localhost:3000
```

## Wireshark Analysis Guide

The lab includes browser-based Wireshark that can be accessed at http://localhost:3000. Here's how to analyze SOCKS5 protocol in detail:

### Useful Filters

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

### What to Look For

#### SOCKS5 Protocol Handshake

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

### Analysis Techniques

1. **Color Coding**: Wireshark uses different colors for different protocols
   - Look for the color transitions to identify where the SOCKS5 handshake ends and tunneled data begins

2. **TCP Stream View**: Shows the complete conversation
   - Shows both hex and ASCII formats
   - Makes it easy to identify protocol boundaries

3. **Time Analysis**:
   - Check the time between packets to understand protocol latency
   - Look for delays in authentication or connection phases

4. **Protocol Hierarchy**:
   - Statistics → Protocol Hierarchy shows traffic composition
   - Helps differentiate between handshake and tunneled data

### Real-world Example

When making a CURL request through the proxy, you'll see:
1. TCP connection to the SOCKS server (SYN, SYN-ACK)
2. SOCKS5 handshake packets
3. TCP connection from proxy to target server
4. HTTP request/response tunneled through the proxy

### Specific Byte Patterns

The most critical SOCKS5 protocol bytes to observe:
- Version identifier: `05`
- Authentication methods: `00` (no auth), `02` (username/password)
- Command codes: `01` (CONNECT), `02` (BIND), `03` (UDP ASSOCIATE)
- Address types: `01` (IPv4), `03` (Domain name), `04` (IPv6)
- Reply codes: `00` (Success), `01`-`08` (Various error codes)

### Locating SOCKS5 Protocol Bytes in Wireshark

When analyzing SOCKS5 traffic in Wireshark, you need to know where to look for the protocol bytes:

1. **Select a TCP packet** on port 1080 after the TCP handshake (SYN, SYN-ACK, ACK)

2. **Expand the packet details**:
   - Look for the "Transmission Control Protocol" section
   - Expand that section to see the TCP payload
   - Look for a section labeled either:
     - "Data" (for raw unidentified protocol data)
     - "SOCKS Protocol" (if Wireshark recognizes it)

3. **View the bytes in these fields**:
   - In the middle pane, look for the hexadecimal representation
   - For example, the bytes `05 01 00` will appear in the "Data" section
   - This is typically displayed both as hex and ASCII

4. **Alternative view**:
   - Right-click a packet → "Follow" → "TCP Stream"
   - In the popup window, switch to "Hex Dump" view
   - Look for the pattern starting with `05 01 00` or `05 02 00 02`
   - Client messages are typically colored red, server responses blue

5. **Finding specific bytes**:
   - Use display filter: `tcp.payload contains 05:01:00`
   - Or use filter: `data contains 05:01:00`

6. **Packet bytes pane** (bottom):
   - The bottom pane shows raw packet bytes
   - The SOCKS5 protocol begins after the TCP header
   - Typically starts around byte offset 54 or 66 (depending on IP version)
   - Look for `05 01 00` pattern highlighted in this view

7. **For SOCKS5 authentication**:
   - After the server replies with `05 02`
   - Look for client packets containing the pattern `01` followed by username/password
   - These appear in the same packet areas described above

The SOCKS5 bytes are not interpreted by a dissector in all Wireshark versions, so they often appear simply as "Data" in the TCP payload.

## Protocol Encapsulation

### SOCKS5 in the Network Stack

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

### Complete Frame Structure

In Wireshark, a typical SOCKS5 packet is encapsulated as follows:

1. **Ethernet Frame** (Layer 2)
   - 14 bytes: Ethernet header
     - 6 bytes: Destination MAC address
     - 6 bytes: Source MAC address
     - 2 bytes: EtherType (0x0800 for IPv4, 0x86DD for IPv6)

2. **IP Packet** (Layer 3)
   - For IPv4: 20+ bytes header
     - Includes source and destination IP addresses
     - Protocol field set to 6 (TCP)
   - For IPv6: 40 bytes header

3. **TCP Segment** (Layer 4)
   - 20+ bytes: TCP header
     - Source port (client ephemeral port)
     - Destination port (1080 for SOCKS5)
     - Sequence and acknowledgment numbers
     - Flags, window size, etc.

4. **SOCKS5 Message** (Layer 5)
   - Initial handshake:
     - Client greeting (3+ bytes)
     - Server choice (2 bytes)
   - Authentication (if required):
     - Variable length authentication data
   - Connection request/response:
     - Command, address type, address, port

5. **Application Data** (Layer 7)
   - After SOCKS5 handshake completes
   - HTTP, FTP, or other protocol data
   
### SOCKS5 Protocol Position in TCP Stream

In a TCP stream carrying SOCKS5 traffic:

1. **First few packets**: Pure SOCKS5 protocol (handshake)
   - These packets contain ONLY SOCKS5 protocol bytes
   - No application data is present yet

2. **Subsequent packets**: Application protocol encapsulated in the established SOCKS5 tunnel
   - After connection establishment, the SOCKS5 protocol disappears
   - The TCP connection now carries pure application data (e.g., HTTP)

### Identifying SOCKS5 in Wireshark

1. **Packet List**: 
   - Filter for TCP port 1080 (`tcp.port == 1080`)
   - Initial packets after TCP handshake contain SOCKS5 protocol

2. **Packet Details**:
   - Expand: Ethernet II → Internet Protocol → Transmission Control Protocol → Data
   - The "Data" section contains the SOCKS5 protocol bytes

3. **Packet Bytes**:
   - Bottom pane shows all bytes in the packet
   - SOCKS5 protocol begins after the TCP header (typically 54 or 74 bytes in)
   - First SOCKS5 byte (0x05) indicates protocol version

4. **TCP Stream Reassembly**:
   - Follow TCP Stream to see the complete SOCKS handshake sequence
   - Observe transition from SOCKS5 protocol to application data

### Why This Matters

Understanding this encapsulation helps you:
- Locate SOCKS5 protocol bytes in Wireshark captures
- Understand protocol boundaries and state transitions
- Distinguish between SOCKS5 protocol traffic and tunneled application data
- Analyze timing and overhead of the SOCKS5 protocol itself

### Layer Responsibility: OS vs. User-Space Applications

When working with SOCKS5 and network protocols, different layers are handled by different components:

| Layer | OSI Layer | Handled By | Description |
|-------|-----------|------------|-------------|
| Ethernet Frame | Layer 1-2 | **OS Kernel** | The operating system and network drivers fully handle the physical and data link layers. User applications never directly encode Ethernet frames. |
| IP | Layer 3 | **OS Kernel** | IP packet construction, routing decisions, and header handling are managed by the kernel's networking stack. |
| TCP | Layer 4 | **OS Kernel** | The operating system handles TCP connection management, segmentation, retransmissions, and flow control. Applications only see a stream interface. |
| SOCKS5 | Layer 5 | **User Application** | This is where the boundary typically exists. Our client scripts (or library) must implement the SOCKS5 protocol by constructing the correct byte sequences. |
| Application | Layer 7 | **User Application** | The actual data (HTTP, FTP, etc.) is handled entirely by user-space code. |

#### In Our Lab Environment:

1. **User-Space Responsibilities** (Our Scripts/Applications):
   - Constructing the SOCKS5 protocol messages (`\x05\x01\x00`, etc.)
   - Formatting authentication credentials
   - Creating connection requests with proper address types
   - Interpreting SOCKS5 server responses
   - Handling application protocols (HTTP in our example)

2. **OS/Kernel Responsibilities**:
   - Creating TCP sockets for the SOCKS5 connection
   - Managing the TCP connection state
   - Constructing IP packets with proper headers
   - Building Ethernet frames with correct addressing
   - Managing ARP for MAC address resolution
   - Handling physical transmission of frames

#### Implementation Details:

- **Low-level Testing** (in `test-socks5.sh`

## Security and Encryption with SOCKS5

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

## Replicating This Lab with SSH Dynamic Port Forwarding

This entire lab scenario can be replicated in a simpler manner using SSH's built-in SOCKS5 proxy feature via dynamic port forwarding (`-D` option).

### How SSH Implements SOCKS5

When you run `ssh -D 1080 username@remote-server`, SSH creates a SOCKS5 proxy server listening on port 1080 of your local machine:

1. **SSH as a SOCKS5 Server**:
   - SSH client creates a local SOCKS5 proxy server
   - All SOCKS5 protocol handling is done by the SSH client
   - The remote SSH server doesn't need any SOCKS-specific setup

2. **Comparison with this Lab**:

   | Feature | Our Docker Lab | SSH -D |
   |---------|---------------|--------|
   | SOCKS5 Implementation | Dedicated SOCKS5 server | Built into SSH client |
   | Protocol Support | Full SOCKS5 (RFC 1928) | Full SOCKS5 (RFC 1928) |
   | Encryption | None (plaintext) | Built-in SSH encryption |
   | Authentication | SOCKS5 username/password | SSH authentication |
   | Components | 4 containers | 1 SSH command |
   | Protocol Analysis | Full visibility (unencrypted) | Limited visibility (encrypted) |
   | Usage | Educational / Protocol inspection | Practical / Production use |

3. **SSH -D Command Equivalent**:
   ```bash
   # Instead of our Docker lab setup, you could simply:
   ssh -D 1080 -C -q -N user@remote-server
   
   # Then use curl exactly the same way:
   curl --socks5 localhost:1080 http://example.com
   ```

4. **Key Differences**:
   - SSH automatically encrypts all traffic
   - SOCKS5 authentication is replaced by SSH authentication
   - Protocol inspection is much more difficult (can't see plaintext)
   - No need for a dedicated SOCKS5 server

5. **Why Use Our Lab Instead?**:
   - Educational value (seeing the raw protocol)
   - Ability to inspect unencrypted traffic
   - Understanding the SOCKS5 protocol details
   - Flexibility to modify and experiment with protocol details

### Combining the Lab with SSH

You could enhance this lab by adding an SSH server container and demonstrating the difference between:
1. Direct SOCKS5 (our current setup)
2. SSH-based SOCKS5 (with the added SSH container)

This would show how the same application behaves with both methods, but with the SSH version providing encryption.

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

#### Practical Consideration: Connection Management

One key difference is how connection drops are handled:

- **SSH-based SOCKS5**: 
  ```
  Client --> [SSH SOCKS5 on localhost] ==SSH CONNECTION==> Remote SSH Server --> Destination
  ```
  If the SSH connection drops, the entire SOCKS5 service becomes unavailable until reconnection.

- **Dedicated SOCKS5**:
  ```
  Client --> SOCKS5 Server --> Destination
  ```
  If a client connection drops, other connections are unaffected, and the service remains available.

For production use, many organizations employ both approaches in combination:
- SSH dynamic port forwarding for administrative/secure access
- Dedicated SOCKS5 servers for high-volume or performance-critical applications

## Using SOCKS5 for Origin Protection

SOCKS5 can be used as part of a security architecture to protect web servers and hide their origin IP addresses. Here's how to implement this strategy:

### Security Architecture with SOCKS5 as a Protective Layer

```
Internet <---> SOCKS5 Proxy <---> [Firewall] <---> Origin Web Server
```

In this setup:
1. Public users connect to your SOCKS5 proxy
2. Only the SOCKS5 proxy can communicate with your origin web server
3. The origin server's direct IP address is never exposed to the public

### Implementation Steps

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

2. **Reverse Proxy Configuration**:
   - While SOCKS5 can provide this protection, a reverse proxy (like Nginx) is typically better for HTTP services
   - SOCKS5 is protocol-agnostic but has no caching, load balancing, or HTTP-specific features
   - Consider this hybrid approach:
     ```
     Internet <---> Nginx Reverse Proxy <---> [Firewall] <---> Origin Web Server
                    ^
                    | (Administrative access)
                 SOCKS5 Proxy
     ```

3. **DNS Protection**:
   - Ensure your origin server's hostname resolves only to internal IPs
   - Use separate public DNS records that point to your proxy

### Security Benefits

- **DDoS Protection**: Attacks hit your proxy, not your origin server
- **IP Concealment**: Clients never see your origin server's IP address
- **Access Control**: Origin server accessible only through controlled channels
- **Inspection Point**: All traffic can be monitored at the proxy
- **Geographic Distribution**: Proxies can be placed in multiple regions

### Limitations When Using SOCKS5 for Web Protection

1. **Protocol Limitations**:
   - SOCKS5 doesn't understand HTTP specifically
   - No SSL termination capabilities
   - No HTTP header manipulation
   - No caching or compression

2. **Better Alternatives for Web Traffic**:
   - For HTTP/HTTPS specifically, a reverse proxy like Nginx or a CDN will provide better features
   - SOCKS5 is more appropriate for protecting non-HTTP services or for creating general-purpose tunnels

3. **Authentication Requirements**:
   - For public web access, you'll need to modify the architecture as standard web browsers don't support SOCKS5 by default
   - Consider a reverse proxy that accepts standard HTTP/HTTPS and internally connects via SOCKS5

### Production Architecture Recommendation

For protecting a web server in production:

1. **Public-Facing Layer**:
   - CDN or reverse proxy (Nginx/HAProxy)
   - DDoS protection services

2. **Restricted Access Layer**:
   - SOCKS5 proxy for administrative access
   - SSH bastion host with dynamic port forwarding

3. **Origin Protection**:
   - Strict firewall rules allowing only connections from trusted proxies
   - No public DNS records pointing to origin
   - Web server configured to reject requests with incorrect host headers

This layered approach provides much stronger protection than SOCKS5 alone, while still allowing you to use SOCKS5 for specific administrative access scenarios.

## SOCKS5 for End Users: Browser Configuration and SSH Integration

For non-technical users who need to access protected web services, configuring their browsers to use SOCKS5 proxies is a viable option. Here's how browser-based SOCKS5 access works and its relationship to SSH dynamic port forwarding:

### Browser SOCKS5 Configuration for End Users

Most modern web browsers support SOCKS5 proxy configuration:

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

### User Experience with Browser SOCKS5 Configuration

1. **Advantages for End Users**:
   - No additional software required
   - Works with all websites once configured
   - DNS requests can be proxied to prevent leaks
   - All browser traffic flows through the proxy

2. **Disadvantages for End Users**:
   - Affects all browsing (unless using browser extensions that allow per-site proxying)
   - Requires manual configuration
   - Non-browser applications still require separate configuration
   - May slow down browsing due to proxy overhead

### SSH Dynamic Port Forwarding for End Users

This is where SSH's `-D` feature becomes particularly valuable:

```
[User's Computer] <---> [SSH Server with Internet Access] <---> [Protected Website]
   |
   +--> Browser configured to use localhost:1080 as SOCKS5 proxy
   +--> SSH client running: ssh -D 1080 user@ssh-server
```

#### Practical End-User Implementation

1. **Local SSH Client Setup**:
   ```bash
   # User runs this on their machine
   ssh -D 1080 -C -q -N user@ssh-server.example.com
   ```

2. **Browser Configuration**:
   - Configure browser to use `localhost:1080` as SOCKS5 proxy
   - All browser traffic now tunnels through SSH connection

3. **User-Friendly Packaging**:
   - For non-technical users, this can be packaged as a simple application
   - Create a one-click solution that establishes SSH connection and configures browser
   - Examples: FoxyProxy with SSH integration, custom wrapper applications

### Relation Between Browser SOCKS5 and SSH Dynamic Port Forwarding

SSH's `-D` option creates a SOCKS5 proxy server on the user's local machine that tunnels traffic through the SSH connection:

1. **Technical Relationship**:
   - The SSH client itself implements a SOCKS5 server
   - Browser connects to this local SOCKS5 server
   - Traffic flows: Browser → Local SSH SOCKS5 Server → SSH Encrypted Tunnel → SSH Server → Destination

2. **Browser Perspective**:
   - Browser doesn't know it's using SSH
   - Browser simply sees a standard SOCKS5 proxy at localhost:1080
   - Same browser configuration works with both standalone SOCKS5 and SSH-provided SOCKS5

3. **Security Advantages**:
   - All traffic is encrypted within the SSH tunnel
   - SSH provides authentication
   - DNS queries can be tunneled, preventing DNS leaks

### Practical Use Cases

1. **Corporate Access Solution**:
   - Employees need access to internal websites
   - Company provides SSH access to a bastion host
   - Employees use SSH -D and browser configuration to access internal resources

2. **Censorship Circumvention**:
   - Users in restricted networks configure browsers to use SSH-provided SOCKS5
   - All traffic tunnels through SSH to an unrestricted server
   - Particularly useful when standard SOCKS5 ports might be blocked

3. **Secure Public Wi-Fi Browsing**:
   - Users connect to untrusted networks
   - All browser traffic encrypted through SSH tunnel
   - Prevents local network sniffing of web traffic

### Implementation Example: User-Friendly Script

For less technical users, a simple script can make the process more accessible:

```bash
#!/bin/bash
# secure-browser.sh - Start SSH tunnel and configured browser

# Start SSH tunnel in background
ssh -D 1080 -C -q -N user@ssh-server.example.com &
SSH_PID=$!

# Wait for tunnel to establish
sleep 2

# Launch browser with proxy configuration
# Firefox example with profile that has SOCKS configured
firefox -P socks_profile

# When browser closes, kill SSH tunnel
kill $SSH_PID
```

This approach makes SSH dynamic port forwarding accessible to end users who may not be familiar with command-line tools.

## Enterprise Solutions: IT-Managed Proxy Access

For organizations where users shouldn't or can't run SSH commands directly, IT teams can implement several alternative approaches that provide the same benefits with less technical burden on end users.

### 1. Centralized Proxy Server Solutions

#### Dedicated Edge Proxy Server

```
[User Browsers] <---> [IT-Managed SOCKS5/HTTP Proxy] <---> [Protected Resources]
```

- **Implementation Options**:
  - Deploy a dedicated proxy server (SOCKS5, HTTP, or both)
  - Place this server at the network edge
  - Configure enterprise firewall to allow only this proxy to access protected resources
  - Provide users with simple proxy configuration instructions

- **Enterprise Technologies**:
  - **Squid Proxy**: Supports both HTTP and SOCKS protocols
  - **Dante**: Enterprise-grade SOCKS server with strong authentication
  - **HAProxy**: High-performance TCP/HTTP proxy
  - **Commercial proxies**: Blue Coat, Cisco, Forcepoint

- **Advantages**:
  - Centralized management and logging
  - No client-side software beyond browser configuration
  - Works with all client operating systems
  - Can implement authentication, filtering, and access control

### 2. Pre-Configured VPN Solutions

For even greater simplicity for end users:

```
[User with VPN Client] <===> [VPN Concentrator] <---> [Protected Resources]
```

- **Implementation Options**:
  - Deploy enterprise VPN solution (Cisco, Fortinet, Pulse Secure, etc.)
  - Configure split tunneling to route only protected resources through VPN
  - Provide users with simple VPN client

- **Advantages over Direct SOCKS5**:
  - More familiar to end users than proxy settings
  - Routes all application traffic, not just browser
  - Integrated with enterprise authentication systems
  - Often packaged as a simple installer with one-click connect

### 3. Pre-Configured SSH Client Packages

For organizations preferring the SSH approach but wanting to simplify user experience:

- **Packaged SSH Client with Pre-configured Settings**:
  - Create custom installers that bundle:
    - SSH client software
    - Pre-configured connection settings
    - Auto-start script that establishes SSH tunnel
    - System-wide proxy settings configuration

- **Example Implementation**:
  - Deploy OpenSSH with a custom configuration file
  - Create Windows service or Mac/Linux daemon that maintains the SSH tunnel
  - Use system-level proxy settings rather than per-browser

- **Commercial Solutions**:
  - **Tectia SSH**: Enterprise SSH with packaged client configurations
  - **Bitvise SSH**: Windows-centric SSH with GUI and configuration packaging

### 4. Remote Browser Isolation

A modern approach that completely removes the need for client-side configuration:

```
[User's Standard Browser] <---> [Cloud-hosted Browsing Session] <---> [Protected Resources]
```

- **Implementation**:
  - Deploy a browser isolation platform (Symantec Web Isolation, Citrix Secure Browser, etc.)
  - Users access a URL that connects to a remote browser instance
  - The remote browser connects to protected resources
  - Only rendered content is streamed to the user's device

- **Advantages**:
  - Zero client configuration
  - Works on any device with a standard browser
  - No local software installation
  - Can provide additional security by isolating browsing activity from user's device

### 5. Pre-Configured Browser Distributions

IT teams can provide custom browser packages with proxy settings pre-configured:

- **Implementation Options**:
  - Package Firefox or Chrome with custom proxy settings
  - Create portable browser installations with proxy configuration
  - Use Firefox's Enterprise MSI installers with pre-configured proxy settings
  - Use Chrome's enterprise policy settings

- **Example Deployment**:
  - Package Firefox Portable with:
    - Pre-configured SOCKS5 proxy settings
    - Bookmark to launch SSH connection script
    - Custom profile that separates from user's normal browsing

### 6. Jump Server / Bastion Host Approach

For administrative access to protected resources:

```
[Users] <---> [Web-based Jump Server] <---> [Protected Resources]
```

- **Implementation**:
  - Deploy a server with web-based terminal access (Apache Guacamole, etc.)
  - Users connect through web browser to jump server
  - Jump server has direct access to protected resources
  - All access and commands logged centrally

- **Advantages**:
  - No client software required beyond a browser
  - Complete audit trail of all access and commands
  - Centralizes security controls
  - Works from any device with a web browser

### Factors for Choosing the Right Approach

When selecting a solution for your organization, consider:

1. **User Technical Ability**: Lower technical ability favors VPN or packaged solutions
2. **Security Requirements**: Higher security needs may favor jump servers or remote isolation
3. **Scale**: Larger deployments benefit from centralized, managed solutions
4. **Client Environment**: Diverse client devices favor browser-based solutions
5. **Management Overhead**: Consider ongoing maintenance requirements
6. **Performance Needs**: Some solutions (like remote browser isolation) may introduce latency

The best approach often combines multiple solutions - for example, a centralized proxy for general users and SSH tunneling for power users or administrators.

## Protocol Analyzer Tool

This lab includes a specialized SOCKS5 protocol analyzer tool (`protocol_analyzer.py`) that complements Wireshark by providing detailed field-by-field explanations of SOCKS5 protocol messages. While Wireshark offers comprehensive packet capture and visualization, this tool focuses exclusively on SOCKS5 protocol structure.

### Key Features

- **Detailed Protocol Dissection**: Breaks down each field in SOCKS5 messages
- **Field-by-Field Explanations**: Explains the meaning and purpose of each byte
- **Command-Line Interface**: Easy to use with captured packet data
- **Educational Focus**: Designed to help understand protocol structure

### Using the Protocol Analyzer

The analyzer is mounted in both the client and analyzer containers and can be accessed at `/usr/local/bin/socks5-analyzer.py`. It accepts hex data representing SOCKS5 protocol messages and provides detailed explanations.

#### Basic Usage:

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

#### Example Usage:

```bash
# Analyze a client greeting packet
python3 /usr/local/bin/socks5-analyzer.py client_greeting --hex "05020002"
```

#### Integration with Wireshark:

1. Capture SOCKS5 traffic in Wireshark
2. Select a SOCKS5 packet of interest
3. Right-click → Copy → Bytes (Hex Stream)
4. Use the protocol analyzer with the copied hex data

#### Demonstration Script:

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

### Why Use the Protocol Analyzer?

While Wireshark provides excellent visualization of network traffic, the protocol analyzer offers:

1. **Simplified Output**: Focuses only on SOCKS5-specific fields
2. **Educational Explanations**: Provides more context about field meanings
3. **Field-Level Details**: Shows exactly what each byte represents
4. **Command-Line Interface**: Useful for scripting or automated analysis
5. **No GUI Required**: Can be used in environments without graphical interfaces

By using both tools together, you can gain a deeper understanding of the SOCKS5 protocol structure and behavior.

## Protocol Reference