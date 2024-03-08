#include <iostream>
#include <cstdio>
#include <ctime>
#include <cstdlib>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <cstring>
#include <string>
#include <openssl/evp.h>
#include <sstream>
#include <iomanip>

#include <zlib.h>

#include "def.h"

using namespace std;

int base = 1;
struct segment buffer_sgmt[257];
int buffer_filled[257];
int buffer_start = 1;
int buffer_end = 256;
int buffer_ct = 0;
string file = "";
int bytesRead = 0;

void setIP(char *dst, char *src){
    if(strcmp(src, "0.0.0.0") == 0 || strcmp(src, "local") == 0 || strcmp(src, "localhost") == 0){
        sscanf("127.0.0.1", "%s", dst);
    }
    else{
        sscanf(src, "%s", dst);
    }
    return;
}

string hexDigest(const void *buf, int len) {
    const unsigned char *cbuf = static_cast<const unsigned char *>(buf);
    ostringstream hx{};

    for (int i = 0; i != len; ++i)
        hx << hex << setfill('0') << setw(2) << (unsigned int)cbuf[i];

    return hx.str();
}

void SHA256(int flag){
    unsigned char hash[EVP_MAX_MD_SIZE];
    unsigned int hash_len;

    // make a SHA256 object and initialize
    EVP_MD_CTX *sha256 = EVP_MD_CTX_new();
    EVP_DigestInit_ex(sha256, EVP_sha256(), NULL);
    
    // update the object given a buffer and length
    // (here we add just one character per update)
    EVP_DigestUpdate(sha256, file.c_str(), bytesRead);

    // calculating hash
    // (we need to make a copy of `sha256` for EVP_DigestFinal_ex to use,
    // otherwise `sha256` will be broken)
    EVP_MD_CTX *tmp_sha256 = EVP_MD_CTX_new();
    EVP_MD_CTX_copy_ex(tmp_sha256, sha256);
    EVP_DigestFinal_ex(tmp_sha256, hash, &hash_len);
    EVP_MD_CTX_free(tmp_sha256);
    
    // print hash
    string s = hexDigest(hash,hash_len);
    if(flag == 0) printf("sha256\t%d\t%s\n", bytesRead, s.c_str());
    if(flag == 1) printf("finsha\t%s\n", s.c_str());
    //cout << "sha256(\"" << str.substr(0, s_i + 1) << "\") = " << hexDigest(hash, hash_len) << endl;
    EVP_MD_CTX_free(sha256);
}

void flush(){
    printf("flush\n");
    for(int i=1;i<=buffer_ct;i++){
        file += std::string(buffer_sgmt[i].data, buffer_sgmt[i].head.length);;
        bytesRead += buffer_sgmt[i].head.length;
    }
    SHA256(0);

    bzero(buffer_sgmt, sizeof(buffer_sgmt));
    bzero(buffer_filled, sizeof(buffer_filled));
    buffer_start += 256;
    buffer_end += 256;
    buffer_ct = 0;
}

void updateBuffer(struct segment recv_sgmt){
    if(buffer_filled[(recv_sgmt.head.seqNumber-1)%256+1] == 0){
        buffer_sgmt[(recv_sgmt.head.seqNumber-1)%256+1] = recv_sgmt;
        buffer_filled[(recv_sgmt.head.seqNumber-1)%256+1] = 1;
        buffer_ct += 1;
    }
}

void updateBase(){
    base += 1;
    while(1){
        if(base > buffer_end){
            base = buffer_sgmt[256].head.seqNumber + 1;
            break;
        }
        else if(buffer_filled[(base-1) % 256 + 1] == 0){
            base = buffer_sgmt[(base-1) % 256].head.seqNumber + 1;
            break;
        }
        else base += 1;
    }
}

