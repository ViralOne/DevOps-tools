import asyncio
import argparse
import ipaddress

async def scan_port(ip, port, banner_grab, username=None, password=None, timeout=1):
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout=timeout)
        print(f"IP: {ip}, Port: {port} - Open")

        if banner_grab:
            banner = await grab_banner(reader)
            print(f"Banner: {banner}")

        if username and password:
            auth_result = await authenticate(reader, writer, username, password)
            if auth_result:
                print(f"Authentication successful for {ip}:{port}")
            else:
                print(f"Authentication failed for {ip}:{port}")

        writer.close()
    except (asyncio.TimeoutError, OSError):
        pass

async def grab_banner(reader):
    try:
        data = await reader.read(1024)
        return data.decode().strip()
    except asyncio.CancelledError:
        pass

async def authenticate(reader, writer, username, password):
    try:
        writer.write(f"{username}:{password}\n".encode())
        await writer.drain()

        response = await reader.read(1024)
        return response.decode().strip() == "Authentication successful"
    except asyncio.CancelledError:
        pass

async def scan_ports(ip, ports, banner_grab, username=None, password=None, timeout=1):
    tasks = [scan_port(ip, port, banner_grab, username, password, timeout) for port in ports]
    await asyncio.gather(*tasks)

async def scan_cidr(cidr, ports, banner_grab, username=None, password=None, timeout=1):
    network = ipaddress.IPv4Network(cidr, strict=False)
    tasks = [scan_ports(str(ip), ports, banner_grab, username, password, timeout) for ip in network.hosts()]
    await asyncio.gather(*tasks)

def main():
    parser = argparse.ArgumentParser(description="Advanced asynchronous port scanner")
    parser.add_argument("-c", "--cidr", help="CIDR notation for scanning multiple IPs")
    parser.add_argument("-i", "--ip", help="Single IP to scan")
    parser.add_argument("-l", "--portlist", help="File containing a list of ports")
    parser.add_argument("-p", "--ports", help="Comma-separated list of ports to scan")
    parser.add_argument("-t", "--timeout", type=float, default=1, help="Timeout value in seconds (default: 1)")
    parser.add_argument("--banner-grab", action="store_true", help="Grab banner/header from open ports")
    parser.add_argument("--username", help="Username for authentication")
    parser.add_argument("--password", help="Password for authentication")
    args = parser.parse_args()

    port_list = []
    if args.ports:
        port_list = [int(port) for port in args.ports.split(',')]
    else:
        with open(args.portlist, "r") as port_file:
            port_list = [int(line.strip()) for line in port_file]

    if args.cidr:
        asyncio.run(scan_cidr(args.cidr, port_list, args.banner_grab, args.username, args.password, args.timeout))
    else:
        asyncio.run(scan_ports(args.ip, port_list, args.banner_grab, args.username, args.password, args.timeout))

if __name__ == "__main__":
    main()
