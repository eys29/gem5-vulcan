from gem5.components.processors.linear_generator import LinearGenerator
from gem5.components.boards.test_board import TestBoard
from gem5.components.memory.single_channel import SingleChannelDDR3_1600
from gem5.simulate.simulator import Simulator
from gem5.utils.override import *
from l1cache_hierarchy import L1CacheHierarchy




cache_hierarchy = L1CacheHierarchy()
memory = SingleChannelDDR3_1600(size="2GiB")

# simple processor from here: https://www.gem5.org/documentation/gem5-stdlib/hello-world-tutorial
# processor = SimpleProcessor(cpu_type=CPUTypes.TIMING, num_cores=1, isa=ISA.X86)

# https://www.gem5.org/assets/files/hpca2023-tutorial/gem5-tutorial-hpca-2023.pdf slide 51
generator = LinearGenerator(
        duration="1ms", rate="32GiB/s", max_addr=memory.get_size(), rd_perc=0, data_limit=16384
    )

board = TestBoard(
    clk_freq="3GHz",
    generator=generator,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)


# Setup the Simulator and run the simulation.
print("cacheline size: " + str(board.get_cache_line_size()))

simulator = Simulator(board=board)
simulator.run()
