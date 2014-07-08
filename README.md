papilio-clock
=============

Calculate clock settings for Papilio DCM/PLL timer system.
This is a Spartan6 FPGA.
Derived from http://www.xilinx.com/support/documentation/user_guides/ug382.pdf

Presents a basic GUI unless invoked with two args (in MHz).
E.g. papilio_clock 32 24.576

Basic GUI prompts for these values and displays as pictured.
The clocks are also printed to console or cmd line.
If invoked with two args - does not show GUI.

Currently only computes possibilities for one single, or two cascaded, DCMs.
PLLs may follow...