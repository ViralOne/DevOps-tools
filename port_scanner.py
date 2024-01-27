import asyncio
import argparse
import ipaddress
import json
import sys
from datetime import datetime

async def scan_port(ip, port, banner, username=None, password=None, timeout=1):
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout=timeout)
        result = {"ip": ip, "port": port, "status": "Open"}

        if banner:
            result["banner"] = await grab_banner(reader)

        if username and password:
            result["authentication"] = await authenticate(reader, writer, username, password)

        writer.close()
    except (asyncio.TimeoutError, OSError):
        result = {"ip": ip, "port": port, "status": "Closed"}

    return result

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

async def scan_ports(ip, ports, banner, username=None, password=None, timeout=1):
    tasks = [scan_port(ip, port, banner, username, password, timeout) for port in ports]
    return await asyncio.gather(*tasks)

async def scan_cidr(cidr, ports, banner, username=None, password=None, timeout=1):
    network = ipaddress.IPv4Network(cidr, strict=False)
    tasks = [scan_ports(str(ip), ports, banner, username, password, timeout) for ip in network.hosts()]
    return await asyncio.gather(*tasks)

async def scan_range(start_ip, end_ip, ports, banner, username=None, password=None, timeout=1):
    start_ip_obj = ipaddress.IPv4Address(start_ip)
    end_ip_obj = ipaddress.IPv4Address(end_ip)

    current_ip_obj = start_ip_obj
    tasks = []

    while current_ip_obj <= end_ip_obj:
        tasks.append(scan_ports(str(current_ip_obj), ports, banner, username, password, timeout))
        current_ip_obj += 1

    return await asyncio.gather(*tasks)

def save_to_json(data, output_file):
    current_time = datetime.now().strftime("%d-%m-%Y-%H%M")
    file_name = f"{output_file}_{current_time}.json"

    with open(file_name, 'w') as json_file:
        json.dump(data, json_file, indent=2)

def print_results(results):
    for ip_results in results:
        if isinstance(ip_results, list):
            ip_address = ip_results[0]["ip"]
            print(f"IP: {ip_address}")

            for result in ip_results:
                port_status = f"Port: {result['port']} - {result['status']}"

                if "banner" in result:
                    port_status += f" - Banner: {result['banner']}"

                if "authentication" in result:
                    port_status += f" - Authentication: {'Successful' if result['authentication'] else 'Failed'}"

                print(port_status)

            print()
        else:
            ip_address = ip_results["ip"]
            port_status = f"Port: {ip_results['port']} - {ip_results['status']}"

            if "banner" in ip_results:
                port_status += f" - Banner: {ip_results['banner']}"

            if "authentication" in ip_results:
                port_status += f" - Authentication: {'Successful' if ip_results['authentication'] else 'Failed'}"

            print(f"IP: {ip_address} - {port_status}\n")

def parse_args():
    parser = argparse.ArgumentParser(description="Advanced asynchronous port scanner")
    parser.add_argument("-c", "--cidr", help="CIDR notation for scanning multiple IPs")
    parser.add_argument("-i", "--ip", help="Single IP to scan")
    parser.add_argument("-r", "--range", help="IP range for scanning")
    parser.add_argument("-l", "--portlist", help="File containing a list of ports")
    parser.add_argument("-p", "--ports", help="Comma-separated list of ports to scan")
    parser.add_argument("-t", "--timeout", type=float, default=1, help="Timeout value in seconds (default: 1)")
    parser.add_argument("--banner", action="store_true", help="Grab banner/header from open ports")
    parser.add_argument("-o", "--output", help="Output file in JSON format")
    parser.add_argument("--username", help="Username for authentication")
    parser.add_argument("--password", help="Password for authentication")
    return parser.parse_args()

def main():
    args = parse_args()

    # Check if either -c, -i, or -r is provided, and either -l or -p is provided
    if not ((args.cidr or args.ip or args.range) and (args.ports or args.portlist)):
        print("Error: Specify either -c, -i, or -r along with either -l or -p.")
        sys.exit(1)

    port_list = []

    if args.ports:
        port_list = [int(port) for port in args.ports.split(',')]
    elif args.portlist:
        with open(args.portlist, "r") as port_file:
            port_list = [int(line.strip()) for line in port_file]

    if args.cidr:
        results = asyncio.run(scan_cidr(args.cidr, port_list, args.banner, args.username, args.password, args.timeout))
        output_file_name = args.cidr.replace("/", "_") if not args.output else args.output
    elif args.range:
        start_ip, end_ip = args.range.split('-')
        results = asyncio.run(scan_range(start_ip, end_ip, port_list, args.banner, args.username, args.password, args.timeout))
        output_file_name = args.range.replace("/", "_") if not args.output else args.output
    else:
        results = asyncio.run(scan_ports(args.ip, port_list, args.banner, args.username, args.password, args.timeout))
        output_file_name = args.ip if not args.output else args.output

    if args.output:
        save_to_json(results, output_file_name)
    else:
        print_results(results)

if __name__ == "__main__":
    main()
