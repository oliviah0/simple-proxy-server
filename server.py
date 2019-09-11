import socket
import sys
from _thread import start_new_thread

try:
    listening_port = int(input("[*] Enter a listening port number: "))
except KeyboardInterrupt:
    print("\n[*] Exiting...")
    sys.exit(0)

MAX_CONN = 15  # max connection of queues to hold
BUFFER_SIZE = 8192  # max socket buffer size


# MAIN PROGRAM
def start():
    '''
    Sets up socket, binds socket to port, and listens for incoming connections.
    When connection arrives from client, we accept/receive the client data (browser request). 
    We then dispatch the request in a separate thread, making us available for the next request.
    This allows us to handle multiple requests simultaneously which boosts the performance of the server multifold times.
    '''
   
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("[*] Initialized sockets successfully...")
       
        s.bind(('', listening_port))  # associate the socket the host and port
        print("[*] Sockets binded successfully...")
       
        s.listen(MAX_CONN)  # start listening for incoming connections
        print(f"[*] Server started successfully [{listening_port}]")

    except Exception as e:
        print("[*]", e)
        sys.exit(2)

    while 1:
        try:
            conn, addr = s.accept()  # accept connection from client
            data = conn.recv(BUFFER_SIZE)  # receive client data
            start_new_thread(conn_string, (conn, data, addr))  # start a thread

        except KeyboardInterrupt:
            s.close()
            print("\n[*] Shutting Down Proxy Server ...")
            sys.exit(1)
    s.close()


# RETRIEVE CONNECTION DETAILS
def conn_string(conn, data, addr):
    '''
    Retrieves destination address, host and port (if specified by client)
    in the received client data and calls proxy_server
    '''
   
    try:
        first_line = data.decode().split('\n')[0]
        url = first_line.split(' ')[1]

        http_pos = url.find("://")

        if http_pos == -1:
            temp = url
        else:
            # get the rest of the url
            temp = url[(http_pos + 3):] 
       
        # position of the port (if any)
        port_pos = temp.find(":")
       
        # find the end of the webserver
        webserver_pos = temp.find("/")
        if webserver_pos == -1:
            webserver_pos = len(temp)

        webserver = ""
        port = -1

        if port_pos == -1 or webserver_pos < port_pos:
            # default port
            port = 80
            webserver = temp[:webserver_pos]
        else:
            # specific port
            port = int(temp[(port_pos + 1):][:webserver_pos - port_pos - 1])
            webserver = temp[:port_pos]
      
        print(f"\n- URL: {url}\n- Webserver: {webserver}\n- Port: {port}\n- Addr: {addr}\n")
        proxy_server(webserver, port, conn, data, addr)
   
    except Exception as e:
        print("[*] ERROR: Could not retrieve connection details ...", e)


# MAKE CONNECTION TO END SERVER
def proxy_server(webserver, port, conn, data, addr):
    '''
    Create a new connection to the destination webserver.
    Sends the client's original request data to the desination webserver.
    Take the response received by the webserver and redirect to the client.
    ('conn' is the original connection to the client.)
    Lastly, closes the stream
    '''

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((webserver, port))
        s.send(data)

        while 1:
            # read/reply data to/from end web server
            reply = s.recv(BUFFER_SIZE)
            if len(reply) > 0:
                conn.send(reply)  # send reply back to client/browser

                dar = float(len(reply))
                dar = float(dar / 1024)
                dar = "{}.3s".format(dar)
                print(f"[*] Request Done: {addr[0]} => {dar} <= {webserver}")
            else:
                break

        # close server and client sockets
        s.close()
        conn.close()

    except OSError:
        s.close()
        conn.close()
        sys.exit(1)


start()
