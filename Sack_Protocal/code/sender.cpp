#include <iostream>
#include <cstdio>
#include <cstdlib>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <cstring>
#include <fcntl.h>
#include <sys/stat.h>
#include <vector>
#include <map>
#include <algorithm>
#include <zlib.h>
#include <sys/time.h>
#include <sys/select.h>
#include <unistd.h>
#include <chrono>
#include <thread>

#include "def.h"

using namespace std;

double cwnd = 1;
int thresh = 16;
int dup_ack = 0;
int base = 1;
int state = 0; //0:slow start; 1:congestion
int cur_seq = 1;
int cwnd_sended = 0;
int *entered_window;

vector<int> window;
vector<struct segment> transmit_queue;

void setIP(char *dst, char *src){
    if(strcmp(src, "0.0.0.0") == 0 || strcmp(src, "local") == 0 || strcmp(src, "localhost") == 0){
        sscanf("127.0.0.1", "%s", dst);
    }
    else{
        sscanf(src, "%s", dst);
    }
    return;
}

void markSACK(int erase_sacknum){
    if(erase_sacknum < transmit_queue[0].head.seqNumber) return;
    auto it = std::find_if(transmit_queue.begin(), transmit_queue.end(),
            [erase_sacknum](const segment& element) {
                return element.head.seqNumber == erase_sacknum;
            });
    if(it != transmit_queue.end()){
        transmit_queue.erase(it);
        cwnd_sended -= 1;
    }
}

void transmitFin(int sock_fd, struct sockaddr_in recv_addr){
    struct segment sgmt;
    sgmt.head.length = 0;
    sgmt.head.seqNumber = cur_seq;
    sgmt.head.ack = 0;
    sgmt.head.fin = 1;
    sendto(sock_fd, &(sgmt), sizeof(sgmt), 0, (struct sockaddr *)&recv_addr, sizeof(sockaddr));
    printf("send\tfin\n");
}

void transmitNew(int sock_fd, struct sockaddr_in recv_addr){
    while(cwnd_sended < int(cwnd) && cwnd_sended < transmit_queue.size()){
        int index = cwnd_sended;
        sendto(sock_fd, &(transmit_queue[index]), sizeof(transmit_queue[index]), 0, (struct sockaddr *)&recv_addr, sizeof(sockaddr));
        if(entered_window[transmit_queue[index].head.seqNumber] == 0){
            printf("send\tdata\t#%d,\twinSize = %d\n", transmit_queue[index].head.seqNumber, int(cwnd));
            entered_window[transmit_queue[index].head.seqNumber] = 1;
        }
        else printf("resnd\tdata\t#%d,\twinSize = %d\n", transmit_queue[index].head.seqNumber, int(cwnd));
        
        cur_seq += 1;
        cwnd_sended += 1;
    }
}

