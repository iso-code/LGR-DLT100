#About file: mimic_pal_sampler_DLT-100:
This script enables to use the LGR DLT-100 in automatic mode without attached Autosampler
instead you create a connection between your serial to usb adapter and the LGR
Things to do:
- Configure your serial port
- make a bridge between pin 4 and 7 of at the LGR serial plug
- Connect the serial of your computer and the LGR
- start the script, then start a measurement cycle with the LGR

addition in file: mimic_pal_sampler_DLT-100.py
I added the ption to use the RTS and DTS signal to switch some valve.
new features:
automated sampling if solonoid valves are attached to the DTS/RTS pinouts of the serail adapter

A applied example can be found here:
https://doi.org/10.5194/hess-20-715-2016

Cite this code with:

DOI: 10.5281/zenodo.1405290
