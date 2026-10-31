#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void win() {
    printf("FLAG: CTF{pwn_th3_s3rv3r_g3t_th3_r00t}\n");
    fflush(stdout);
}

void vuln() {
    char buffer[64];
    printf("[+] Enter system diagnostic payload: ");
    fflush(stdout);
    gets(buffer); // Vulnerable function
}

int main() {
    vuln();
    return 0;
}
