"""Read the API key for the selected platform from the environment (public release; the original read a local file).
Platform comes from env var LLM_PLATFORM: 'openai' (default, uses OPENAI_API_KEY) or 'openrouter' (uses OPENROUTER_API_KEY)."""
import os
def configure():
 platform=os.environ.get('LLM_PLATFORM','openai')
 if platform=='openai':key=os.environ.get('OPENAI_API_KEY');base='https://api.openai.com/v1'
 else:key=os.environ.get('OPENROUTER_API_KEY');base='https://openrouter.ai/api/v1'
 if not key:raise RuntimeError('API key for '+platform+' not set')
 for k in ('ALL_PROXY','all_proxy','HTTP_PROXY','http_proxy','HTTPS_PROXY','https_proxy'):os.environ.pop(k,None)
 os.environ['OPENAI_API_KEY']=key
 return key,base
