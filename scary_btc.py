import threading
import requests
from mnemonic import Mnemonic
from embit.bip32 import HDKey
from embit.script import p2wpkh
import time
from requests.exceptions import ConnectionError

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

# Function to generate addresses infinitely with threading
def generate_addresses_infinite(num_threads=1):
    # Function to generate addresses and check balances
    def generate_addresses_thread():
        count = 1
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
                    print(f"Address {count}: {address} has a balance of {balance} satoshis.")
                    # Save the mnemonic, address, and balance to a text file
                    with open("addresses_with_balance.txt", "a") as file:
                        file.write(f"Current Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                        file.write(f"Mnemonic: {mnemonic}\n")
                        file.write(f"Address: {address}\n")
                        file.write(f"Balance: {balance} satoshis\n\n")
                else:
                    print(f"Address {count}: {address} has a balance of 0 satoshis.")
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

# Ask the user for the number of threads
num_threads = int(input("Enter the number of threads: "))

# Call the function to start generating addresses infinitely with threading
generate_addresses_infinite(num_threads)