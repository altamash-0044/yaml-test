from netmiko import ConnectHandler
import concurrent.futures
import csv
import datetime  # Standard module for dates and times
import os

# 1. Function to read your custom CSV inventory file
def load_switches():
    switch_list = []
    inventory_file = r'C:\Switch_Backups\switches.csv'
    
    if not os.path.exists(inventory_file):
        print(f"Error: Can't find '{inventory_file}'.")
        return []
        
    with open(inventory_file, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            row['global_delay_factor'] = 2
            switch_list.append(row)
    return switch_list

# 2. Worker function that handles a single switch task
def backup_switch(switch):
    ip = switch['ip']
    print(f"[Starting] Connecting to {ip}...")
    
    # Get current date and time formatted safely for Windows filenames ---
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # -----------------------------------------------------------------------------
    
    try:
        connection = ConnectHandler(**switch, fast_cli=False)
        
        
        # Download the running config
        config = connection.send_command("show running-config")
        
        # --- NEW: Filename now includes the timestamp variable ---
        filename = f"backup_{ip}_{timestamp}.txt"
        # ---------------------------------------------------------
        
        full_path = os.path.join(r"C:\Switch_Backups", filename)
        with open(full_path, "w") as f:
            f.write(config)
        print(f"[PROGRESS] Saved local text file for {ip}")
            
        # Save configuration permanently on the switch hardware itselfs
        print(f"[PROGRESS] Saving configuration permanently on switch memory for {ip}...")
        output = connection.send_command_timing("copy running-config startup-config")
        if "Destination filename" in output:
            output += connection.send_command_timing("\n")
        
        connection.disconnect()
        return f"[SUCCESS] {ip} backup and write completed."
        
    except Exception as e:
        return f"[FAILED] {ip} encountered an error: {e}"

# 3. Main execution loop
def main():
    if not os.path.exists(r"C:\Switch_Backups"):
        os.makedirs(r"C:\Switch_Backups")
        
    switches = load_switches()
    if not switches:
        return
        
    print(f"Loaded {len(switches)} switches from inventory. Starting simultaneous execution...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(backup_switch, sw) for sw in switches]
        for future in concurrent.futures.as_completed(futures):
            print(future.result())

if __name__ == "__main__":
    main()
