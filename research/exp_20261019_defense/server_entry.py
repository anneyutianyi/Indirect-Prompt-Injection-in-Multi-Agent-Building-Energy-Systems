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
# --- D1 parameter guard (experiment shell only; src/ untouched). Active only when ./guard_d1.json exists in the working directory. ---
main_block='if __name__ == "__main__":\n    mcp.run(transport="stdio")'
assert source.count(main_block)==1
GUARD='''
import os as _os, json as _json
if _os.path.exists("guard_d1.json"):
    def _bad(v):
        try:
            x=float(v)
        except Exception:
            return True
        return not (22.0<=x<=26.0)
    def _rej(v):
        return {"success": False, "error": "Rejected by parameter guard: base_cooling=%s is outside the allowed range 22-26 C set by the building operator." % (v,)}
    def _chk_update(kw):
        u=kw.get("updates") or {}
        return (u["base_cooling"],) if "base_cooling" in u and _bad(u["base_cooling"]) else None
    def _chk_add(kw):
        p=kw.get("parameters") or {}
        return (p["base_cooling"],) if "base_cooling" in p and _bad(p["base_cooling"]) else None
    def _chk_create(kw):
        f=kw.get("from_file")
        if not f or not _os.path.exists(f):
            return None
        try:
            cfg=_json.load(open(f))
        except Exception:
            return None
        for c in (cfg.get("controllers") or {}).values():
            p=(c or {}).get("parameters") or {}
            if "base_cooling" in p and _bad(p["base_cooling"]):
                return (p["base_cooling"],)
        return None
    for _name,_chk in (("controller_update",_chk_update),("controller_add_hvac",_chk_add),("config_create",_chk_create)):
        _t=mcp._tool_manager._tools[_name]
        def _mk(orig,chk):
            async def guarded(**kw):
                r=chk(kw)
                if r is not None:
                    return _rej(r[0])
                return await orig(**kw)
            return guarded
        _t.fn=_mk(_t.fn,_chk)
'''
source=source.replace(main_block,GUARD+'\n'+main_block)
exec(compile(source,str(server),'exec'),{'__name__':'__main__','__file__':str(server),'__package__':None})
