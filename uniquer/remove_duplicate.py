def remove_and_sort_ips(input_file='ips.txt', output_file='uniqueips.txt'):
    with open(input_file, 'r') as f:
        ips = f.read().splitlines()

    # Remove duplicates while preserving order
    unique_ips = list(dict.fromkeys(ips))

    # Sort IPs by converting them into tuples of integers
    unique_ips.sort(key=lambda ip: tuple(map(int, ip.split('.'))))

    with open(output_file, 'w') as f:
        for ip in unique_ips:
            f.write(ip + '\n')

if __name__ == "__main__":
    remove_and_sort_ips()
