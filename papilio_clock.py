#!/usr/bin/python

### Papilio Plus clock helper
### given a desired frequency - find the best multipliers to get what you need.

### The incoming clock to a DCM can be manipulated in a numbe of ways to get a given frequency.
### So finding a good set of values to get close to a required frequency would be useful.


### Author: M. Schafer Dec 2012
### Derived from http://www.xilinx.com/support/documentation/user_guides/ug382.pdf


CLOCKIN = 320 # MHz. The clock frequency supplied to the FPGA
# possibly turn these into dictioanry so coudl have diff devices.
# is papilio plus, duo different ?
DCM_CLOCKDIV_RATIOS = [1.5,2,2.5,3,3.5,4,4.5,5,5.5,6,6.5,7,7.5,8,9,10,11,12,13,14,15,16]
DCM_SYNTH_DIVIDE_MAX = 32

### UI compnent
from Tkinter import *
import sys
        
class App: # Build a simple UI
    def __init__(self, master):
        # setup entry field, calculate button and report.
        master.title("Papilio Clock helper")
        frame = Frame(master)
        frame.pack()
        self.reportvar = StringVar()
        self.reportvar.set("Choose a frequency\n\n")
 
        self.desired = Entry(frame, text="Desired frequency", width=20)
        self.desired.pack(side=LEFT)

        self.calc = Button(frame, text="Calculate", command=self.calculate)
        self.calc.pack(side=LEFT)
        #self.calc.bind("<Return>", self.calculate)
        self.report = Label(master, width=120, justify=LEFT,
                            textvariable=self.reportvar)
        self.report.pack(side=BOTTOM)

    def calculate(self):
        """ extract user input,
            display freq above and below desired one
        """
        success = False
        try:
            desired = float(self.desired.get())
            success = True
        except:
            self.reportvar.set("Must be a number.\n")
        if success:
            result = find_best_multipliers(desired, CLOCKIN)
            #sort results by r[1] and display as label
            label = "Desired Frequency = %s\n\n" % desired
            label += collate_output(desired, result)
            self.reportvar.set(label)
            print label # if you want to cut and paste
        

def DCM_clkdiv(clkin, suffix=""):
    """ Calc all frequencies if using CLKDV output """
    clocks = []
    for i in DCM_CLOCKDIV_RATIOS:
        freq = clkin/float(i)
        #clocks.append([freq, "CLKDV", "For %s MHz: CLKDV_DIV = %s%s" % (freq, i, suffix)])
        clocks.append([freq, "CLKDV", "CLKDV_DIV = %s%s" % (i, suffix)])
    return clocks
        
###
def calc_possible_clocks(clkin=CLOCKIN):
    """ Make a single list of all possible clock frequencies """
    clocks = []
    # DCM 2X
    clocks.append([clkin*2, "CLK2X,CLK2X180", "For %s MHz" % (clkin*2)])
    # DCM fractional CLKDV
    clocks.extend(DCM_clkdiv(clkin))
    clocks.extend(DCM_clkdiv(clkin/2, " (+CLKIN_DIV_BY_2)"))
    # DCM Synthesis
    for i in range(2,32):
        f1 = (clkin) * i
        for j in range (1,32):
            f2 = f1 / float(j)
            #msg = "For %s MHz: CLKFX_MUL/CLKFX_DIV = %s / %s" % (f2, i, j)
            msg = "CLKFX_MUL/CLKFX_DIV = %s / %s" % (i, j)
            if f2 > 350: msg += " . Unlikely (>350MHz internal speedgrade-3)"
            elif f2 > 250: msg += " . Unlikely (>250MHz internal speedgrade-2)"
            elif f2 > 200: msg += " . Possible (>200MHz internal speedgrade-2)"
            clocks.append([f2, 'CLKFX, CLKFX180', msg])
    return clocks

def find_best_multipliers(desired_freq, clkin=CLOCKIN):
    """ move through the list until find first value > desired_freq
        - Collect sequences along the way (Could be many multiplier ratios for a given frequency)
        - Collect the multipler(s) for the next highest frequency
    """
    clocks = calc_possible_clocks(clkin)
    print "%s clocks evaluated" % (len(clocks))
    #print clocks
    clocks.sort()
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
    result = low
    if high[0][0] != low[0][0]: # cleanup if first clock
        result.extend(high)
    return result
        
def collate_output(desired, result):
    message = ""
    for r in result:
        error = abs(r[0]-desired)
        message += "\nFor %s MHz. Error = %f   mult1/mult2 = %s / %s." % (r[0], error, r[1], r[2])
    return message


### Coment out the UI section if you want this simpler...
if __name__ == '__main__':
    # check argv to see if being called by command line - in which case demand two args and ignore UI
    print sys.argv, len(sys.argv)
    if len(sys.argv) == 2:
        # print usage
        print "Usage: papillio_clock clock_freq desired_freq"
    if len(sys.argv) == 3:
        # called from command line - ignore UI
        CLOCKIN = float(sys.argv[1])
        desired = float(sys.argv[2])
        print "Desired Frequency = %s" % desired
        result = find_best_multipliers(desired)
        print collate_output(desired, result)
    else:
        # UI based version
        root = Tk()
        app = App(root)
        root.mainloop()
    
