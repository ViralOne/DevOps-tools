import asyncio
import argparse
import ipaddress

async def scan_port(ip, port):
    try:
        reader, writer = await asyncio.open_connection(ip, port)
        print(f"IP: {ip}, Port: {port} - Open")
        writer.close()
    except (asyncio.TimeoutError, OSError):
        pass

async def scan_ports(ip, ports):
    tasks = [scan_port(ip, port) for port in ports]
    await asyncio.gather(*tasks)

async def scan_cidr(cidr, ports):
    network = ipaddress.IPv4Network(cidr, strict=False)
    tasks = [scan_ports(str(ip), ports) for ip in network.hosts()]
    await asyncio.gather(*tasks)

def main():
    parser = argparse.ArgumentParser(description="Simple asynchronous port scanner")
    parser.add_argument("-c", "--cidr", help="CIDR notation for scanning multiple IPs")
    parser.add_argument("-i", "--ip", help="Single IP to scan")
    parser.add_argument("-l", "--portlist", help="File containing a list of ports")
    parser.add_argument("-p", "--ports", help="Comma-separated list of ports to scan")
    args = parser.parse_args()

    port_list = []
    if args.ports:
        port_list = [int(port) for port in args.ports.split(',')]
    else:
        with open(args.portlist, "r") as port_file:
            port_list = [int(line.strip()) for line in port_file]

    if args.cidr:
        asyncio.run(scan_cidr(args.cidr, port_list))
    else:
        asyncio.run(scan_ports(args.ip, port_list))

if __name__ == "__main__":
    main()
