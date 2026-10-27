"""Replay the overloaded __post_init__ finding and controls entirely offline.

From the repository root:
    PYTHONPATH=. /path/to/python findings/2026-10-25/overloaded_post_init/verify.py --out runs/postinit
"""
import argparse
import json,subprocess,tempfile,sys
from pathlib import Path
from typediff.runners import Runners,ToolConfig
from typediff.models import Tool
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args()
src=Path(__file__).with_name('repro.py').read_text()
first='    @overload\n    def __post_init__(self, value: int) -> None: ...\n'
second='    @overload\n    def __post_init__(self, value: str) -> None: ...\n'
cases={
 'extra_arity':src.replace('def __post_init__(self, value: str) -> None: ...', 'def __post_init__(self, value: int, extra: str) -> None: ...').replace('def __post_init__(self, value: int | str) -> None:', 'def __post_init__(self, value: int, extra: str = "") -> None:'),
 'original':src,
 'reverse_overload_order':src.replace(first+second,second+first),
 'union_only':src.replace(first+second,''),
 'integer_only':src.replace(first+second,'').replace('int | str','int'),
 'manual_string_call':src+'Record(1).__post_init__("manual")\n',
 'ordinary_override':'''from typing import overload
class Base:
    def hook(self, value: int) -> None:
        print(value)
class Record(Base):
    @overload
    def hook(self, value: int) -> None: ...
    @overload
    def hook(self, value: str) -> None: ...
    def hook(self, value: int | str) -> None:
        print(value)
Record().hook(1)
''',
 'bound_callable_assignment':src.replace('from typing import overload','from typing import overload\nfrom collections.abc import Callable')+'callback: Callable[[int], None] = Record(1).__post_init__\ncallback(1)\n',
 'keyword_only_constructor':src.replace('@dataclass\n','@dataclass(kw_only=True)\n').replace('Record(1)','Record(value=1)'),
 'defaulted_initvar':src.replace('value: InitVar[int]','value: InitVar[int] = 1').replace('Record(1)','Record()'),
 'bad_hook_no_integer_overload':src.replace('def __post_init__(self, value: int) -> None: ...','def __post_init__(self, value: bytes) -> None: ...').replace('value: int | str','value: bytes | str').replace('        print(value)','        print(value.upper())'),
 'bad_constructor_argument':src.replace('Record(1)','Record("bad")'),
}
r=Runners(ToolConfig(python_version='3.13',timeout_s=20));root=args.out;root.mkdir(parents=True,exist_ok=True);results=[]
for name,source in cases.items():
 (root/f'{name}.py').write_text(source)
 row={'name':name,'source':source,'tools':{}}
 for t in (Tool.MYPY,Tool.TY,Tool.PYRIGHT):
  res=r.check(t,source)
  row['tools'][t.value]={'exit_code':res.run.exit_code,'flags':res.run.flags,'stdout':res.run.stdout,'stderr':res.run.stderr,'crashes':[c.signature for c in res.crashes]}
 res=r.check(Tool.MYPY,source,['--strict']);row['mypy_strict']={'exit_code':res.run.exit_code,'stdout':res.run.stdout,'stderr':res.run.stderr}
 with tempfile.TemporaryDirectory() as wd:
  p=Path(wd)/'case.py';p.write_text(source)
  rt=subprocess.run([sys.executable,str(p)],cwd=wd,capture_output=True,text=True,timeout=10)
 row['runtime']={'exit_code':rt.returncode,'stdout':rt.stdout,'stderr':rt.stderr}
 results.append(row);print(name,{t:v['exit_code'] for t,v in row['tools'].items()},'runtime',rt.returncode,flush=True)
(root/'results.json').write_text(json.dumps({'versions':{t:r.version(t) for t in ('mypy','ty','pyright','runtime')},'cases':results},indent=2))
