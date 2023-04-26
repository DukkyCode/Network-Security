import sys
import socket
import time
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
        print "Error resolving hostname: ", e
    
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
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.connect((host, port))

            #Setting the value of the dictionary
            ports_open[port] = 0
            ports_open[port] = socket.getservbyport(port, 'tcp')

            #Closing the server
            server.close()

        #If getservbyport() raise an exception
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
        print str(element[0]) + ' (' + str(element[1]) + ') was open'

    print 'time elapsed = ' + str(elapsed_time) + 's'
    print 'time per scan = ' + str(scan_rate) + 's'

    #Write to scanner.txt
    with open('scanner.txt', 'w') as file:
        for element in sorted_ports:
            file.write(str(element[0]) + ' (' + str(element[1]) + ') was open\n')

        file.write('time elapsed = ' + str(elapsed_time) + 's\n')
        file.write('time per scan = ' + str(scan_rate) + 's\n')          
