import dpkt 
import pcap
import sys
import socket
import signal

#Global variables
consecutive_ports = 15  #15+ consecutive ports
time_window = 300       #5 minute time window

#Function handler for exit
def handler(sig, frame):
    print 'Terminating the Program'
    sys.exit(0)

# Main Function
if __name__ == '__main__':
    #Declare interface
    interface = 'lo'
    syn_flags = 2
    ip_counts = {}                      #Dictionary to store value of the IP address being accessed 
    ip_detected = []

    #Listen to packets
    packets = pcap.pcap(interface)
    packets.setfilter('tcp')

    for timestamp, buffer in packets:
        #Parsing the packets
        eth = dpkt.ethernet.Ethernet(buffer)
        ip = eth.data
        tcp = ip.data
        
        #If the SYN flags are being set
        if tcp.flags & syn_flags:
            #Get the source IP address
            ip_src_addr = socket.inet_ntoa(ip.src)

            #If the IP source address is not in the list
            if ip_src_addr not in ip_counts:
                #Initialize all the data in our data structure
                ip_counts[ip_src_addr] = {
                    'count': 0,
                    'last_port': tcp.dport,
                    'intial_timestamp': timestamp,
                    'current_timestamp': timestamp,
                }

            else:
                #If the current TCP port is not a consecutive port from the last port
                if tcp.dport != ip_counts[ip_src_addr]['last_port'] + 1:
                    if ip_counts[ip_src_addr]['count'] > 0:
                        ip_counts[ip_src_addr]['count'] -= 1

                else:
                    #Increment the consecutive count by 1
                    ip_counts[ip_src_addr]['count'] += 1

                    #If the consecutive ports is larger than 15 and within the 5 minute window
                    if ip_counts[ip_src_addr]['count'] >= consecutive_ports and timestamp - ip_counts[ip_src_addr]['intial_timestamp'] <= time_window:     
                        if ip_src_addr not in ip_detected:
                            ip_detected.append(ip_src_addr)
                            print 'Scanner detected. The scanner originated from host ', ip_src_addr
                            #Write back to a txt file
                            with open('detector.txt', 'w') as file:
                                file.write('Scanner detected. The scanner originated from host ' + ip_src_addr + '\n')

                #Update the value of our data structure
                ip_counts[ip_src_addr]['last_port'] = tcp.dport
                ip_counts[ip_src_addr]['current_timestamp'] = timestamp

    #Handler to terminate the program when press CTRL-C
    signal.signal(signal.SIGINT, handler)




















