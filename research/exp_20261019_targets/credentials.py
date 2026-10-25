"""Read the DeepSeek API key from the environment (public release; the original read a local file)."""
import os
def configure():
 key=os.environ.get('DEEPSEEK_API_KEY')
 if not key:raise RuntimeError('Set DEEPSEEK_API_KEY')
 base='https://api.deepseek.com/v1'
 for k in ('ALL_PROXY','all_proxy','HTTP_PROXY','http_proxy','HTTPS_PROXY','https_proxy'):os.environ.pop(k,None)
 os.environ['OPENAI_API_KEY']=key;os.environ['OPENAI_BASE_URL']=base
 return key,base
