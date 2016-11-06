#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdio.h>


int main(void)
{
    int d = 5;
    int h = 3;
    int m = 20;
    int s = 15;
    int h2 = 22;
    int m2 = 50;
    int s2 = 50;
    long e = d*(24*3600)+ h*3600 + m*60 +s;
    int cs, cm;
    printf("e: %i\r\n", e);
    int x = (55 + 10)/60;
    printf("x: %d\r\n", x);
    //s = e%60; e /= 60;
    //m = e%60; e /= 60;
    //h = e%24; e /= 24;
    //d = e;
    //printf("d: %d, h: %d, m: %d, s: %d\r\n", d, h, m, s);
    cs = (s2 + s)/60; s = (s2 + s)%60; 
    printf("cs: %d\r\n", cs);
    cm = (m2 + m + cs)/60; m = (m2 + m + cs)%60; 
    printf("cm: %d\r\n", cm);
    h = (h2 + h + cm)%24;
    printf("d: %d, h: %d, m: %d, s: %d\r\n", d, h, m, s);
}
