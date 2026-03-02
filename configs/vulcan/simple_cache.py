from gem5.components.boards.x86_board import X86Board
from gem5.components.memory.single_channel import SingleChannelDDR3_1600
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.isas import ISA
from gem5.resources.resource import BinaryResource
from gem5.simulate.simulator import Simulator
from gem5.utils.override import *
from gem5.utils.requires import requires
from l1cache_hierarchy import L1CacheHierarchy

# following tutorial: https://www.gem5.org/documentation/gem5-stdlib/x86-full-system-tutorial
requires(isa_required=ISA.X86)

cache_hierarchy = L1CacheHierarchy()
memory = SingleChannelDDR3_1600(size="2GiB")

# simple processor from here: https://www.gem5.org/documentation/gem5-stdlib/hello-world-tutorial
processor = SimpleProcessor(cpu_type=CPUTypes.TIMING, num_cores=1, isa=ISA.X86)

board = X86Board(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

# Set the workload.
# binary = obtain_resource("x86-hello64-static")
binary = BinaryResource(local_path="configs/vulcan/prime_cache")
board.set_se_binary_workload(binary)

# Setup the Simulator and run the simulation.
print("cacheline size: " + str(board.get_cache_line_size()))

simulator = Simulator(board=board)
simulator.run()
