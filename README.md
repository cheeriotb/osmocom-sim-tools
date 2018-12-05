# osmocom-sim-tools

This is a fork project of OSMOCOM SIM Tools.
There is nothing special added from the functionality viewpoint, but just an adaptation to Python 3 (3.7.0) was done.
Please check the bottom of this file and refer to the original project to have a good understanding regarding the setup and the usage.

# Usage examples

The command usages in this readme file are kind of examples with the following conditions.

- Terminal Interface
    - Use PC/SC interface between the terminal and the card.

- TELECOM Keys
    - The KIc of the card is 9A665E9CDA096DAE9C04894785EB0B18.
    - The KID of the card is 1A8DD88431450CAF8D3719F6380F0A18.

- Java Card applet and package

    - The file name of the applet is "cardlet.cap".
    - The package AID is A000000476416E64726F6964435453.
    - The module AID is A000000476416E64726F696443545331.
    - The instance AID is A000000476416E64726F696443545331.

## Load

    $ python shadysim.py --pcsc -l ./cardlet.cap --kic 9A665E9CDA096DAE9C04894785EB0B18 --kid 1A8DD88431450CAF8D3719F6380F0A18

## Install

    $ python shadysim.py --pcsc -i ./cardlet.cap --module-aid A000000476416E64726F696443545331 --instance-aid A000000476416E64726F696443545331 --nonvolatile-memory-required 0100 --volatile-memory-for-install 0300 --kic 9A665E9CDA096DAE9C04894785EB0B18 --kid 1A8DD88431450CAF8D3719F6380F0A18

## List

    $ python shadysim.py --pcsc --list-applets --kic 9A665E9CDA096DAE9C04894785EB0B18 --kid 1A8DD88431450CAF8D3719F6380F0A18

## Delete

    $ python shadysim.py --pcsc -d A000000476416E64726F6964435453 --kic 9A665E9CDA096DAE9C04894785EB0B18 --kid 1A8DD88431450CAF8D3719F6380F0A18

# Licence

This software is released under the GNU General Public License v2.0, see LICENSE.

# Author

cheeriotb <cheerio.the.bear@gmail.com>

Please check the original project and its author also.

# Reference

* Original Project
    * OSMOCOM SIM Tools - https://osmocom.org/projects/cellular-infrastructure/wiki/Shadysimpy
