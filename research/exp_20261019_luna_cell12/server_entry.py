"""MCP entry wrapper: reset exogenous RNG per environment, no source edits.

The framework seeds once at module import. Repeated simulations in one MCP
process otherwise consume different stochastic occupancy/EV histories. The
same seed must be re-applied for every alternative in a comparison.
"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from bestopt.env.core.environment import BESTOptEnvironment,set_seed
original=BESTOptEnvironment.__init__
def deterministic(self,*args,**kwargs):
 set_seed(142857)
 return original(self,*args,**kwargs)
BESTOptEnvironment.__init__=deterministic
server=ROOT/'src'/'mcp_center'/'mcp_server.py'
source=server.read_text()
# An audit snapshot must not add a selectable stale configuration to the
# application. Keep the original config_save behavior for all real calls.
needle='if name != state.active_config and name not in state.config_managers:'
assert source.count(needle)==1
source=source.replace(needle,'if name != "__audit__" and name != state.active_config and name not in state.config_managers:')
exec(compile(source,str(server),'exec'),{'__name__':'__main__','__file__':str(server),'__package__':None})
