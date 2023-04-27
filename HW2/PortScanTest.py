from scapy.all import *
import argparse

# Main Function
if __name__ == '__main__':

    #Argument Handler
    parser = argparse.ArgumentParser(description= 'Usage: python PortScan.py target')
    parser.add_argument(dest='target', type=str, help="Target IP Address")
    args = parser.parse_args()

    #Get the target hostname
    try:
        host = socket.gethostbyname(args.target)
    #If the hostname is invalid
    except socket.gaierror as error:
        print("Error resolving hostname: %s", error)

    #Create a dictionary for the opened port
    ports_open = {}

    #Initialize port min and max
    port_min = 0
    port_max = 65535

    #Record the start time
    start_time = time.time()

    #Bind Socket with all of the ports and append to the port array
    for port in range(port_min, port_max + 1):
        try:
            # Create IP layer with spoofed source address
            ip = IP(src='192.68.1.1', dst=host)

            # Create TCP layer with the desired port
            tcp = TCP(sport=RandShort(), dport=port, flags='S')

            # Combine the layers into a packet and send it
            packet = ip / tcp
            response = sr1(packet, timeout=1, verbose=0)

            # If the response is a SYN/ACK packet, the port is open
            if response:
                print("Port is open")
                ports_open[port] = 0
                ports_open[port] = socket.getservbyport(port, 'tcp')
            else:
                print("Port is not open")
        except socket.error:
            pass

    #Record the end time
    end_time = time.time()

    #Calculated the Elapsed Time
    elapsed_time = end_time - start_time

    #Calculate time per scan
    scan_rate = elapsed_time / port_max

    #Post procesing the dictionary
    for key in ports_open:
        if ports_open[key] == 0:
            ports_open[key] = 'NA'

    #Sorted the Element
    sorted_ports = sorted(ports_open.items())

    #Print and pipe to the txt file
    for element in sorted_ports:
        print(str(element[0]) + ' (' + str(element[1]) + ') was open')

    print ('time elapsed = ' + str(elapsed_time) + 's')
    print ('time per scan = ' + str(scan_rate) + 's')

    #Write to scanner.txt
    with open('scanner.txt', 'w') as file:
        for element in sorted_ports:
            file.write(str(element[0]) + ' (' + str(element[1]) + ') was open\n')

        file.write('time elapsed = ' + str(elapsed_time) + 's\n')
        file.write('time per scan = ' + str(scan_rate) + 's\n')
