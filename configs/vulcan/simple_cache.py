from m5.objects import (
    BadAddr,
    Cache,
    SystemXBar,
)

from gem5.components.boards.abstract_board import AbstractBoard
from gem5.components.boards.x86_board import X86Board
from gem5.components.cachehierarchies.abstract_cache_hierarchy import (
    AbstractCacheHierarchy,
)
from gem5.components.cachehierarchies.classic.abstract_classic_cache_hierarchy import (
    AbstractClassicCacheHierarchy,
)
from gem5.components.memory.single_channel import SingleChannelDDR3_1600
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.isas import ISA
from gem5.resources.resource import BinaryResource
from gem5.simulate.simulator import Simulator
from gem5.utils.override import *
from gem5.utils.requires import requires


class L1Cache(Cache):
    """Simple L1 Cache with default values, direct mapped and no prefetcher"""

    assoc = 1
    tag_latency = 2
    data_latency = 2
    response_latency = 2
    mshrs = 4
    tgts_per_mshr = 20

    def __init__(self):
        super().__init__()
        pass

    def connectBus(self, bus):
        """Connect this cache to a memory-side bus"""
        self.mem_side = bus.cpu_side_ports

    def connectCPU(self, cpu):
        """Connect this cache's port to a CPU-side port
        This must be defined in a subclass"""
        raise NotImplementedError


class L1ICache(L1Cache):
    """Simple L1 instruction cache, direct mappped, no prefetcher"""

    # Set the default size
    size = "16KiB"

    def __init__(self):
        super().__init__()
        pass

    def connectCPU(self, cpu):
        """Connect this cache's port to a CPU icache port"""
        self.cpu_side = cpu.icache_port


class L1DCache(L1Cache):
    """Simple L1 data cache with default values, direct mapped, no prefetcher"""

    # Set the default size
    size = "16KiB"

    def __init__(self):
        super().__init__()
        pass

    def connectCPU(self, cpu):
        """Connect this cache's port to a CPU dcache port"""
        self.cpu_side = cpu.dcache_port


# from cachehierarchies/classic/private_l1_cache_hierarchy.py
class L1CacheHierarchy(AbstractClassicCacheHierarchy):
    def __init__(self):
        super().__init__()
        self.membus = SystemXBar(width=64)
        self.membus.badaddr_responder = BadAddr()
        self.membus.default = self.membus.badaddr_responder.pio

    @overrides(AbstractClassicCacheHierarchy)
    def get_mem_side_port(self):
        return self.membus.mem_side_ports

    @overrides(AbstractClassicCacheHierarchy)
    def get_cpu_side_port(self):
        return self.membus.cpu_side_ports

    @overrides(AbstractCacheHierarchy)
    def incorporate_cache(self, board: AbstractBoard):
        # Set up the system port for functional access from the simulator.
        board.connect_system_port(self.membus.cpu_side_ports)

        for _, port in board.get_mem_ports():
            self.membus.mem_side_ports = port

        assert board.get_processor().get_num_cores() == 1
        self.l1icache = L1ICache()

        self.l1dcache = L1DCache()

        if board.has_coherent_io():
            self._setup_io_cache(board)

        cpu = board.get_processor().get_cores()[0]
        cpu.connect_icache(self.l1icache.cpu_side)
        cpu.connect_dcache(self.l1dcache.cpu_side)

        self.l1icache.mem_side = self.membus.cpu_side_ports
        self.l1dcache.mem_side = self.membus.cpu_side_ports

        if board.get_processor().get_isa() == ISA.X86:
            int_req_port = self.membus.mem_side_ports
            int_resp_port = self.membus.cpu_side_ports
            cpu.connect_interrupt(int_req_port, int_resp_port)
        else:
            cpu.connect_interrupt()


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
