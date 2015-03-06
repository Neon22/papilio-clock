#!/usr/bin/python

### Papilio Plus clock helper
### given a desired frequency - find the best multipliers to get what you need.

### The incoming clock to a DCM can be manipulated in a numbe of ways to get a given frequency.
### So finding a good set of values to get close to a required frequency would be useful.


### Author: M. Schafer Dec 2012
### Jul 2014 - cascading DCMs
### Derived from http://www.xilinx.com/support/documentation/user_guides/ug382.pdf


CLOCKIN = 32 # MHz. The clock frequency supplied to the FPGA

# possibly turn these into a dictionary so can support different devices.
# is papilio plus, duo different ?
DCM_CLOCKDIV_RATIOS = [1.5,2,2.5,3,3.5,4,4.5,5,5.5,6,6.5,7,7.5,8,9,10,11,12,13,14,15,16]
DCM_CLKFX_MUL = 32
DCM_CLKFX_DIV = 32

### GUI component
from Tkinter import *
import sys
from operator import itemgetter # used in sort


class App: # Build a simple UI
    def __init__(self, master):
        # setup entry field, calculate button and report.
        master.title("Papilio Clock helper")
        # Top frame
        topframe = Frame(master)
        topframe.pack()
        label  = "The Spartan6 FPGA has clock modules composed of two DCM units and a PLL."
        #label += "\nThe DCM units can be chained together."
        label += "\nThis helper calculates the ways a desired clock can be generated using one or both DCMs."
        label += "\nIt shows the exact clock if possible. Or the clocks below and above if not."
        label += "\n(If window overflows - consult console for full list)"
        Ltop = Label(topframe, text=label)
        Ltop.pack(side=LEFT)
        inputframe = Frame(master)
        inputframe.pack()
        # Input frame
        L1 = Label(inputframe, text="Source Clock")
        L1.pack(side=LEFT)
        self.clkin = Entry(inputframe, width=20)
        self.clkin.insert(0, CLOCKIN)
        self.clkin.pack(side=LEFT)
        L2 = Label(inputframe, text="Desired frequency")
        L2.pack(side=LEFT)
        self.desired = Entry(inputframe, width=20)
        self.desired.pack(side=LEFT)
        # Button frame
        buttonframe = Frame(master)
        buttonframe.pack()
        self.calc = Button(buttonframe, text="Calculate", command=self.calculate)
        self.calc.pack(side=LEFT)
        self.desired.bind("<Return>", self.calculate)
        #
        self.reportvar = StringVar()
        self.reportvar.set("Choose a desired frequency\n\n")
        self.report = Label(master, width=130, justify=LEFT,
                            textvariable=self.reportvar)
        self.report.pack(side=BOTTOM)
        #
        self.desired.focus_set()
        #
        self.clocks = []
        self.lastclk = 0

    def calculate(self, *args):
        """ extract user input,
            display freq above and below desired one
        """
        # *args ignored - so we can have <return> operate on desired freq slot
        success = False
        try:
            desired = float(self.desired.get())
            clkin = float(self.clkin.get())
            success = True
        except:
            self.label_freq.set("Must be a number.\n")
        if success:
            if len(self.clocks) == 0 or self.lastclk != clkin:
                # make/remake if input values change
                self.clocks, self.singlepass = calc_possible_twolayer_clocks(clkin)
                self.singlepass.sort()
                self.clocks.sort()
                self.lastclk = clkin
            result = find_best_multipliers(desired, self.clocks)
            #sort results by r[1] and display as label
            label = "Desired Frequency = %s\n" % desired
            label += collate_output(desired, result, self.singlepass, clkin)
            self.reportvar.set(label)
            print label # if you want to cut and paste
        

def DCM_clkdiv(clkin, suffix=""):
    """ Calc all frequencies if using CLKDV output """
    clocks = []
    for i in DCM_CLOCKDIV_RATIOS:
        freq = clkin/float(i)
        #clocks.append([freq, "CLKDV", "For %s MHz: CLKDV_DIV = %s%s" % (freq, i, suffix), clkin])
        clocks.append([freq, "CLKDV", "Set CLKDV_DIV = %s%s" % (i, suffix), clkin])
    return clocks
        

def calc_possible_clocks(clkin=CLOCKIN):
    """ Make a single list of all possible clock frequencies
        - return list of: [freq, using_signals, how, source_clk]
    """
    clocks = []
    # DCM 2X
    #clocks.append([clkin*2, "CLK2X,CLK2X180", "For %s MHz" % (clkin*2), clkin])
    clocks.append([clkin*2, "CLK2X,CLK2X180", "Set ", clkin])
    # DCM fractional CLKDV
    clocks.extend(DCM_clkdiv(clkin))
    clocks.extend(DCM_clkdiv(clkin/2, " (+CLKIN_DIV_BY_2)"))
    # DCM Synthesis
    for i in range(2,DCM_CLKFX_MUL):
        f1 = (clkin) * i
        for j in range (1,DCM_CLKFX_DIV):
            if i != j: # ignore equiv of *1
                f2 = f1 / float(j)
                #msg = "For %s MHz: CLKFX_MUL/CLKFX_DIV = %s / %s" % (f2, i, j)
                msg = "Set CLKFX_MUL/CLKFX_DIV = %s / %s" % (i, j)
                if f2 > 350:   msg += " -Unlikely. (>350MHz. Needs chip speedgrade-3)"
                elif f2 > 250: msg += " -Unlikely. (>250MHz. Needs chip speedgrade-2)"
                elif f2 > 200: msg += " -Possible. (>200MHz. Needs chip speedgrade-2)"
                clocks.append([f2, 'CLKFX, CLKFX180', msg, clkin])
    return clocks


