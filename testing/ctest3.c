#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdio.h>


int main(void)
{
    uint8_t test[32] = "ABCDEF";
    uint8_t test2[32];
    int i;
    int8_t rssi;
    uint8_t tmp = 0;
    uint8_t* data = malloc(6);
    uint8_t             node_id[]               = {0x01, 0x02, 0x03, 0x04};
    uint8_t data2[6];

    strcpy(test2, "ABC");
    printf("test %s, test2: %s\r\n", test, test2);
    i = strncmp(test+1, "BC", 2);
    printf("i=2: %d\r\n", i);
    i = strncmp(test, test2, 3);
    printf("i=3: %d\r\n", i);
    i = strncmp(test, test2, 4);
    printf("i=4: %d\r\n", i);

    rssi = -41;
    memcpy(data, node_id, 4);
    memcpy(data+4, &tmp, 1);
    memcpy(data+5, &rssi, 1);
    printf("data: %d %d %d %d %d %d\r\n", data[0], data[1], data[2], data[3], data[4], data[5]);
    for(i=0; i<4; i++)
        data2[i] = node_id[i];
    data2[4] = tmp;
    data2[5] = rssi;
    printf("data2: %d %d %d %d %d %d\r\n", data2[0], data2[1], data2[2], data2[3], data2[4], data2[5]);
}
