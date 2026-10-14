"""Inspect compaction records in a DSH session log."""
import sys, json
import zstandard as zstd

path = sys.argv[1]
mode = sys.argv[2] if len(sys.argv) > 2 else 'compaction'
dctx = zstd.ZstdDecompressor()
with open(path, 'rb') as fh:
    data = dctx.stream_reader(fh).read()
lines = [l for l in data.decode('utf-8', 'replace').split('\n') if l.strip()]
objs = [json.loads(l) for l in lines]

def brief(v, n=400):
    s = json.dumps(v, ensure_ascii=False)
    return s if len(s) <= n else s[:n] + f'...<{len(s)} chars>'

if mode == 'compaction':
    for i, o in enumerate(objs):
        t = o.get('type', '')
        if t.startswith('compaction/'):
            print(f"--- line {i} seq={o.get('seq')} {t}")
            for k, v in o.items():
                if k in ('type', 'seq'):
                    continue
                print(f"    {k} = {brief(v, 300)}")
elif mode == 'tail':
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    for i, o in enumerate(objs[-n:], start=len(objs) - n):
        t = o.get('type', '')
        if t in ('tool/result',):
            print(f"[{i}] seq={o.get('seq')} {t} keys={sorted(o.keys())}")
            continue
        print(f"[{i}] seq={o.get('seq')} {t} :: {brief({k: v for k, v in o.items() if k not in ('type','seq')}, 500)}")
elif mode == 'range':
    a, b = int(sys.argv[3]), int(sys.argv[4])
    for i in range(a, min(b, len(objs))):
        o = objs[i]
        t = o.get('type', '')
        print(f"[{i}] seq={o.get('seq')} {t} :: {brief({k: v for k, v in o.items() if k not in ('type','seq')}, 600)}")
