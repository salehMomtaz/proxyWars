import json

# Read ips from file
with open("ips.txt", "r") as f:
    ips = [line.strip() for line in f if line.strip()]

# Create the structure
data = {
    "version": "1.0",
    "servers": [{"ip": ip} for ip in ips]
}

# Write to ips.json
with open("ips.json", "w") as f:
    json.dump(data, f, indent=2)

print("ips.json created successfully.")