// ./sender <send_ip> <send_port> <agent_ip> <agent_port> <src_filepath>
int main(int argc, char *argv[]){
    // parse arguments
    if (argc != 6) {
        cerr << "Usage: " << argv[0] << " <send_ip> <send_port> <agent_ip> <agent_port> <src_filepath>" << endl;
        exit(1);
    }

    int send_port, agent_port;
    char send_ip[50], agent_ip[50];

    // read argument
    setIP(send_ip, argv[1]);
    sscanf(argv[2], "%d", &send_port);

    setIP(agent_ip, argv[3]);
    sscanf(argv[4], "%d", &agent_port);

    char *filepath = argv[5];

    // make socket related stuff
    int sock_fd = socket(PF_INET, SOCK_DGRAM, 0);

    struct sockaddr_in recv_addr;
    recv_addr.sin_family = AF_INET;
    recv_addr.sin_port = htons(agent_port);
    recv_addr.sin_addr.s_addr = inet_addr(agent_ip);

    struct sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_port = htons(send_port);
    addr.sin_addr.s_addr = inet_addr(send_ip);
    memset(addr.sin_zero, '\0', sizeof(addr.sin_zero));    
    bind(sock_fd, (struct sockaddr *)&addr, sizeof(addr));

    int fd = open(filepath, O_RDONLY);
    char buffer[MAX_SEG_SIZE];
    ssize_t bytesRead;
    int ct = 1;
    while(1){
        struct segment sgmt;
        bzero(sgmt.data, sizeof(char) * MAX_SEG_SIZE);
        if((bytesRead = read(fd, sgmt.data, MAX_SEG_SIZE)) <= 0) break;

        sgmt.head.length = bytesRead;
        sgmt.head.seqNumber = ct;
        sgmt.head.ack = 0;
        sgmt.head.fin = 0;
        sgmt.head.checksum = crc32(0L, (const Bytef *)sgmt.data, MAX_SEG_SIZE);
        transmit_queue.push_back(sgmt);
        ct += 1;
    }
    entered_window = new int[ct+1];
    bzero(entered_window, sizeof(int)*(ct+1));
    

    transmitNew(sock_fd, recv_addr);
    auto start_time = std::chrono::steady_clock::now();
    state = 0;
    while(1){
        struct segment sgmt;
        socklen_t recv_addr_sz;

        fd_set readFds;
        FD_ZERO(&readFds);
        FD_SET(sock_fd, &readFds);

        int result;
        auto end_time = std::chrono::steady_clock::now();
        std::chrono::duration<double> elapsed_time = (end_time - start_time);
        double remainingTime = double(1) - elapsed_time.count();
        if(remainingTime <= 0){
            result = 0;
        }
        else{
            struct timeval timeout;
            timeout.tv_sec = int(remainingTime);
            timeout.tv_usec = int((remainingTime-int(remainingTime)) * 1000000);
            result = select(sock_fd + 1, &readFds, nullptr, nullptr, &timeout);
        }
        
        if(result <= 0){ //timeout
            thresh = max(1, int(cwnd / 2));
            cwnd_sended = 1;
            cwnd = 1;
            dup_ack = 0;
            printf("time\tout,\tthreshold = %d,\twinSize = %d\n", thresh, int(cwnd));
            sendto(sock_fd, &transmit_queue[0], sizeof(transmit_queue[0]), 0, (struct sockaddr *)&recv_addr, sizeof(sockaddr)); 
            printf("resnd\tdata\t#%d,\twinSize = %d\n", transmit_queue[0].head.seqNumber, int(cwnd));
            start_time = std::chrono::steady_clock::now();
            state = 0;
        }
        else{ 
            recvfrom(sock_fd, &sgmt, sizeof(sgmt), 0, (struct sockaddr *)&recv_addr, &recv_addr_sz);
            //printf("head:%d %d %d\n",sgmt.head.ack, sgmt.head.ackNumber, sgmt.head.sackNumber);
            if(sgmt.head.fin == 1){
                printf("recv\tfinack\n");
                break;
            }
            else if(sgmt.head.ack == 1){
                printf("recv\tack\t#%d,\tsack\t#%d\n", sgmt.head.ackNumber, sgmt.head.sackNumber);
                //if(sgmt.head.sackNumber < transmit_queue[0].head.sackNumber && sgmt.head.ackNumber == sgmt.head.sackNumber) cwnd_sended -= 1;
                if(sgmt.head.ackNumber < base){ //dup ack
                    dup_ack += 1;
                    markSACK(sgmt.head.sackNumber);
                    if(transmit_queue.size() == 0){
                        transmitFin(sock_fd, recv_addr);
                        break;
                    }
                    transmitNew(sock_fd, recv_addr);
                    if(dup_ack == 3){
                        //transmitMissing
                        sendto(sock_fd, &transmit_queue[0], sizeof(transmit_queue[0]), 0, (struct sockaddr *)&recv_addr, sizeof(sockaddr)); 
                        printf("resnd\tdata\t#%d,\twinSize = %d\n", transmit_queue[0].head.seqNumber, int(cwnd));
                    }
                }
                else{ //new ack
                    dup_ack = 0;
                    markSACK(sgmt.head.sackNumber);
                    base = transmit_queue[0].head.seqNumber;
                    if(transmit_queue.size() == 0){
                        transmitFin(sock_fd, recv_addr);
                        break;
                    }
                    if(state == 0){
                        cwnd += 1;
                        if(cwnd >= thresh) state = 1;
                    }
                    else if(state == 1){
                        cwnd += double(1) / int(cwnd);
                    }
                    transmitNew(sock_fd, recv_addr);
                    start_time = std::chrono::steady_clock::now();
                }
                
            }
        }
    }
    while(1){
        struct segment sgmt;
        socklen_t recv_addr_sz;
        if(recvfrom(sock_fd, &sgmt, sizeof(sgmt), 0, (struct sockaddr *)&recv_addr, &recv_addr_sz) > 0){
            if(sgmt.head.fin == 1){ //fin == 1
                printf("recv\tfinack\n");
                break;
            }
        }
    }
    return 0;
}