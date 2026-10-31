#include <stdio.h>
#include <stdlib.h>

void win() {
    printf("FLAG: CTF{pwn_lntu_st4ck_0v3rfl0w_r00t}\n");
    fflush(stdout);
}

void vuln() {
    char buffer[64];
    printf("[+] Введіть службовий токен авторизації: ");
    fflush(stdout);
    gets(buffer);
}

int main() {
    vuln();
    return 0;
}
