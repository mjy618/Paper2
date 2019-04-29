import numpy

import markov

class model:
    """This class manages the state of the system in response to the device's
    actions, and evaluates the utility function.

    """

    class connection(markov.chain):
        def __init__(self, rates):
            self.rates = rates
            self.cStates = len(self.rates)
            mat = [ [ 1 / self.cStates for dest in range(self.cStates) ]
                    for src in range(self.cStates)]

            super().__init__(mat)

        def statecount(self):
            return self.cStates

        def rateFromIndex(self, index):
            return self.rates[index]

    def __init__(self, cServers, cParts, cBatteryLevels, cHarvestLevels,
                 transmission_rates, max_battery, max_harvest, data_gen_rate,
                 energy_weight, latency_weight, drop_penalty, cycles_per_bit,
                 effective_capacitance, clock_frequency, transmit_power):
        #TODO: WAAY to many parameters here. Can argparse construct an object?
        #Then we could just pass that and save it. It'd make usage a little
        #uglier inside of this class (self.args.LATENCY_WEIGHT instead of
        #self.LATENCY_WEIGHT), but that'd still be an improvement over this,
        #I think.
        self.C_SERVERS = cServers
        self.C_PARTS = cParts
        self.C_BAT = cBatteryLevels
        self.C_HARVEST = cHarvestLevels
        self.MAX_BATTERY = max_battery
        self.MAX_HARVEST = max_harvest
        self.DATA_GEN_RATE = data_gen_rate
        self.ENERGY_WEIGHT = energy_weight
        self.LATENCY_WEIGHT = latency_weight
        self.DROP_PENALTY = drop_penalty
        self.CYCLES_PER_BIT = cycles_per_bit
        self.TRANSMIT_POWER = transmit_power
        self.TRANSMISSION_RATES = transmission_rates
        self.EFFECTIVE_CAPACITANCE = effective_capacitance
        self.CLOCK_FREQ = clock_frequency

        self.reset()

    def getStateMetadata(self):
        return tuple(con.statecount() for con in self.connections) + (self.C_HARVEST, self.C_BAT)

    def getState(self):
        bat = self.battery * self.C_BAT / self.MAX_BATTERY
        bat = round(bat)

        harv = self.harvest_est * self.C_HARVEST / self.MAX_HARVEST
        harv = round(harv)

        return tuple(self.datarates) + (harv,bat)

    def reset(self):
        #TODO?
        self.connections = [ model.connection(rates) for rates in self.TRANSMISSION_RATES ]
        self.battery = 0

        self.computation_prestep()
        return self.getState()


    def computation_prestep(self):
        self.datarates = [ con.step() for con in self.connections ]

        self.harvest = 0 #TODO
        self.harvest_est = 0 #TODO

    def computation_step(self, selection, nOffload):
        assert(0 <= self.battery and self.battery <= self.MAX_BATTERY)

        #x^{(k)}*C^{(k)}
        cOffloadBits = (nOffload/self.C_PARTS)*self.DATA_GEN_RATE

        #(1-x^{(k)}) * C^{(k)}
        cLocalBits = self.DATA_GEN_RATE - cOffloadBits

        #(1-x^{(k)}) * C^{(k)} * N
        cLocalCycles = cLocalBits * self.CYCLES_PER_BIT

        #B_i^{(k)}
        linkRate = self.datarates[selection]



        #(1): TODO ASSUMING CONSTANT FREQ
        latencyLocal = cLocalCycles / self.CLOCK_FREQ

        #(3)
        latencyOffload = cOffloadBits / linkRate

        #(N/A): pg. 1934, left column, near middle at the end of a paragraph
        latency = max(latencyLocal, latencyOffload)


        #(2), but with fixed clock frequency
        energyLocal = cLocalCycles * self.EFFECTIVE_CAPACITANCE * \
            (self.CLOCK_FREQ**2)

        #(4)
        energyOffload = latencyOffload * self.TRANSMIT_POWER

        #(N/A): pg. 1933, directly above (5)
        energyConsumption = energyLocal + energyOffload

        # (8)
        utility  = 0
        utility += cOffloadBits
        utility -= self.DROP_PENALTY * (self.battery == 0)
        utility -= self.ENERGY_WEIGHT * energyConsumption
        utility -= self.LATENCY_WEIGHT * latency

        #TODO update battery x2

        return (utility,)

    def step(self, selection, nOffload):
        """Simulates a single timestep. The device elects to offload `nOffload`
        of the `C_PARTS` parts to the server indicated by the index `selection`.

        """
        assert(type(nOffload) == int)
        assert(0 <= nOffload and nOffload <= self.C_PARTS) #equality on both

        assert(type(selection) == int)
        assert(0 <= selection and selection < self.C_SERVERS)

        (reward,) = self.computation_step(selection, nOffload)

        # "pre"-step computations are done after computing the reward because
        # it's actually setting up the state for the NEXT step.
        self.computation_prestep()
        state = self.getState()

        raise Exception("Not Implemented")

        done = False
        return (state, reward, done)

    def closeEpisode(self):
        """Returns a list. That contains, for each time step, the tuple (energy
        consumption, computational latency, whether or not the task dropped,
        utility)

        """
        raise Exception("Not Implemented")