void sendSack(int ackNumber, int sackNumber, int sock_fd, struct sockaddr_in recv_addr){
    struct segment sgmt;
    sgmt.head.ackNumber = ackNumber;
    sgmt.head.sackNumber = sackNumber;
    sgmt.head.ack = 1;
    sgmt.head.fin = 0;
    
    sendto(sock_fd, &sgmt, sizeof(sgmt), 0, (struct sockaddr *)&recv_addr, sizeof(sockaddr));
    printf("send\tack\t#%d,\tsack\t#%d\n", sgmt.head.ackNumber, sgmt.head.sackNumber);
}

// ./receiver <recv_ip> <recv_port> <agent_ip> <agent_port> <dst_filepath>
int main(int argc, char *argv[]) {
    // parse arguments
    if (argc != 6) {
        cerr << "Usage: " << argv[0] << " <recv_ip> <recv_port> <agent_ip> <agent_port> <dst_filepath>" << endl;
        exit(1);
    }

    int recv_port, agent_port;
    char recv_ip[50], agent_ip[50];

    // read argument
    setIP(recv_ip, argv[1]);
    sscanf(argv[2], "%d", &recv_port);

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
    addr.sin_port = htons(recv_port);
    addr.sin_addr.s_addr = inet_addr(recv_ip);
    memset(addr.sin_zero, '\0', sizeof(addr.sin_zero));    
    bind(sock_fd, (struct sockaddr *)&addr, sizeof(addr));
    
    bzero(buffer_filled, sizeof(buffer_filled));
    while(1){
        socklen_t recv_addr_sz;
        struct segment recv_sgmt;
        struct segment sgmt;
        if(recvfrom(sock_fd, &recv_sgmt, sizeof(recv_sgmt), 0, (struct sockaddr *)&recv_addr, &recv_addr_sz) > 0){
            if(recv_sgmt.head.fin == 1){ //get fin
                printf("recv\tfin\n");
                sgmt.head.length = 0;
                sgmt.head.ack = 1;
                sgmt.head.fin = 1;
                sendto(sock_fd, &sgmt, sizeof(sgmt), 0, (struct sockaddr *)&recv_addr, sizeof(sockaddr));
                printf("send\tfinack\n");
                flush();
                break;
            }
            unsigned int recv_data_checksum = crc32(0L, (const Bytef *)recv_sgmt.data, MAX_SEG_SIZE);
            if(recv_sgmt.head.checksum != recv_data_checksum){ //corrupt
                printf("drop\tdata\t#%d\t(corrupted)\n", recv_sgmt.head.seqNumber);
                sendSack(base - 1, base - 1, sock_fd, recv_addr);
                continue;
            }
            if(!(recv_sgmt.head.seqNumber >= buffer_start && recv_sgmt.head.seqNumber <= buffer_end)){ //out buffer range
                printf("drop\tdata\t#%d\t(buffer overflow)\n", recv_sgmt.head.seqNumber);
                sendSack(base - 1, base - 1, sock_fd, recv_addr);
                continue;
            }
            
            if(recv_sgmt.head.seqNumber == base){
                updateBuffer(recv_sgmt);
                updateBase();
                printf("recv\tdata\t#%d\t(in order)\n", recv_sgmt.head.seqNumber);
                sendSack(base-1, recv_sgmt.head.seqNumber, sock_fd, recv_addr);
                if(buffer_ct >= 256) flush();
            }
            else{
                if(!(recv_sgmt.head.seqNumber >= buffer_start && recv_sgmt.head.seqNumber <= buffer_end)){
                    printf("recv\tdata\t#%d\t(out of order, sack-ed)\n", recv_sgmt.head.seqNumber);
                    sendSack(base-1, base-1, sock_fd, recv_addr);
                }
                else{
                    updateBuffer(recv_sgmt);
                    printf("recv\tdata\t#%d\t(out of order, sack-ed)\n", recv_sgmt.head.seqNumber);
                    sendSack(base-1, recv_sgmt.head.seqNumber, sock_fd, recv_addr);
                }
            }
        }
    }
    SHA256(1);
    FILE* outFile = fopen(filepath, "w");
    fwrite(file.c_str(), 1, bytesRead, outFile);
    fclose(outFile);
    return 0;
}