def calc_possible_twolayer_clocks(clkin=CLOCKIN):
    " cascade two DCM units to find all poss frequencies "
    clocks = []
    singlepass_clocks = calc_possible_clocks(clkin)
    clocks.extend(singlepass_clocks)
    for c in singlepass_clocks:
        pass2 = calc_possible_clocks(c[0])
        clocks.extend(pass2)
    return clocks, singlepass_clocks


def find_base_frequency(desired_freq, freqs, base_clk):
    """ look for desired_freq made from base clock
        - freqs is a sorted list
        return list of entires of desired_freq
    """
    found = False
    temp = []
    for i in range(len(freqs)):
        freq = freqs[i]
        if freq[0] == desired_freq and freq[-1] == base_clk:
            temp.append(freq)
            found = True
        elif found:
            # we found and now we're not finding anymore - we're done.
            break
    # Remove duplicates
    result = []
    for i in temp:
        if i not in result:
          result.append(i)
    result.sort(key=itemgetter(1))
    return result


def find_best_multipliers(desired_freq, clocks):
    """ move through the list until find first value > desired_freq
        - Collect sequences along the way (Could be many multiplier ratios for a given frequency)
        - Collect the multipler(s) for the next highest frequency
    """
    # initial values
    clk = [1,0,0]
    low = [clocks[0]]
    high = [clocks[-1]]
    # begin searching for desired_freq
    for i in range(len(clocks)):
        diff = clocks[i][0] - clk[0] # is this a multiple
        clk = clocks[i]
        if clocks[i][0] < desired_freq:
            if diff == 0: #multiple at this frequency
                low.append(clocks[i])
            else: # only one so start a new list
                low = [clocks[i]]
        else: # we are at, or near, the desired_freq.
            # next will be one or more matches equal or above
            high = [clocks[i]]
            diff = high[0][0] - desired_freq
            j = i+1
            while j < len(clocks) and clocks[j][0] <= desired_freq+diff:
                    high.append(clocks[j])
                    j += 1
            break
    # gather nicely
    # forget low if high error == 0. I.e. exact match to desired
    if high[0][0] - desired_freq ==0:
        temp = high
    else:
        # no exact match - show low and high
        temp = low
        if high[0][0] != low[0][0]: # cleanup if first clock
            temp.extend(high)
    #remove duplicates
    result = []
    for i in temp:
        if i not in result:
          result.append(i)
    #result.sort(key=itemgetter(1,-1))#, reverse=True)
    result.sort(key=itemgetter(1))
    return result


def collate_output(desired, result, clocks, base_clk):
    " Present the result list usefully "
    message = ""
    for r in result:
        error = abs(r[0]-desired)
        if error == 0: error = "Exact."
        elif error*10 == int(error*10): error = "Error = %2.1f" % error
        else: error = "Error = %f" % error
        if CLOCKIN == r[-1]:
            message += "\nFor %s MHz. %s  Use: %s. %s." % (r[0], error, r[1], r[2])
        else:
            message += "\nFor %s MHz. %s  Use: %s. %s from %f MHz." % (r[0], error, r[1], r[2], r[-1])
            sources = find_base_frequency(r[-1], clocks, base_clk)
            for s in sources:
                message += "\n    - For %f MHz. Use: %s. %s." % (s[0], s[1], s[2])
    return message


###
if __name__ == '__main__':
    # check argv to see if being called by command line - in which case demand two args and ignore UI
    print sys.argv, len(sys.argv)
    if len(sys.argv) == 2:
        # print usage
        print "Usage: papilio_clock clock_freq desired_freq"
    if len(sys.argv) == 3:
        # called from command line - ignore UI
        clkin = float(sys.argv[1])
        desired = float(sys.argv[2])
        print "Desired Frequency = %s" % desired
        #
        clocks, singlepass = calc_possible_twolayer_clocks(clkin)
        print "%s clocks evaluated" % (len(clocks))
        #print clocks[0]
        # many dups in clocks but too big to sort now - sort later.
        singlepass.sort()
        clocks.sort()
        result = find_best_multipliers(desired, clocks)
        print collate_output(desired, result, singlepass, clkin)
    else:
        # GUI based version
        root = Tk()
        app = App(root)
        root.mainloop()
    
# Bug:
#   For 4.26666666667 MHz. Error = 0.000007  Use: CLKDV. Set CLKDV_DIV = 7.5.
#   For 4.26666666667 MHz. Error = 0.000007  Use: CLKDV. Set CLKDV_DIV = 7.5 (+CLKIN_DIV_BY_2).
# Todo:
# IWBNI we could check for several frequencies and refine the choices to the minimum.
#  - run coltae_output analog just to gather and prune.
#  - once for each desired freq
#  - correlate and minimise number of DCM units.
