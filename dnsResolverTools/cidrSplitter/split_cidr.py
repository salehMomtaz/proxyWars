import ipaddress
import sys

def ips_in_cidr(cidr):
    """Calculate number of IP addresses in a CIDR block."""
    net = ipaddress.ip_network(cidr, strict=False)
    return net.num_addresses

def split_cidr(cidr):
    """Split a CIDR into two equal sub-CIDRs."""
    net = ipaddress.ip_network(cidr, strict=False)
    if net.prefixlen == 32:
        # Cannot split further
        return [str(net)]

    new_prefix = net.prefixlen + 1
    subnets = list(net.subnets(new_prefix=new_prefix))
    
    return [str(subnets[0]), str(subnets[1])]

def split_large_cidr(cidr, max_ips):
    """Recursively split CIDRs if their IPs exceed max_ips."""
    queue = [cidr]
    result = []

    while queue:
        current = queue.pop(0)
        n_ips = ips_in_cidr(current)
        if n_ips <= max_ips:
            result.append(current)
        else:
            # Split current CIDR into two halves and add back to queue
            parts = split_cidr(current)
            queue.extend(parts)
    
    return result

def split_cidr_file(input_file, max_ips_per_file=500_000):
    output_index = 1
    current_ips = 0
    output_lines = []
    total_ips_in_current_file = 0 # Keep track of total IPs for the current output file

    def write_output(lines, index, num_ips):
        # Modified filename to include the number of IPs
        filename = f"cidr_part_{index}_{num_ips}ips.txt" 
        with open(filename, 'w') as f_out:
            f_out.writelines(lines)
        print(f"Wrote {len(lines)} lines ({num_ips} IPs) to {filename}")

    with open(input_file, 'r') as f:
        for line in f:
            cidr = line.strip()
            if not cidr:
                continue

            # Possibly split large CIDR into smaller CIDRs
            cidr_blocks = split_large_cidr(cidr, max_ips_per_file)

            for block in cidr_blocks:
                n_ips = ips_in_cidr(block)

                if current_ips + n_ips > max_ips_per_file:
                    # Write current batch and reset
                    if output_lines:
                        write_output(output_lines, output_index, total_ips_in_current_file) # Pass total_ips_in_current_file
                        output_index += 1
                        current_ips = 0
                        total_ips_in_current_file = 0 # Reset total IPs for new file
                        output_lines = []

                output_lines.append(block + '\n')
                current_ips += n_ips
                total_ips_in_current_file += n_ips # Add to total IPs for the current file

        # Write any remaining lines left after the loop
        if output_lines:
            write_output(output_lines, output_index, total_ips_in_current_file) # Pass total_ips_in_current_file

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python split_cidr.py cidr.txt")
        sys.exit(1)

    input_file = sys.argv[1]
    split_cidr_file(input_file)
