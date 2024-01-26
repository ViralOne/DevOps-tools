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

async def scan_ports(ip, port_list):
    tasks = [scan_port(ip, port) for port in port_list]
    await asyncio.gather(*tasks)

async def scan_cidr(cidr, port_list):
    network = ipaddress.IPv4Network(cidr, strict=False)
    tasks = [scan_ports(str(ip), port_list) for ip in network.hosts()]
    await asyncio.gather(*tasks)

def main():
    parser = argparse.ArgumentParser(description="Simple asynchronous port scanner")
    parser.add_argument("-c", "--cidr", help="CIDR notation for scanning multiple IPs")
    parser.add_argument("-i", "--ip", help="Single IP to scan")
    parser.add_argument("-l", "--portlist", help="File containing a list of ports", required=True)
    args = parser.parse_args()

    port_list = []
    with open(args.portlist, "r") as port_file:
        port_list = [int(line.strip()) for line in port_file]

    asyncio.run(scan_cidr(args.cidr, port_list)) if args.cidr else asyncio.run(scan_ports(args.ip, port_list))

if __name__ == "__main__":
    main()
