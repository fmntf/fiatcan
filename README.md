# dcan - Doblò CAN

This repo documents with Python3 code the findings documented on [Medium](https://medium.com/@fmntf) regarding the CAN frames that you can observe in a Fiat Doblò (263).

The goal is to reimplement the [Blue&Me](https://en.wikipedia.org/wiki/Blue%26Me) infotainment system, abandoned by FCA after the release of UConnect.

### Compatibility
Most of those information are valid for similar FCA cars equipped with Blue&Me, like Fiat Punto (199), Fiat Qubo (225), Fiat Panda (312), Alfa Romeo 147 (937), Alfa Romeo 159 (939), Alfa Romeo MiTo (955), etc. 

### Current State
Most of the infotainment related CAN frames have been decoded:

 * network wakeup / shutdown
 * PROXI validation
 * steering wheel buttons
 * Media Player, Voice, Phone, Navigation, FM radio audio channels
