"""
Module to work with Angstrom WS7 wavelength meter

The MIT License (MIT)

Copyright (c) 2015 Stepan Snigirev

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

import argparse
import ctypes, os, sys, random, time

class WavelengthMeter:

    def __init__(self, dllpath="C:\Windows\System32\wlmData.dll", debug=False):
        """
        Wavelength meter class.
        Argument: Optional path to the dll. Default: "C:\Windows\System32\wlmData.dll"
        """
        self.channels = []
        self.dllpath = dllpath
        self.debug = debug
        if not debug:
            self.dll = ctypes.WinDLL(dllpath)
            self.dll.GetWavelengthNum.restype = ctypes.c_double
            self.dll.GetFrequencyNum.restype = ctypes.c_double
            self.dll.GetSwitcherMode.restype = ctypes.c_long

    def GetExposureMode(self):
        if not self.debug:
            return (self.dll.GetExposureMode(ctypes.c_bool(0))==1)
        else:
            return True

    def SetExposureMode(self, b):
        if not self.debug:
            return self.dll.SetExposureMode(ctypes.c_bool(b))
        else:
            return 0

    def GetWavelength(self, channel=1):
        if not self.debug:
            return self.dll.GetWavelengthNum(ctypes.c_long(channel), ctypes.c_double(0))
        else:
            wavelengths = [460.8618, 689.2643, 679.2888, 707.2016, 460.8618*2, 0, 0, 0]
            if channel>9:
                return 0
            return wavelengths[channel-1] + channel * random.uniform(0,0.0001)

    def GetFrequency(self, channel=1):
        if not self.debug:
            return self.dll.GetFrequencyNum(ctypes.c_long(channel), ctypes.c_double(0))
        else:
            return 38434900

    def GetAll(self):
        return {
            "debug": self.debug,
            "wavelength": self.GetWavelength(),
            "frequency": self.GetFrequency(),
            "exposureMode": self.GetExposureMode()
        }

    @property
    def wavelengths(self):
        return [self.GetWavelength(i+1) for i in range(8)]
    
    @property
    def frequencies(self):
        return [self.GetFrequency(i+1) for i in range(8)]

    @property
    def wavelength(self):
        return self.GetWavelength(1)

    @property
    def switcher_mode(self):
        if not self.debug:
        	return self.dll.GetSwitcherMode(ctypes.c_long(0))
        else:
            return 0

    @switcher_mode.setter
    def switcher_mode(self, mode):
        if not self.debug:
        	self.dll.SetSwitcherMode(ctypes.c_long(int(mode)))
        else:
            pass

if __name__ == '__main__':

    # command line arguments parsing
    parser = argparse.ArgumentParser(description='Reads out wavelength values from the High Finesse Angstrom WS7 wavemeter.')
    parser.add_argument('--debug', dest='debug', action='store_const',
                        const=True, default=False,
                        help='runs the script in debug mode simulating wavelength values')
    parser.add_argument('channels', metavar='ch', type=int, nargs='*',
                        help='channel to get the wavelength, by default all channels from 1 to 8',
                        default=range(1,8))

    args = parser.parse_args()

    wlm = WavelengthMeter(debug=args.debug)

    for i in args.channels:
        print("Frequency at channel %d:\t%.6f THz" % (i, wlm.frequencies[i]))

    print(wlm.frequencies[1:6:2])
    # old_mode = wlm.switcher_mode

    # wlm.switcher_mode = True

    # print(wlm.wavelengths)
    # time.sleep(0.1)
    # print(wlm.wavelengths)

    # wlm.switcher_mode = old_mode

