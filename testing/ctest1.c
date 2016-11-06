#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdio.h>

#define COUNTOF(x)          (sizeof(x) / sizeof((x)[0]))
#define TXBUFFERSIZE        (COUNTOF(aTxBuffer) - 1)
#define RXBUFFERSIZE        8
#define ARRAY_CONCAT(TYPE, A, An, B, Bn) \
  (TYPE *)array_concat((const void *)(A), (An), (const void *)(B), (Bn), sizeof(TYPE));

#define BEACON_ADDRESS      0xBBBB
#define GRANT_ADDRESS       0xBB00

// Function codes:
#define  include_req        0x00
#define  s_include_req      0x01
#define  include_grant      0x02
#define  reinclude          0x04
#define  config             0x05
#define  send_battery       0x06
#define  alert              0x09
#define  woken_up           0x07
#define  ack                0x08
#define  beacon             0x0A



static void Error_Handler(uint8_t error)
//static void Error_Handler(void)
{
  //printf("Error Handler, *error: %d, error: %d\r\n", *error, error);
  printf("Error Handler, error: %d\r\n", error);
  int i;
  uint8_t *buffer = malloc(20*sizeof(uint8_t));
  //memcpy(buffer, "Error: ", 7);
  //memcpy(buffer + 14, &error, 1);
  memcpy(buffer, &error, 1);
  //memcpy(buffer + 8, ".\r\n", 2);
  printf("Error handler buffer:\r\n");
  for (i=0; i<20; i++)
  {
    printf("%c", buffer[i]);
  }
  printf("\r\n");
}

int main(void)
{
  typedef enum {initial, normal, pressed, search, search_failed, reverting} NodeState;
  NodeState         nodeState           = search; 
  uint16_t          bridgeAddress       = 0;
  uint8_t           test2[]             = "Test2\r\n";
  uint8_t           test3[20];
  static uint16_t   destination;
  static uint16_t   source;
  static uint16_t   wakeup;
  static uint8_t    function;
  static uint8_t    length;
  static uint8_t    nodeAddress         = 0;
  static uint8_t    *payload;

  memcpy(test3, "TestA", 5);
  memcpy(test3 + 5, test2, 7);
  printf("test3: %s \r\n", test3);
  static uint8_t err = 5;
  Error_Handler(err);
  uint8_t buffer[] = {0xBB, 0xBB, 3, 4, 5, 10, 0x00, 0x10, 0x0a, 0x0b};
  destination = (buffer[0] << 8) | buffer[1];
  if ((destination == nodeAddress) || (destination == BEACON_ADDRESS) || (destination == GRANT_ADDRESS))
  {      
    source = (buffer[2] << 8) | buffer[3];
    function = buffer[4];
    length = buffer[5];
    printf("header: %04X, %04X, %02X, %02x\r\n", destination, source, function, length);
    if (length > 6)
        wakeup = (buffer[6] << 8) | buffer[7];
    else
        wakeup = 0;
    printf("wakeup: %04X\r\n", wakeup);
    if (length > 8)
    {
        payload = buffer + 8;
        printf("payload: %04X\r\n", *payload);
    }
    if (function == beacon)
    {
        //manageSend;
        if (nodeState == search)
        {
            bridgeAddress = source;
            nodeState = include_req;
            //sendRadio(include_req, NODE_ID);
            //setDisplay(connecting);
        }
    }
    else if (function == include_grant)
    {
        nodeState = normal;
        //setDisplay(m1);
        //onIncludeGrant(payload);
        //sendRadio(ack);
    }
    else if (function == config)
    {
        //onConfig(payload);
        //sendRadio(ack);
    }
    else if (function == send_battery)
    {
        //sendBattery;
    }
    else if (function == ack)
    {
        //acknowledged();
    }
    else
    {
    }
    //if (function != beacon)
    //    setWakeup(wakeup);
  }
}
