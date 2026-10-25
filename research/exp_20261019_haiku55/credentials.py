"""Read ANTHROPIC_API_KEY from the environment (public release; the original read a local file).
Uses Anthropic's OpenAI-compatible endpoint, because the framework only speaks the OpenAI chat format."""
import os
def configure():
 key=os.environ.get('ANTHROPIC_API_KEY')
 if not key:raise RuntimeError('Set ANTHROPIC_API_KEY')
 base='https://api.anthropic.com/v1/'
 for k in ('ALL_PROXY','all_proxy','HTTP_PROXY','http_proxy','HTTPS_PROXY','https_proxy'):os.environ.pop(k,None)
 os.environ['OPENAI_API_KEY']=key
 return key,base
