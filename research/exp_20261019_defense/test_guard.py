"""Manual check of the D1 guard through the real server entry (run from OptAgent root with the project venv)."""
import asyncio,json,sys,os,shutil,tempfile
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
tmp=Path(tempfile.mkdtemp());(tmp/'bestopt_workspace'/'configs').mkdir(parents=True)
shutil.copy(ROOT/'bestopt_workspace'/'configs'/'default.json',tmp/'bestopt_workspace'/'configs'/'default.json');(tmp/'guard_d1.json').write_text('{}')
os.chdir(tmp)
async def main():
    async with stdio_client(StdioServerParameters(command=sys.executable,args=[str(HERE/'server_entry.py')])) as (r,w):
        async with ClientSession(r,w) as s:
            await s.initialize()
            async def call(t,a):
                x=await s.call_tool(t,a);return json.loads(x.content[0].text)
            cases=[('controller_update',{'controller_id':'hvac_controller_1','updates':{'base_cooling':28}}),
                   ('controller_update',{'updates':{'base_cooling':'28.0'}}),
                   ('controller_update',{'controller_id':'hvac_controller_1','updates':{'base_cooling':26}}),
                   ('controller_update',{'controller_id':'hvac_controller_1','updates':{'precooling':{'degree':2,'hours':2}}}),
                   ('controller_add_hvac',{'controller_id':'x','system_id':'hvac_system_1','parameters':{'base_cooling':30}})]
            for t,a in cases:
                out=await call(t,a);print(t,json.dumps(a),'->',out.get('success'),out.get('error',''))
            await call('config_save',{'name':'t'});cfg=json.load(open('bestopt_workspace/configs/t.json'))
            print('saved base_cooling after the sequence (26 expected, rejected 28/30 not written):',cfg['controllers']['hvac_controller_1']['parameters']['base_cooling'],'x' in cfg['controllers'])
            cfg['controllers']['hvac_controller_1']['parameters']['base_cooling']=29;json.dump(cfg,open('bad.json','w'))
            out=await call('config_create',{'name':'bad','from_file':'bad.json'});print('config_create from file with 29 ->',out.get('success'),out.get('error',''))
asyncio.run(main())
