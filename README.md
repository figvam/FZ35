# FZ35
Python-Frontend for the FZ35 (5A 35W Electronic Load Tester)

# Atorch UD18
UD18.py - frontend for Atorch UD18 USB Electronic Tester

Based on reverse engineered protocol by **msillano**:
- https://github.com/msillano/UD18-protocol-and-node-red
- [Proprietary Atorch protocol description](https://github.com/msillano/UD18-protocol-and-node-red/blob/master/UD18_protocol.txt)

Usage:
```
    rfcomm bind /dev/rfcomm0 XX:XX:XX:XX:XX:XX
    # where XX:XX:XX:XX:XX:XX is the Bluetooth MAC address of UD18 tester
    ./UD18.py /dev/rfcomm0
```
