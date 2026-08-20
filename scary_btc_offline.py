import threading
import requests
from mnemonic import Mnemonic
from embit.bip32 import HDKey
from embit.script import p2wpkh
import time
from requests.exceptions import ConnectionError
import json
import os

# Configuration - Add your target addresses here
CONFIG_ADDRESSES = [
    "bc1qa5wkgaew2dkv56kfvj49j0av5nml45x9ek9hz6",  # Example address 1
    "bc1q7ydrtdn8z62xhslqyqtyt38mm4e2c4h3mxjkug",
    "bc1qjh0akslml59uuczddqu0y4p3vj64hg5mc94c40",
      # Example address 2
    # Add more addresses as needed
]

# Function to read a random 12-word mnemonic from a wordlist file
def get_random_mnemonic():
    mnemo = Mnemonic("english")
    mnemonic = mnemo.generate(strength=128)
    return mnemonic

# Function to generate addresses from a given mnemonic
def generate_addresses_from_mnemonic(mnemonic, num_addresses=1):
    # Create a BIP32 root key from the mnemonic
    seed = Mnemonic.to_seed(mnemonic)
    root_key = HDKey.from_seed(seed)

    # Derive the BIP32 key from the root key
    key = root_key.derive("m/84'/0'/0'")  # BIP84 derivation path

    # Generate and store the addresses
    addresses = []
    for i in range(num_addresses):
        # Derive the child key at the specified index
        child_key = key.derive([0, i])  # 0 for external chain
        
        # Get the address from the child key
        address = p2wpkh(child_key).address()
        addresses.append(address)

    return addresses

def check_address_balance(address):
    url = f"https://blockchain.info/q/getreceivedbyaddress/{address}"
    while True:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                # Convert the balance to an integer before returning
                return int(response.text)
            else:
                return f"Error: Unable to fetch balance. Status code: {response.status_code}"
        except ConnectionError as e:
            print(f"Connection error occurred: {e}. Retrying in 5 seconds...")
            time.sleep(5)

# Function to check if any generated address matches the config addresses
def check_address_match(generated_addresses, mnemonic):
    matched_addresses = []
    for address in generated_addresses:
        if address in CONFIG_ADDRESSES:
            matched_addresses.append(address)
    
    if matched_addresses:
        # Save matched addresses along with mnemonic
        save_matched_addresses(mnemonic, matched_addresses)
        return True
    return False

# Function to save matched addresses and mnemonics to file
def save_matched_addresses(mnemonic, matched_addresses):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    with open("matched_addresses.txt", "a") as file:
        file.write(f"Time Found: {timestamp}\n")
        file.write(f"Mnemonic: {mnemonic}\n")
        file.write("Matched Addresses:\n")
        for address in matched_addresses:
            file.write(f"  - {address}\n")
        file.write("-" * 50 + "\n\n")

# Function to generate addresses in offline mode
def generate_addresses_offline(num_threads=1):
    def generate_addresses_thread():
        count = 0
        while True:
            mnemonic = get_random_mnemonic()
            print(f"\nCurrent Time: {time.strftime('%Y-%m-%d %H:%M:%S')} | Mnemonic: {mnemonic}\n")
            
            # Generate addresses from the mnemonic
            addresses = generate_addresses_from_mnemonic(mnemonic)
            
            # Check if any address matches the config
            if check_address_match(addresses, mnemonic):
                print(f"✅ MATCH FOUND! Addresses matched with config!")
                for addr in addresses:
                    if addr in CONFIG_ADDRESSES:
                        print(f"  - {addr}")
            else:
                print(f"No matches found for this mnemonic.")
            
            count += 1
            print(f"Total checked: {count}")

    # Create and start threads
    threads = []
    for _ in range(num_threads):
        thread = threading.Thread(target=generate_addresses_thread)
        thread.start()
        threads.append(thread)
    
    # Wait for all threads to finish
    for thread in threads:
        thread.join()

# Function to generate addresses in online mode
def generate_addresses_online(num_threads=1):
    def generate_addresses_thread():
        count = 0
        while True:
            # Get a random 12-word mnemonic
            mnemonic = get_random_mnemonic()
            print(f"\nCurrent Time: {time.strftime('%Y-%m-%d %H:%M:%S')} | Mnemonic: {mnemonic}\n")
            
            # Generate addresses from the mnemonic
            addresses = generate_addresses_from_mnemonic(mnemonic)
            
            # Check balance for each address and save if non-zero
            for address in addresses:
                balance = check_address_balance(address)
                if balance > 0:
                    print(f"💰 Address {count+1}: {address} has a balance of {balance} satoshis.")
                    # Save the mnemonic, address, and balance to a text file
                    with open("addresses_with_balance.txt", "a") as file:
                        file.write(f"Current Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                        file.write(f"Mnemonic: {mnemonic}\n")
                        file.write(f"Address: {address}\n")
                        file.write(f"Balance: {balance} satoshis\n\n")
                else:
                    print(f"Address {count+1}: {address} has a balance of 0 satoshis.")
                
                # Also check if address matches config addresses
                if address in CONFIG_ADDRESSES:
                    print(f"🎯 MATCH FOUND! Address {address} matches config!")
                    with open("matched_addresses.txt", "a") as file:
                        file.write(f"Current Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                        file.write(f"Mnemonic: {mnemonic}\n")
                        file.write(f"Matched Address: {address}\n")
                        file.write(f"Balance: {balance} satoshis\n")
                        file.write("-" * 50 + "\n\n")
                
                count += 1

    # Create and start threads
    threads = []
    for _ in range(num_threads):
        thread = threading.Thread(target=generate_addresses_thread)
        thread.start()
        threads.append(thread)
    
    # Wait for all threads to finish
    for thread in threads:
        thread.join()

# Main function to ask user for mode
def main():
    print("=" * 50)
    print("Bitcoin Address Generator & Checker")
    print("=" * 50)
    print("\nSelect mode:")
    print("1. Online - Check balances of all addresses")
    print("2. Offline - Match addresses with config addresses only")
    
    while True:
        choice = input("\nEnter your choice (1 or 2): ").strip()
        if choice in ['1', '2']:
            break
        print("Invalid choice. Please enter 1 or 2.")
    
    num_threads = int(input("Enter the number of threads: "))
    
    print(f"\nConfig Addresses to match: {len(CONFIG_ADDRESSES)} addresses")
    print("=" * 50)
    
    if choice == '1':
        print("Starting ONLINE mode - Checking balances for all addresses...")
        generate_addresses_online(num_threads)
    else:
        print("Starting OFFLINE mode - Matching addresses with config only...")
        generate_addresses_offline(num_threads)

# Run the main function
if __name__ == "__main__":
    main()